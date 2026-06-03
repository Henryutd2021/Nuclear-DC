"""Case 0 — grid-only baseline (v2.5 §B).

Per v2.5 §2.1, Case 0 runs as an "independent LP estimation" rather than as
part of the unified MILP. With a fixed PUE and no on-site generation or
storage, dispatch is deterministic per hour:

    Q_cool(t) = (PUE - 1) * P_IT(t) / eta_chain      [v2.5 §F definition]
    P_VCC(t) = Q_cool(t) / COP_VCC_Houston           [v2.5 §B + Houston derating]
    P_grid_buy(t) = P_IT(t) + P_VCC(t)               [grid covers everything]

TAC then follows the §2.0.3 unified formula:

    TAC = CRF * CAPEX + FOM + VOM_annual + Grid_annual    (Carbon term zero
                                                          when no carbon
                                                          price; emissions
                                                          tracked separately
                                                          for KPI accounting)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.config import RunConfig
from src.data import TimeSeries


@dataclass(frozen=True)
class Case0Result:
    """Outputs of a Case 0 solve: hourly dispatch + annualized cost."""

    # Hourly dispatch (length == ts.num_hours)
    P_IT_MW: pd.Series
    Q_cool_MWth: pd.Series
    P_VCC_elec_MW: pd.Series
    P_grid_buy_MW: pd.Series
    grid_cost_usd_per_h: pd.Series
    grid_emissions_kg_co2_per_h: pd.Series

    # Scalars
    vcc_capacity_MWth: float
    pue: float
    capex_annual_usd: float
    fom_annual_usd: float
    vom_annual_usd: float
    grid_annual_usd: float
    carbon_annual_usd: float
    tac_usd_per_yr: float
    co2_annual_tonnes: float


def solve_case0(
    cfg: RunConfig,
    ts: TimeSeries,
    pue: Optional[float] = None,
) -> Case0Result:
    """Compute Case 0 dispatch and TAC for a given configuration and year slice.

    Args:
        cfg: ``RunConfig`` loaded for ``case_id=0``.
        ts: Aligned hourly time series (one ERCOT year).
        pue: Override the PUE setpoint (defaults to ``cfg.base.physics.pue_default``).
            v2.5 S1 sensitivity values: {1.10, 1.30, 1.50}.

    Returns:
        ``Case0Result`` bundling per-hour dispatch and annualized accounting.

    Raises:
        ValueError: cooling demand exceeds installed VCC capacity in any hour.
    """
    if cfg.case.case_id != 0:
        raise ValueError(f"solve_case0 requires case_id=0, got {cfg.case.case_id}")
    if cfg.case.vcc is None:
        raise ValueError("Case 0 requires a vcc block in plant_case0.yaml")

    vcc = cfg.case.vcc
    pue_used = float(pue if pue is not None else cfg.base.physics.pue_default)
    eta_chain = cfg.base.physics.cooling_chain_efficiency
    dt = cfg.base.time.delta_t

    # ---- Hourly dispatch (deterministic) -----------------------------------
    # All IT electrical draw ends up as heat the chiller must reject; eta_chain
    # captures chilled-water distribution losses. PUE is a reported outcome
    # (1 + P_VCC/P_IT), not an input to the heat load.
    P_IT = ts.it_load_MW
    Q_cool = P_IT / eta_chain
    P_VCC = Q_cool / vcc.cop_houston
    P_grid_buy = P_IT + P_VCC

    Q_capacity = cfg.case.capacities.electric_chiller_capacity_MWth
    if Q_capacity is None:
        raise ValueError("Case 0 requires capacities.electric_chiller_capacity_MWth")
    if Q_cool.max() > Q_capacity + 1e-6:
        raise ValueError(
            f"VCC capacity {Q_capacity} MWth insufficient for Q_cool max "
            f"{Q_cool.max():.2f} MWth (= P_IT_max / eta_chain)"
        )

    # ---- Hourly cost & emissions -------------------------------------------
    grid_cost_h = ts.price_import_usd_per_mwh * P_grid_buy * dt          # $/h
    emissions_kg_h = P_grid_buy * dt * ts.carbon_intensity_g_per_kwh      # kg/h

    # ---- Annualization -----------------------------------------------------
    annual_scale = 8760.0 / ts.num_hours

    capex_annual = (
        vcc.capex_usd_per_kWth
        * Q_capacity
        * 1000.0
        * cfg.financial.capital_recovery_factor
    )
    fom_annual = vcc.fixed_om_usd_per_kWth_year * Q_capacity * 1000.0
    vom_annual = (
        vcc.variable_om_usd_per_mwh_th
        * Q_cool.sum()
        * dt
        * annual_scale
    )
    grid_annual = grid_cost_h.sum() * annual_scale
    co2_annual_tonnes = emissions_kg_h.sum() * annual_scale / 1000.0

    # v2.7 §S6: carbon cost applied to net grid-AEF emissions. Case 0 has no
    # on-site generation so the only CO2 source is imported grid electricity.
    carbon_price = cfg.base.physics.carbon_price_usd_per_tco2
    carbon_annual = carbon_price * co2_annual_tonnes

    tac = capex_annual + fom_annual + vom_annual + grid_annual + carbon_annual

    return Case0Result(
        P_IT_MW=P_IT,
        Q_cool_MWth=Q_cool,
        P_VCC_elec_MW=P_VCC,
        P_grid_buy_MW=P_grid_buy,
        grid_cost_usd_per_h=grid_cost_h,
        grid_emissions_kg_co2_per_h=emissions_kg_h,
        vcc_capacity_MWth=Q_capacity,
        pue=pue_used,
        capex_annual_usd=capex_annual,
        fom_annual_usd=fom_annual,
        vom_annual_usd=vom_annual,
        grid_annual_usd=grid_annual,
        carbon_annual_usd=carbon_annual,
        tac_usd_per_yr=tac,
        co2_annual_tonnes=co2_annual_tonnes,
    )
