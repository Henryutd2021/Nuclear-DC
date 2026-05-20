"""Tests for src.cases.case3 — turbine + absorption (no ORC)."""

from pathlib import Path

import pytest

from src.cases.case3 import solve_case3
from src.config import load_config
from src.data import load_time_series

PROJECT_ROOT = Path(__file__).resolve().parent.parent

gurobi = pytest.importorskip("pyomo.opt").SolverFactory("gurobi")
if not gurobi.available(exception_flag=False):
    pytest.skip("Gurobi unavailable", allow_module_level=True)


@pytest.fixture(scope="module")
def cfg():
    return load_config(case_id=3, project_root=PROJECT_ROOT)


@pytest.fixture(scope="module")
def ts_2023_168h():
    return load_time_series(project_root=PROJECT_ROOT, year=2023, num_hours=168)


def test_case3_solve_returns_optimal(cfg, ts_2023_168h):
    r = solve_case3(cfg, ts_2023_168h)
    assert r.tac_usd_per_yr > 0
    assert r.case_id == 3


def test_case3_no_orc(cfg, ts_2023_168h):
    """ORC disabled → P_orc must be zero throughout."""
    r = solve_case3(cfg, ts_2023_168h)
    assert r.P_orc_MW.sum() == 0


def test_case3_electric_balance_closes(cfg, ts_2023_168h):
    r = solve_case3(cfg, ts_2023_168h)
    residual = (
        r.P_turb_net_MW
        + r.P_grid_buy_MW
        - r.P_IT_MW
        - r.P_VCC_elec_MW
        - r.P_grid_sell_MW
    ).abs().max()
    assert residual < 1e-4


def test_case3_cooling_balance_combines_abs_and_vcc(cfg, ts_2023_168h):
    r = solve_case3(cfg, ts_2023_168h)
    residual = (r.Q_abs_cool_MWth + r.Q_VCC_cool_MWth - r.Q_cool_demand_MWth).abs().max()
    assert residual < 1e-4


def test_case3_capex_less_than_case2_at_same_year(cfg, ts_2023_168h):
    """No ORC → Case 3 capex must be lower than Case 2 (same year, same PUE)."""
    from src.cases.case2 import solve_case2
    cfg2 = load_config(case_id=2, project_root=PROJECT_ROOT)
    r2 = solve_case2(cfg2, ts_2023_168h)
    r3 = solve_case3(cfg, ts_2023_168h)
    # ORC annualized capex ≈ $2,800/kWe × 8 MW × 1000 × 0.0922 ≈ $2.07M/yr
    delta = r2.capex_annual_usd - r3.capex_annual_usd
    assert delta > 1.5e6
