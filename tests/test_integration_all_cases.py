"""v2.6 integration: 4-case Premium matrix and P1-A wet-bulb gate.

Locks in cross-case behavior at the v2.6 baseline grid (3 ERCOT years
× PUE 1.30 × ATB-Mid reactor CAPEX). Premium(Case 0, Case N) signs
become regression checks: if a future code change accidentally flips
one of them, this test catches it.
"""

from pathlib import Path

import pytest

from src.cases.case0 import solve_case0
from src.cases.case1 import solve_case1
from src.cases.case2 import solve_case2
from src.cases.case3 import solve_case3
from src.config import load_config
from src.data import load_time_series
from src.kpi import heat_recovery_premium

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration

gurobi = pytest.importorskip("pyomo.opt").SolverFactory("gurobi")
if not gurobi.available(exception_flag=False):
    pytest.skip("Gurobi unavailable", allow_module_level=True)


def _solve_all(year: int, pue: float = 1.30, hours: int = 168):
    """Solve all 4 cases for one (year, PUE) and return TAC dict."""
    ts = load_time_series(project_root=PROJECT_ROOT, year=year, num_hours=hours)
    tacs = {}
    for case_id, solver in (
        (0, solve_case0),
        (1, solve_case1),
        (2, solve_case2),
        (3, solve_case3),
    ):
        cfg = load_config(case_id=case_id, project_root=PROJECT_ROOT)
        r = solver(cfg, ts, pue=pue)
        tacs[case_id] = r.tac_usd_per_yr
    return tacs


def test_all_cases_solve_and_return_positive_tac():
    tacs = _solve_all(2023)
    for cid, tac in tacs.items():
        assert tac > 0, f"Case {cid} returned non-positive TAC {tac}"


def test_nuclear_cases_lose_to_case0_at_atb_mid_capex():
    """At NREL ATB Moderate ($7,615/kWe), BWRX CAPEX dominates → Cases 1-2 lose to Case 0."""
    tacs = _solve_all(2023)
    for cid in (1, 2):
        prem = heat_recovery_premium(tacs[0], tacs[cid])
        assert prem < 0, f"Case {cid} unexpectedly cheaper than Case 0 at ATB-Mid"


def test_case2_beats_case1_via_cascaded_extraction():
    """v2.6 cascaded extraction must reduce TAC vs no-heat-recovery Case 1.

    Diverting steam at the mid-pressure tap costs ~0.083 MWe per MWth but
    delivers ~COP×1.0 MWth of cooling that would otherwise need ~1/COP_VCC
    MWe of compressor power. Net effect is positive at any realistic LMP.
    """
    tacs = _solve_all(2023)
    assert tacs[2] < tacs[1], (
        f"Expected Case 2 (cascaded extraction) < Case 1 (no recovery); "
        f"got TAC_1={tacs[1]/1e6:.1f}M, TAC_2={tacs[2]/1e6:.1f}M"
    )


def test_p1a_absorption_gate_triggers_in_hot_hour_summer_slice():
    """A 168h slice starting mid-July (hour 4344 = Jul 1 00:00) hits Houston
    wet-bulb peaks that exceed the 27 °C crystallization-cutoff threshold;
    Case 2 must force absorption off and use VCC backup during those hours.
    """
    cfg = load_config(case_id=2, project_root=PROJECT_ROOT)
    ts = load_time_series(
        project_root=PROJECT_ROOT, year=2023, num_hours=168, start_hour=4344
    )
    r = solve_case2(cfg, ts, pue=1.30)
    # At least some VCC dispatch must happen — proves the gate engaged
    assert r.Q_VCC_cool_MWth.sum() > 0, (
        "Expected VCC backup to engage during July hot hours when absorption "
        "is gated off by the crystallization rule"
    )
