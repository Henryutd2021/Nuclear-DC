"""Tests for src.cases.case2 — full cogen MILP (reactor + turbine + ORC + abs + VCC backup)."""

from pathlib import Path

import pytest

from src.cases.case2 import solve_case2
from src.config import load_config
from src.data import load_time_series

PROJECT_ROOT = Path(__file__).resolve().parent.parent

gurobi = pytest.importorskip("pyomo.opt").SolverFactory("gurobi")
if not gurobi.available(exception_flag=False):
    pytest.skip("Gurobi unavailable", allow_module_level=True)


@pytest.fixture(scope="module")
def cfg():
    return load_config(case_id=2, project_root=PROJECT_ROOT)


@pytest.fixture(scope="module")
def ts_2023_168h():
    return load_time_series(project_root=PROJECT_ROOT, year=2023, num_hours=168)


def test_case2_solve_returns_optimal(cfg, ts_2023_168h):
    r = solve_case2(cfg, ts_2023_168h)
    assert r.tac_usd_per_yr > 0
    assert r.case_id == 2


def test_case2_electric_balance_closes(cfg, ts_2023_168h):
    """P_turb_net + P_orc + P_grid_buy = P_IT + P_VCC + P_grid_sell."""
    r = solve_case2(cfg, ts_2023_168h)
    residual = (
        r.P_turb_net_MW
        + r.P_orc_MW
        + r.P_grid_buy_MW
        - r.P_IT_MW
        - r.P_VCC_elec_MW
        - r.P_grid_sell_MW
    ).abs().max()
    assert residual < 1e-4


def test_case2_cooling_balance_combines_abs_and_vcc(cfg, ts_2023_168h):
    """Q_abs_cool + Q_VCC_cool == Q_cool_demand every hour."""
    r = solve_case2(cfg, ts_2023_168h)
    residual = (r.Q_abs_cool_MWth + r.Q_VCC_cool_MWth - r.Q_cool_demand_MWth).abs().max()
    assert residual < 1e-4


def test_case2_reactor_min_load_and_ramp(cfg, ts_2023_168h):
    r = solve_case2(cfg, ts_2023_168h)
    assert r.P_rx_MWth.min() >= 435.0 - 1e-4
    deltas = r.P_rx_MWth.diff().abs().dropna()
    assert deltas.max() <= 522.0 + 1e-3


def test_case2_absorption_active_in_normal_hours(cfg, ts_2023_168h):
    """Cooling is dominantly served by absorption (free heat) when LMP > 0 and reactor on."""
    r = solve_case2(cfg, ts_2023_168h)
    # In aggregate, abs should cover at least 60% of cooling (rest is VCC backup or
    # hours where exporting electricity is more valuable than driving abs).
    abs_share = r.Q_abs_cool_MWth.sum() / r.Q_cool_demand_MWth.sum()
    assert abs_share > 0.6


def test_case2_capex_includes_orc_and_absorption(cfg, ts_2023_168h):
    """ORC + absorption CAPEX adds to the line vs Case 1 (same reactor)."""
    from src.cases.case1 import solve_case1
    cfg1 = load_config(case_id=1, project_root=PROJECT_ROOT)
    r1 = solve_case1(cfg1, ts_2023_168h)
    r2 = solve_case2(cfg, ts_2023_168h)
    # Case 2 capex must exceed Case 1 capex by the ORC + abs annualized capex
    delta = r2.capex_annual_usd - r1.capex_annual_usd
    assert delta > 7.0e6   # ORC $2,800/kWe × 8 MW × CRF + abs $750/kWth × 100 × CRF ≈ $9M
