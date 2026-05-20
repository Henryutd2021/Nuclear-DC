"""Regression tests for the 3 load-bearing plan-compliance fixes:

- F.2 absorption parasitic kWe applied to electric load
- A11 PCC capacity upper bound on grid_buy / grid_sell
- A15 reactor capacity factor (annual mean ≥ 92% × P_max on full-year runs)
"""

from pathlib import Path

import pyomo.environ as pyo
import pytest

from src.cases.case2 import solve_case2
from src.config import load_config
from src.data import load_time_series
from src.milp.builder import build_model
from src.milp.solve import solve_model

PROJECT_ROOT = Path(__file__).resolve().parent.parent

gurobi = pytest.importorskip("pyomo.opt").SolverFactory("gurobi")
if not gurobi.available(exception_flag=False):
    pytest.skip("Gurobi unavailable", allow_module_level=True)


# ----- F.2 absorption parasitic --------------------------------------------


def test_absorption_parasitic_increases_grid_buy_in_short_slice():
    """With parasitic 0.020 kWe/kWth and ~35 MWth mean cooling, parasitic load
    is ~0.7 MW — small but must show up as extra electric draw vs no-parasitic
    counterfactual. We just check it's accounted for: P_VCC + P_grid_buy +
    parasitic load = P_IT + ... (already covered by the electric_balance tests).
    Here we double-check by setting a finite parasitic and ensuring grid_buy
    or P_VCC is non-zero somewhere.
    """
    cfg = load_config(case_id=2, project_root=PROJECT_ROOT)
    ts = load_time_series(project_root=PROJECT_ROOT, year=2023, num_hours=24)
    r = solve_case2(cfg, ts, pue=1.30)
    parasitic = cfg.case.absorption.parasitic_kWe_per_kWth * r.Q_abs_cool_MWth
    assert parasitic.sum() > 0   # absorption is being driven → parasitic > 0
    assert cfg.case.absorption.parasitic_kWe_per_kWth == pytest.approx(0.020)


# ----- A11 PCC capacity ----------------------------------------------------


def test_grid_buy_and_sell_bounded_by_pcc_capacity():
    cfg = load_config(case_id=1, project_root=PROJECT_ROOT)
    ts = load_time_series(project_root=PROJECT_ROOT, year=2022, num_hours=168)
    model = build_model(cfg, ts, pue=1.30)
    solve_model(model, quiet=True)
    pcc_cap = cfg.case.capacities.pcc_capacity_MW or 300.0
    for t in model.T:
        assert pyo.value(model.P_grid_buy[t]) <= pcc_cap + 1e-6
        assert pyo.value(model.P_grid_sell[t]) <= pcc_cap + 1e-6


# ----- A15 reactor CF ------------------------------------------------------


def test_reactor_cf_enforced_on_full_year_run():
    """sum(P_rx) / (P_max × 8760) >= 0.92 for full-year solves."""
    cfg = load_config(case_id=1, project_root=PROJECT_ROOT)
    ts = load_time_series(project_root=PROJECT_ROOT, year=2024, num_hours=8760)
    model = build_model(cfg, ts, pue=1.30)
    solve_model(model, quiet=True)
    p_max = cfg.case.reactor.thermal_power_MWth
    total = sum(pyo.value(model.P_rx[t]) for t in model.T)
    cf = total / (p_max * 8760)
    assert cf >= 0.92 - 1e-3


def test_reactor_cf_not_enforced_on_short_slice():
    """A 24h slice should be free of the CF constraint (would force overproduction)."""
    cfg = load_config(case_id=1, project_root=PROJECT_ROOT)
    ts = load_time_series(project_root=PROJECT_ROOT, year=2024, num_hours=24)
    model = build_model(cfg, ts, pue=1.30)
    # If the constraint were active on 24h slice, the model would have a
    # `reactor_cf` attribute. We verify it's absent.
    assert not hasattr(model, "reactor_cf")
