"""Pyomo MILP builder for v2.6 Cases 1-2 (cascaded HP extraction, no ORC).

Each case is built by selectively enabling equipment blocks via the
``cfg.case.equipment`` flags. Energy balances and the TAC objective are
shared so cross-case comparisons stay on the same accounting basis.

v2.6 heat routing (cascaded, NOT parallel):

    Main steam → HP turbine → mid-pressure extraction tap
                              ├─ part diverted to double-effect absorption
                              └─ part continues to LP turbine + condenser

    P_turb_gross_full(t) = rated_efficiency * P_rx(t)            # zero-extraction baseline
    P_turb_gross(t)      = P_turb_gross_full(t)
                           - willans_slope * Q_to_abs(t)         # Willans penalty
    P_turb_net(t)        = (1 - aux_fraction) * P_turb_gross(t)
    Q_abs_cool(t)        = COP_abs(T_wb(t)) * available(t) * Q_to_abs(t)

Versus v2.5: the parallel topology ``eta × (P_rx − Q_to_orc − Q_to_abs)``
is gone. Diverted steam at the HP-LP tap costs ~0.083 MWe per MWth (Plan
§A7 + §F.1), an order of magnitude less than charging the full turbine
efficiency against extracted heat. The ORC bottoming cycle is removed
entirely.
"""

from __future__ import annotations

from typing import Optional

import pyomo.environ as pyo

from src.config import RunConfig
from src.data import TimeSeries
from src.finance import annualized_capex, section_45u_credit_usd_per_mwh
from src.performance import vcc_pwl_points

_MMBTU_PER_MWh: float = 3.412


def _absorption_cop(
    T_wb_C: float,
    cop_houston_baseline: float,
    derate_per_celsius: float,
    cop_nameplate_cap: float,
    baseline_T_wb_C: float = 26.0,
) -> float:
    """v2.6 time-varying COP for the double-effect absorption chiller.

    Linear de-rating around the Houston-baseline anchor and capped at
    nameplate (so cool wet-bulb hours don't extrapolate above 1.30):

        cop_lin = cop_houston_baseline − derate × (T_wb − 26 °C)
        COP     = max(min(cop_lin, cop_nameplate_cap), 0.5)

    The 0.5 floor exists only as numerical insurance — Houston wet bulbs
    never get hot enough in the NSRDB record to drag a real chiller that
    low; the crystallization gate kicks in well before that.
    """
    cop_lin = cop_houston_baseline - derate_per_celsius * (T_wb_C - baseline_T_wb_C)
    return max(min(cop_lin, cop_nameplate_cap), 0.5)


def _absorption_available(
    T_wb_C: float,
    cooling_water_approach_K: float,
    crystallization_cw_inlet_C: float,
) -> bool:
    """P1-A crystallization gate.

    If cooling-water inlet exceeds the LiBr crystallization threshold the
    absorption unit must shut down and the VCC backup picks up the load.
    """
    cw_inlet = T_wb_C + cooling_water_approach_K
    return cw_inlet <= crystallization_cw_inlet_C


def build_model(
    cfg: RunConfig, ts: TimeSeries, pue: Optional[float] = None
) -> pyo.ConcreteModel:
    """Construct the Pyomo model for a nuclear case (Cases 1 or 2, v2.6).

    Returns:
        Concrete model ready for `pyo.SolverFactory(...).solve(model)`. The
        model carries scalar Expressions ``capex_annual``, ``fom_annual``,
        ``vom_annual``, ``fuel_annual``, ``grid_annual`` for post-processing.
    """
    if cfg.case.case_id not in (1, 2):
        raise ValueError(
            f"build_model handles v2.6 Cases 1-2 only; got case_id={cfg.case.case_id}"
        )

    eq = cfg.case.equipment
    cap = cfg.case.capacities
    pue_used = float(pue if pue is not None else cfg.base.physics.pue_default)
    eta_chain = cfg.base.physics.cooling_chain_efficiency
    dt = cfg.base.time.delta_t
    wacc = cfg.financial.WACC_nominal
    annual_scale = 8760.0 / ts.num_hours

    m = pyo.ConcreteModel(name=f"NuclearDC_Case{cfg.case.case_id}")
    m.T = pyo.RangeSet(0, ts.num_hours - 1)

    # ---- Time-series parameters --------------------------------------------
    m.P_IT = pyo.Param(
        m.T,
        initialize={t: float(ts.it_load_MW.iloc[t]) for t in m.T},
        within=pyo.NonNegativeReals,
    )
    m.LMP = pyo.Param(
        m.T,
        initialize={t: float(ts.price_import_usd_per_mwh.iloc[t]) for t in m.T},
        within=pyo.Reals,
    )
    m.AEF = pyo.Param(
        m.T,
        initialize={t: float(ts.carbon_intensity_g_per_kwh.iloc[t]) for t in m.T},
        within=pyo.NonNegativeReals,
    )
    # IT power becomes heat the cooling system must reject each hour
    # (eta_chain = chilled-water distribution losses). PUE is a reported
    # outcome, not a driver of the heat load; S1 sweeps the effective cooling
    # COP (vcc.cop_houston) instead of PUE.
    Q_cool_demand = {
        t: float(ts.it_load_MW.iloc[t]) / eta_chain for t in m.T
    }
    m.Q_cool_demand = pyo.Param(
        m.T, initialize=Q_cool_demand, within=pyo.NonNegativeReals
    )

    # Absorption COP and availability (P1-A) ---------------------------------
    if eq.absorption_chiller_enabled and cfg.case.absorption is not None:
        ab = cfg.case.absorption
        cop_t = {
            t: _absorption_cop(
                float(ts.wet_bulb_C.iloc[t]),
                ab.cop_houston_baseline,
                ab.derate_per_celsius_above_baseline,
                ab.cop_nameplate,
            )
            for t in m.T
        }
        avail_t = {
            t: ab.availability
            if _absorption_available(
                float(ts.wet_bulb_C.iloc[t]),
                ab.cooling_water_approach_K,
                ab.crystallization_cw_inlet_C,
            )
            else 0.0
            for t in m.T
        }
        m.COP_abs = pyo.Param(m.T, initialize=cop_t, within=pyo.NonNegativeReals)
        m.absorption_available = pyo.Param(
            m.T, initialize=avail_t, within=pyo.NonNegativeReals
        )

    # ---- Reactor (always required for Cases 1-2) ---------------------------
    rx = cfg.case.reactor
    if rx is None:
        raise ValueError("Cases 1-2 require a reactor block in plant_caseN.yaml")
    P_rx_cap = cap.reactor_thermal_capacity_MWth or rx.thermal_power_MWth
    P_rx_min = rx.min_load_fraction * P_rx_cap
    ramp_max_per_hour = rx.ramp_rate_pct_per_min / 100.0 * 60.0 * P_rx_cap

    m.P_rx = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(P_rx_min, P_rx_cap))

    # A8 ramp limits (no on/off binary — natural-circulation BWR stays online
    # above min_load_fraction, so explicit uptime/downtime binaries would
    # never bind; reactor_cf below enforces the 12 h-class behavior in aggregate)
    def ramp_up(mdl, t):
        if t == mdl.T.first():
            return pyo.Constraint.Skip
        return mdl.P_rx[t] - mdl.P_rx[t - 1] <= ramp_max_per_hour

    def ramp_down(mdl, t):
        if t == mdl.T.first():
            return pyo.Constraint.Skip
        return mdl.P_rx[t - 1] - mdl.P_rx[t] <= ramp_max_per_hour

    m.ramp_up = pyo.Constraint(m.T, rule=ramp_up)
    m.ramp_down = pyo.Constraint(m.T, rule=ramp_down)

    # v2.6 §A: enforce capacity factor on full-year runs.
    # Soft annual-mean lower bound rather than forced outages — the model is
    # too coarse for explicit outage scheduling.
    if ts.num_hours == 8760:
        m.reactor_cf = pyo.Constraint(
            expr=sum(m.P_rx[t] for t in m.T)
            >= rx.capacity_factor * P_rx_cap * ts.num_hours
        )

    # ---- Absorption steam tap (Case 2 only) --------------------------------
    if eq.absorption_chiller_enabled and cfg.case.absorption is not None:
        Q_abs_cool_max = cap.absorption_capacity_MWth or 100.0
        # Steam-side cap derived from worst case ratio
        Q_to_abs_max = Q_abs_cool_max / max(0.5, cfg.case.absorption.cop_nameplate)
        m.Q_to_abs = pyo.Var(
            m.T, domain=pyo.NonNegativeReals, bounds=(0, Q_to_abs_max)
        )
        m.Q_abs_cool = pyo.Var(m.T, domain=pyo.NonNegativeReals)
        m.abs_yield = pyo.Constraint(
            m.T,
            rule=lambda mdl, t: mdl.Q_abs_cool[t]
            == mdl.COP_abs[t] * mdl.absorption_available[t] * mdl.Q_to_abs[t],
        )
    else:
        m.Q_to_abs = pyo.Param(m.T, initialize=0.0)
        m.Q_abs_cool = pyo.Param(m.T, initialize=0.0)

    # ---- Turbine (cascaded HP extraction, v2.6 Willans line) ---------------
    tb = cfg.case.turbine
    if tb is None:
        raise ValueError("Cases 1-2 require a turbine block in plant_caseN.yaml")
    willans = tb.extraction_willans_slope_MWe_per_MWth

    m.P_turb_gross = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.turb_eq = pyo.Constraint(
        m.T,
        rule=lambda mdl, t: mdl.P_turb_gross[t]
        == tb.rated_efficiency * mdl.P_rx[t] - willans * mdl.Q_to_abs[t],
    )

    # Net = gross less auxiliaries
    m.P_turb_net = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.turb_net = pyo.Constraint(
        m.T,
        rule=lambda mdl, t: mdl.P_turb_net[t]
        == (1.0 - tb.aux_load_fraction) * mdl.P_turb_gross[t],
    )

    # ---- VCC (backup chiller in Case 2 or primary in Case 1) ---------------
    vcc = cfg.case.vcc
    if vcc is None:
        raise ValueError("Cases 1-2 require a vcc block (backup chiller)")
    Q_vcc_max = cap.electric_chiller_capacity_MWth or 0.0
    # Part-load: VCC electricity follows the non-convex IPLV COP curve, so the
    # chiller is an SOS2 piecewise map P_vcc = f(Q_vcc_cool) rather than a single
    # constant-COP line. This makes the model a MILP.
    vcc_q_pts, vcc_p_pts = vcc_pwl_points(vcc.cop_houston, Q_vcc_max)
    m.P_vcc = pyo.Var(
        m.T, domain=pyo.NonNegativeReals, bounds=(0, max(vcc_p_pts))
    )
    m.Q_vcc_cool = pyo.Var(
        m.T, domain=pyo.NonNegativeReals, bounds=(0, Q_vcc_max)
    )
    if Q_vcc_max > 0:
        _vcc_p_of_q = dict(zip(vcc_q_pts, vcc_p_pts))
        m.vcc_pwl = pyo.Piecewise(
            m.T,
            m.P_vcc,
            m.Q_vcc_cool,
            pw_pts=vcc_q_pts,
            pw_constr_type="EQ",
            f_rule=lambda mdl, t, x: _vcc_p_of_q[x],
            pw_repn="SOS2",
        )
    else:
        m.vcc_eq = pyo.Constraint(m.T, rule=lambda mdl, t: mdl.P_vcc[t] == 0.0)

    # ---- Grid (v2.6 §A: PCC interconnect limit) ----------------------------
    pcc_cap = cap.pcc_capacity_MW or 300.0
    if eq.grid_import_enabled:
        m.P_grid_buy = pyo.Var(
            m.T, domain=pyo.NonNegativeReals, bounds=(0, pcc_cap)
        )
    else:
        m.P_grid_buy = pyo.Param(m.T, initialize=0.0)
    if eq.grid_export_enabled:
        m.P_grid_sell = pyo.Var(
            m.T, domain=pyo.NonNegativeReals, bounds=(0, pcc_cap)
        )
    else:
        m.P_grid_sell = pyo.Param(m.T, initialize=0.0)

    # ---- BESS (S3 binary sensitivity) --------------------------------------
    # LP formulation: round-trip loss in the objective makes simultaneous
    # charge/discharge unprofitable, so no integer interlock is needed.
    if eq.bess_enabled and cfg.case.bess is not None:
        bs = cfg.case.bess
        Cap_E = cap.bess_capacity_MWh
        Cap_P = cap.bess_power_MW
        if Cap_E is None or Cap_P is None:
            raise ValueError(
                "BESS enabled but capacities.bess_capacity_MWh / bess_power_MW missing"
            )
        sqrt_eta = bs.round_trip_efficiency ** 0.5
        soc_min = bs.soc_min_fraction * Cap_E
        soc_max = bs.soc_max_fraction * Cap_E
        soc_init = bs.initial_soc_fraction * Cap_E

        m.B_charge = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(0, Cap_P))
        m.B_discharge = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(0, Cap_P))
        m.B_soc = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(soc_min, soc_max))

        def soc_dynamics(mdl, t):
            if t == mdl.T.first():
                prev = soc_init
            else:
                prev = mdl.B_soc[t - 1]
            return mdl.B_soc[t] == prev * (1 - bs.self_discharge_per_hour) + (
                sqrt_eta * mdl.B_charge[t] - mdl.B_discharge[t] / sqrt_eta
            ) * dt

        m.bess_soc_dyn = pyo.Constraint(m.T, rule=soc_dynamics)

        # Cycle closure: only enforce for full-year runs to avoid penalizing
        # short smoke tests that can't naturally close the cycle.
        if ts.num_hours == 8760:
            m.bess_cycle_closure = pyo.Constraint(
                expr=m.B_soc[m.T.last()] == soc_init
            )
    else:
        m.B_charge = pyo.Param(m.T, initialize=0.0)
        m.B_discharge = pyo.Param(m.T, initialize=0.0)

    # ---- Energy balances ---------------------------------------------------
    # Absorption-chiller parasitic electric load (v2.6 §F.1: ~0.02 kWe/kWth)
    absorption_parasitic = (
        cfg.case.absorption.parasitic_kWe_per_kWth
        if (eq.absorption_chiller_enabled and cfg.case.absorption is not None)
        else 0.0
    )

    def electric_balance(mdl, t):
        absorption_aux = absorption_parasitic * mdl.Q_abs_cool[t]
        return (
            mdl.P_turb_net[t] + mdl.P_grid_buy[t] + mdl.B_discharge[t]
            == mdl.P_IT[t]
            + mdl.P_vcc[t]
            + absorption_aux
            + mdl.P_grid_sell[t]
            + mdl.B_charge[t]
        )

    m.elec_balance = pyo.Constraint(m.T, rule=electric_balance)

    def cooling_balance(mdl, t):
        return mdl.Q_abs_cool[t] + mdl.Q_vcc_cool[t] == mdl.Q_cool_demand[t]

    m.cool_balance = pyo.Constraint(m.T, rule=cooling_balance)

    # ---- Objective: TAC (v2.6 unified accounting, ORC removed) -------------
    capex_annual_expr = 0.0
    fom_annual_expr = 0.0
    capex_annual_expr += annualized_capex(
        rx.capex_usd_per_kWe * rx.electric_power_net_MWe * 1000.0, wacc, rx.lifetime_years
    )
    fom_annual_expr += rx.fixed_om_usd_per_kWe_year * rx.electric_power_net_MWe * 1000.0
    if tb.capex_usd_per_kWe > 0:
        # Turbine is bundled into the reactor island; amortize over reactor life.
        capex_annual_expr += annualized_capex(
            tb.capex_usd_per_kWe * rx.electric_power_net_MWe * 1000.0, wacc, rx.lifetime_years
        )
        fom_annual_expr += tb.fixed_om_usd_per_kWe_year * rx.electric_power_net_MWe * 1000.0
    capex_annual_expr += annualized_capex(
        vcc.capex_usd_per_kWth * Q_vcc_max * 1000.0, wacc, vcc.lifetime_years
    )
    fom_annual_expr += vcc.fixed_om_usd_per_kWth_year * Q_vcc_max * 1000.0
    if eq.absorption_chiller_enabled and cfg.case.absorption is not None:
        ab = cfg.case.absorption
        abs_cap_MWth = cap.absorption_capacity_MWth or 100.0
        capex_annual_expr += annualized_capex(
            ab.capex_usd_per_kWth * abs_cap_MWth * 1000.0, wacc, ab.lifetime_years
        )
        fom_annual_expr += ab.fixed_om_usd_per_kWth_year * abs_cap_MWth * 1000.0
    if eq.bess_enabled and cfg.case.bess is not None:
        bs = cfg.case.bess
        Cap_E = cap.bess_capacity_MWh
        Cap_P = cap.bess_power_MW
        capex_annual_expr += annualized_capex(
            bs.capex_usd_per_kwh * Cap_E * 1000.0,
            wacc,
            bs.lifetime_years,
            bs.end_of_life_credit_pct / 100.0,
        )
        fom_annual_expr += bs.fixed_om_usd_per_kw_year * Cap_P * 1000.0

    # Full VOM expression
    vom_annual_expr = (
        sum(
            (rx.variable_om_usd_per_mwh_e + tb.variable_om_usd_per_mwh_e)
            * m.P_turb_net[t]
            + vcc.variable_om_usd_per_mwh_th * m.Q_vcc_cool[t]
            for t in m.T
        )
        * dt
        * annual_scale
    )
    if eq.absorption_chiller_enabled and cfg.case.absorption is not None:
        vom_annual_expr = vom_annual_expr + sum(
            cfg.case.absorption.variable_om_usd_per_mwh_th * m.Q_abs_cool[t]
            for t in m.T
        ) * dt * annual_scale
    if eq.bess_enabled and cfg.case.bess is not None:
        # VOM scales with throughput (charge + discharge), per NREL ATB convention.
        vom_annual_expr = vom_annual_expr + sum(
            cfg.case.bess.variable_om_usd_per_mwh
            * (m.B_charge[t] + m.B_discharge[t])
            for t in m.T
        ) * dt * annual_scale

    fuel_annual_expr = (
        sum(rx.fuel_cost_usd_per_mwh_th * m.P_rx[t] for t in m.T) * dt * annual_scale
    )

    grid_annual_expr = (
        sum(
            m.LMP[t] * (m.P_grid_buy[t] - m.P_grid_sell[t]) for t in m.T
        )
        * dt
        * annual_scale
    )

    # v2.7 §S6: carbon cost = price × net annual CO2 (tonnes).
    # Mirrors result.extract_result's accounting so the optimizer sees the
    # same emissions number that ends up in summary.json. Net = reactor LCA
    # + imported grid AEF − exported grid AEF (export credits the dirtier
    # ERCOT marginal mix that the cogen displaces).
    carbon_price = cfg.base.physics.carbon_price_usd_per_tco2
    co2_net_kg_expr = (
        sum(rx.co2_lifecycle_g_per_kwh_e * m.P_turb_net[t] for t in m.T)
        + sum(m.AEF[t] * m.P_grid_buy[t] for t in m.T)
        - sum(m.AEF[t] * m.P_grid_sell[t] for t in m.T)
    ) * dt * annual_scale
    carbon_annual_expr = carbon_price * co2_net_kg_expr / 1000.0  # → $/yr

    # Section 45U nuclear production tax credit (IRA 2022 Sec. 13105;
    # 26 U.S.C. 45U(b)). A per-MWh credit on net nuclear generation whose rate
    # falls with the hourly market price per the statutory gross-receipts
    # phaseout (full $15/MWh below $25/MWh, zero at $43.75/MWh). LMP is a known
    # parameter, so the per-hour rate is a constant and the credit stays linear
    # in P_turb_net. Default-on for Cases 1-2; entered as a negative cost.
    fin = cfg.financial
    if fin.nuclear_ptc_enabled:
        ptc_rate_t = {
            t: float(
                section_45u_credit_usd_per_mwh(
                    float(ts.price_import_usd_per_mwh.iloc[t]),
                    fin.ptc_usd_per_mwh_assumed,
                    fin.ptc_45u_phaseout_start_usd_per_mwh,
                    fin.ptc_45u_phaseout_end_usd_per_mwh,
                )
            )
            for t in m.T
        }
        ptc_annual_expr = (
            -sum(ptc_rate_t[t] * m.P_turb_net[t] for t in m.T) * dt * annual_scale
        )
    else:
        ptc_annual_expr = 0.0

    m.capex_annual = pyo.Expression(expr=capex_annual_expr)
    m.fom_annual = pyo.Expression(expr=fom_annual_expr)
    m.vom_annual = pyo.Expression(expr=vom_annual_expr)
    m.fuel_annual = pyo.Expression(expr=fuel_annual_expr)
    m.grid_annual = pyo.Expression(expr=grid_annual_expr)
    m.carbon_annual = pyo.Expression(expr=carbon_annual_expr)
    m.ptc_annual = pyo.Expression(expr=ptc_annual_expr)

    m.objective = pyo.Objective(
        expr=(
            m.capex_annual
            + m.fom_annual
            + m.vom_annual
            + m.fuel_annual
            + m.grid_annual
            + m.carbon_annual
            + m.ptc_annual
        ),
        sense=pyo.minimize,
    )

    # Sidecar metadata for the result-extractor (saves passing cfg around)
    m._annual_scale = annual_scale
    m._dt = dt
    m._pue = pue_used

    return m
