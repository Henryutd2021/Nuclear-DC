"""Case 1 — BWRX-300 + main turbine, no heat recovery (v2.5 §B).

The reactor's full thermal output goes through the main turbine to make
electricity for the data center; cooling is from a VCC chiller exactly like
Case 0. This case quantifies how much value the cogen system (ORC +
absorption) in Cases 2-3 adds on top of "just buying the reactor".

Unlike Case 0/4 which are closed-form, Case 1 is solved as an LP through
the unified MILP builder in ``src.milp.builder`` so its TAC accounting is
identical to Cases 2 and 3 (P1-C common-basis statement).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import pyomo.environ as pyo

from src.config import RunConfig
from src.data import TimeSeries
from src.milp.builder import build_model
from src.milp.solve import solve_model


@dataclass(frozen=True)
class Case1Result:
    """Outputs of a Case 1 solve."""

    # Hourly dispatch
    P_IT_MW: pd.Series
    Q_cool_MWth: pd.Series
    P_rx_MWth: pd.Series
    P_turb_net_MW: pd.Series
    P_VCC_elec_MW: pd.Series
    Q_VCC_cool_MWth: pd.Series
    P_grid_buy_MW: pd.Series
    P_grid_sell_MW: pd.Series

    # Scalars
    pue: float
    capex_annual_usd: float
    fom_annual_usd: float
    vom_annual_usd: float
    fuel_annual_usd: float
    grid_annual_usd: float
    tac_usd_per_yr: float
    co2_annual_tonnes: float


def solve_case1(
    cfg: RunConfig,
    ts: TimeSeries,
    pue: Optional[float] = None,
    solver_name: str = "gurobi",
) -> Case1Result:
    if cfg.case.case_id != 1:
        raise ValueError(f"solve_case1 requires case_id=1, got {cfg.case.case_id}")

    model = build_model(cfg, ts, pue=pue)
    solve_model(model, solver_name=solver_name)

    # Extract dispatch
    def _series(var):
        return pd.Series(
            [pyo.value(var[t]) for t in model.T], index=range(ts.num_hours)
        )

    P_IT = pd.Series(ts.it_load_MW.values, index=range(ts.num_hours))
    Q_cool_demand = pd.Series(
        [pyo.value(model.Q_cool_demand[t]) for t in model.T],
        index=range(ts.num_hours),
    )

    P_rx = _series(model.P_rx)
    P_turb_net = _series(model.P_turb_net)
    P_vcc = _series(model.P_vcc)
    Q_vcc_cool = _series(model.Q_vcc_cool)
    P_grid_buy = _series(model.P_grid_buy)
    P_grid_sell = _series(model.P_grid_sell)

    annual_scale = model._annual_scale
    dt = model._dt
    # Reactor LCA emissions only (no grid-source emissions in Case 1's electricity)
    rx = cfg.case.reactor
    co2_kg = (P_turb_net.sum() * dt * rx.co2_lifecycle_g_per_kwh_e) * annual_scale
    # Grid-buy electricity also carries grid carbon — add it
    aef = pd.Series(
        [pyo.value(model.AEF[t]) for t in model.T], index=range(ts.num_hours)
    )
    co2_grid_kg = (P_grid_buy * dt * aef).sum() * annual_scale
    # Grid-sell offsets some grid emissions (avoided)
    co2_offset_kg = (P_grid_sell * dt * aef).sum() * annual_scale
    co2_total_tonnes = (co2_kg + co2_grid_kg - co2_offset_kg) / 1000.0

    return Case1Result(
        P_IT_MW=P_IT,
        Q_cool_MWth=Q_cool_demand,
        P_rx_MWth=P_rx,
        P_turb_net_MW=P_turb_net,
        P_VCC_elec_MW=P_vcc,
        Q_VCC_cool_MWth=Q_vcc_cool,
        P_grid_buy_MW=P_grid_buy,
        P_grid_sell_MW=P_grid_sell,
        pue=model._pue,
        capex_annual_usd=float(pyo.value(model.capex_annual)),
        fom_annual_usd=float(pyo.value(model.fom_annual)),
        vom_annual_usd=float(pyo.value(model.vom_annual)),
        fuel_annual_usd=float(pyo.value(model.fuel_annual)),
        grid_annual_usd=float(pyo.value(model.grid_annual)),
        tac_usd_per_yr=float(pyo.value(model.objective)),
        co2_annual_tonnes=co2_total_tonnes,
    )
