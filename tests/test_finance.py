"""Tests for per-component capital annualization (Tier 1 L1 + L2) and the
Section 45U nuclear production tax credit.

L1: each asset is amortized over its own engineering life via its own CRF,
instead of a single project-wide 20-year CRF.
L2: assets with an end-of-life salvage value get a sinking-fund credit, so the
annual capital charge is (P - F) recovered, i.e. EAC = P*CRF - F*SFF.
45U: the IRA-2022 zero-emission nuclear PTC is a per-MWh credit that phases out
with the market price (gross receipts) per 26 U.S.C. 45U(b).
"""

import numpy as np
import pytest

from src.finance import crf, annualized_capex, section_45u_credit_usd_per_mwh


def test_crf_20yr_at_6_7pct_matches_paper_value():
    # CRF(i=6.7%, n=20) is the 0.0922 used as the global factor today.
    assert crf(0.067, 20) == pytest.approx(0.0922, abs=5e-4)


def test_crf_30yr_at_6_7pct():
    assert crf(0.067, 30) == pytest.approx(0.0782, abs=5e-4)


def test_crf_15yr_at_6_7pct():
    assert crf(0.067, 15) == pytest.approx(0.1077, abs=5e-4)


def test_shorter_life_gives_higher_recovery_factor():
    # A 15-year battery must recover its capital faster than a 30-year plant.
    assert crf(0.067, 15) > crf(0.067, 20) > crf(0.067, 30)


def test_annualized_capex_without_salvage_is_capex_times_crf():
    capex = 1_000_000.0
    assert annualized_capex(capex, 0.067, 25) == pytest.approx(capex * crf(0.067, 25))


def test_salvage_credit_reduces_annual_capital_charge():
    capex = 1_000_000.0
    with_salvage = annualized_capex(capex, 0.067, 15, salvage_fraction=0.05)
    without_salvage = annualized_capex(capex, 0.067, 15, salvage_fraction=0.0)
    assert with_salvage < without_salvage


def test_annualized_capex_salvage_matches_sinking_fund_formula():
    # EAC = P*CRF - F*SFF, F = sf*P, SFF = CRF - i  ->  P*(CRF*(1-sf) + sf*i)
    capex, i, n, sf = 1_000_000.0, 0.067, 15, 0.05
    expected = capex * (crf(i, n) * (1.0 - sf) + sf * i)
    assert annualized_capex(capex, i, n, salvage_fraction=sf) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Section 45U nuclear PTC: piecewise credit C_45U(P_market), 26 U.S.C. 45U(b).
# Full 1.5 cents/kWh ($15/MWh, prevailing-wage rate) below the 2.5 cents/kWh
# ($25/MWh) gross-receipts threshold, then a linear ramp to $0 at 4.375 cents/kWh
# ($43.75/MWh). The ramp slope (0.8 $/$) is the statutory 16% reduction x5.
# ---------------------------------------------------------------------------
def test_45u_full_credit_below_threshold():
    assert section_45u_credit_usd_per_mwh(20.0) == pytest.approx(15.0)
    assert section_45u_credit_usd_per_mwh(0.0) == pytest.approx(15.0)


def test_45u_full_credit_at_threshold():
    assert section_45u_credit_usd_per_mwh(25.0) == pytest.approx(15.0)


def test_45u_zero_at_and_above_phaseout_end():
    assert section_45u_credit_usd_per_mwh(43.75) == pytest.approx(0.0, abs=1e-9)
    assert section_45u_credit_usd_per_mwh(50.0) == pytest.approx(0.0)
    assert section_45u_credit_usd_per_mwh(120.0) == pytest.approx(0.0)


def test_45u_linear_ramp_midpoint():
    # Midpoint of the $25-$43.75 band -> half credit.
    assert section_45u_credit_usd_per_mwh(34.375) == pytest.approx(7.5)


def test_45u_linear_ramp_slope_is_point_eight():
    # Each $1/MWh of price above the threshold removes $0.80 of credit.
    assert section_45u_credit_usd_per_mwh(30.0) == pytest.approx(15.0 - 0.8 * 5.0)


def test_45u_accepts_array_and_is_monotone_nonincreasing():
    prices = np.array([10.0, 25.0, 30.0, 43.75, 60.0])
    out = section_45u_credit_usd_per_mwh(prices)
    assert out.shape == (5,)
    assert np.all(np.diff(out) <= 1e-12)  # never increases with price
    assert out[0] == pytest.approx(15.0)
    assert out[-1] == pytest.approx(0.0)


def test_45u_custom_breakpoints():
    # The full credit and band are configurable (e.g. inflation-adjusted amounts).
    # p=30 is in the ramp: slope = 16.5/(48.125-27.5) = 0.8;
    # credit = 16.5 - 0.8*(30-27.5) = 14.5.
    out = section_45u_credit_usd_per_mwh(
        30.0, full_credit_usd_per_mwh=16.5, phaseout_start_usd_per_mwh=27.5,
        phaseout_end_usd_per_mwh=48.125,
    )
    assert out == pytest.approx(14.5)
