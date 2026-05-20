"""Phase 2A integration: Case 0 (grid-only) vs Case 4 (NGCC off-grid).

Cross-case Heat-Recovery Premium directional checks against the v2.5 §B/§C
narrative. The S2 ERCOT year regime (2022 volatile / 2023 high / 2024 low)
and the Henry Hub year regime (2022 spike / 2023 normal / 2024 low) jointly
determine whether on-site gas beats grid power.
"""

from pathlib import Path

import pytest

from src.cases.case0 import solve_case0
from src.cases.case4 import solve_case4
from src.config import load_config
from src.data import load_time_series
from src.kpi import heat_recovery_premium

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration


def _solve_both(year: int, pue: float):
    cfg0 = load_config(case_id=0, project_root=PROJECT_ROOT)
    cfg4 = load_config(case_id=4, project_root=PROJECT_ROOT)
    ts = load_time_series(project_root=PROJECT_ROOT, year=year, num_hours=8760)
    r0 = solve_case0(cfg0, ts, pue=pue)
    r4 = solve_case4(cfg4, ts, pue=pue)
    return r0, r4


def test_case4_always_dirtier_than_case0_per_kwh():
    """NGCC 420 g/kWh_lifecycle > ERCOT AEF 320-350 g/kWh — Case 4 dirtier all years."""
    for year in (2022, 2023, 2024):
        r0, r4 = _solve_both(year, pue=1.30)
        co2_per_mwh_0 = r0.co2_annual_tonnes * 1000.0 / (r0.P_IT_MW.sum() * 8760.0 / r0.P_IT_MW.shape[0])
        co2_per_mwh_4 = r4.co2_lifecycle_annual_tonnes * 1000.0 / (r4.P_IT_MW.sum() * 8760.0 / r4.P_IT_MW.shape[0])
        assert co2_per_mwh_4 > co2_per_mwh_0, f"year={year}: Case 4 should be dirtier"


def test_premium_case4_year_regime_signs():
    """NGCC-vs-grid winner depends on the LMP/NG-price interaction:

    - 2022: high LMP ($80) but high NG ($6.45) → Case 4 loses by ~10%
    - 2023: high LMP ($55) and cheap NG ($2.53) → Case 4 WINS by ~15-20%  ← sweet spot
    - 2024: cheap LMP ($28) and cheap NG ($2.19) → Case 4 loses badly (~-70%)
    """
    r0_22, r4_22 = _solve_both(2022, pue=1.30)
    r0_23, r4_23 = _solve_both(2023, pue=1.30)
    r0_24, r4_24 = _solve_both(2024, pue=1.30)
    prem = {
        2022: heat_recovery_premium(r0_22.tac_usd_per_yr, r4_22.tac_usd_per_yr),
        2023: heat_recovery_premium(r0_23.tac_usd_per_yr, r4_23.tac_usd_per_yr),
        2024: heat_recovery_premium(r0_24.tac_usd_per_yr, r4_24.tac_usd_per_yr),
    }
    assert prem[2022] < 0, f"2022 expected NGCC loss, got {prem[2022]:.3f}"
    assert prem[2023] > 0, f"2023 expected NGCC win, got {prem[2023]:.3f}"
    assert prem[2024] < 0, f"2024 expected NGCC loss, got {prem[2024]:.3f}"


def test_2024_is_worst_year_for_case4():
    """Case 4 most uneconomic when cheap LMP combines with capex amortization burden."""
    prems = {}
    for year in (2022, 2023, 2024):
        r0, r4 = _solve_both(year, pue=1.30)
        prems[year] = heat_recovery_premium(r0.tac_usd_per_yr, r4.tac_usd_per_yr)
    assert prems[2024] < prems[2022] < prems[2023]


def test_case4_fuel_is_dominant_opex_in_2022():
    """2022 NG spike → fuel_annual should dominate Case 4 OPEX."""
    _, r4 = _solve_both(2022, pue=1.30)
    opex = r4.fom_annual_usd + r4.vom_annual_usd + r4.fuel_annual_usd
    assert r4.fuel_annual_usd / opex > 0.55  # fuel ≥ 55% of OPEX in 2022 spike
