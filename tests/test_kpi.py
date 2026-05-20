"""Tests for src.kpi — v2.5 §D headline KPIs (TAC, LCOE, LCOC, CO2, Premium)."""

from pathlib import Path

import pytest

from src.cases.case0 import solve_case0
from src.config import load_config
from src.data import load_time_series
from src.kpi import compute_kpis_case0, heat_recovery_premium

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cfg():
    return load_config(case_id=0, project_root=PROJECT_ROOT)


@pytest.fixture(scope="module")
def ts_2023():
    return load_time_series(
        project_root=PROJECT_ROOT, year=2023, num_hours=168
    )


@pytest.fixture(scope="module")
def kpis(cfg, ts_2023):
    result = solve_case0(cfg, ts_2023)
    return compute_kpis_case0(result, ts_2023, cfg)


def test_tac_passthrough_equals_solver_output(cfg, ts_2023):
    result = solve_case0(cfg, ts_2023)
    kpis = compute_kpis_case0(result, ts_2023, cfg)
    assert kpis.tac_usd_per_yr == result.tac_usd_per_yr


def test_lcoe_positive_and_within_grid_only_band(kpis):
    """LCOE for grid-only DC should land in $30–$300/MWh band for ERCOT 2023."""
    assert kpis.lcoe_usd_per_mwh_e > 0
    assert 30 < kpis.lcoe_usd_per_mwh_e < 300


def test_lcoc_positive(kpis):
    """LCOC = cooling-attributable annualized cost / cooling delivered (MWh_c)."""
    assert kpis.lcoc_usd_per_mwh_c > 0


def test_co2_per_mwh_realistic(kpis):
    """Case 0 sources all electricity from ERCOT → kg/MWh ≈ ERCOT AEF × PUE factor."""
    # AEF 2023 ≈ 333 g/kWh = 333 kg/MWh; with PUE ~1.5, total / IT-MWh ≈ AEF × 1.5
    # Loose bounds: 300 < kg/MWh < 700
    assert 300 < kpis.co2_per_mwh_kg < 700


def test_co2_annual_tonnes_passthrough(cfg, ts_2023):
    result = solve_case0(cfg, ts_2023)
    kpis = compute_kpis_case0(result, ts_2023, cfg)
    assert kpis.co2_annual_tonnes == result.co2_annual_tonnes


def test_heat_recovery_premium_positive_when_case_cheaper():
    # Synthetic: baseline = $100M, case = $80M → premium = 0.2
    assert heat_recovery_premium(1.0e8, 8.0e7) == pytest.approx(0.2, abs=1e-9)


def test_heat_recovery_premium_zero_when_equal():
    assert heat_recovery_premium(5.0e7, 5.0e7) == pytest.approx(0.0, abs=1e-9)


def test_heat_recovery_premium_negative_when_case_more_expensive():
    # Baseline $100M, case $120M → premium = -0.2
    assert heat_recovery_premium(1.0e8, 1.2e8) == pytest.approx(-0.2, abs=1e-9)


def test_heat_recovery_premium_rejects_nonpositive_baseline():
    with pytest.raises(ValueError, match=r"baseline"):
        heat_recovery_premium(0.0, 1.0e7)
    with pytest.raises(ValueError, match=r"baseline"):
        heat_recovery_premium(-1.0e7, 1.0e7)


def test_lcoc_drops_as_pue_rises_capex_dominated(cfg, ts_2023):
    """At higher PUE, the fixed chiller CAPEX amortizes over MORE cooling.

    For Case 0 with a fixed VCC capacity, going from PUE 1.10 → 1.50
    roughly triples cooling delivered (denominator) while the LMP×P_VCC
    cooling-electricity term only doubles, so LCOC must strictly decrease.
    """
    r110 = solve_case0(cfg, ts_2023, pue=1.10)
    r150 = solve_case0(cfg, ts_2023, pue=1.50)
    k110 = compute_kpis_case0(r110, ts_2023, cfg)
    k150 = compute_kpis_case0(r150, ts_2023, cfg)
    assert k110.lcoc_usd_per_mwh_c > 0
    assert k150.lcoc_usd_per_mwh_c > 0
    assert k150.lcoc_usd_per_mwh_c < k110.lcoc_usd_per_mwh_c
