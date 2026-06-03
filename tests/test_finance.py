"""Tests for per-component capital annualization (Tier 1 L1 + L2).

L1: each asset is amortized over its own engineering life via its own CRF,
instead of a single project-wide 20-year CRF.
L2: assets with an end-of-life salvage value get a sinking-fund credit, so the
annual capital charge is (P - F) recovered, i.e. EAC = P*CRF - F*SFF.
"""

import pytest

from src.finance import crf, annualized_capex


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
