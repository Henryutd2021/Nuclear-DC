"""Capital annualization helpers and the Section 45U nuclear PTC schedule.

Each asset is amortized over its own engineering life rather than a single
project-wide window, and assets with end-of-life value receive a sinking-fund
salvage credit. Both reduce to the textbook equivalent-annual-cost identity

    EAC = P * CRF(i, n) - F * SFF(i, n),

with capital P, salvage F = salvage_fraction * P, recovery factor
CRF(i, n) = i (1+i)^n / ((1+i)^n - 1), and sinking-fund factor
SFF(i, n) = CRF(i, n) - i = i / ((1+i)^n - 1).
"""

from __future__ import annotations

import numpy as np


def crf(wacc: float, lifetime_years: int) -> float:
    """Capital recovery factor at discount rate ``wacc`` over ``lifetime_years``."""
    if wacc <= 0.0:
        raise ValueError(f"wacc must be > 0, got {wacc!r}")
    if lifetime_years <= 0:
        raise ValueError(f"lifetime_years must be > 0, got {lifetime_years!r}")
    growth = (1.0 + wacc) ** lifetime_years
    return wacc * growth / (growth - 1.0)


def annualized_capex(
    capex: float,
    wacc: float,
    lifetime_years: int,
    salvage_fraction: float = 0.0,
) -> float:
    """Annual capital charge for ``capex`` recovered over its own life.

    ``salvage_fraction`` is the fraction of overnight capital recovered at end
    of life and credited via the sinking-fund factor. With no salvage this is
    simply ``capex * crf(wacc, lifetime_years)``.
    """
    if not 0.0 <= salvage_fraction < 1.0:
        raise ValueError(
            f"salvage_fraction must be in [0, 1), got {salvage_fraction!r}"
        )
    recovery = crf(wacc, lifetime_years)
    return capex * (recovery * (1.0 - salvage_fraction) + salvage_fraction * wacc)


def section_45u_credit_usd_per_mwh(
    market_price_usd_per_mwh,
    full_credit_usd_per_mwh: float = 15.0,
    phaseout_start_usd_per_mwh: float = 25.0,
    phaseout_end_usd_per_mwh: float = 43.75,
):
    """IRA-2022 Section 45U zero-emission nuclear PTC as a function of price.

    The credit follows the statutory gross-receipts phaseout (26 U.S.C. 45U(b),
    IRA 2022 Sec. 13105). At the prevailing-wage rate the full credit is
    1.5 cents/kWh ($15/MWh); it is held flat while the facility's receipts per
    kWh stay at or below the 2.5 cents/kWh ($25/MWh) threshold, then reduced by
    16 percent (x5 for the prevailing-wage multiplier, i.e. a 0.8 $/$ slope) of
    the excess, reaching zero at 4.375 cents/kWh ($43.75/MWh):

        C(p) = full                              if p <= start
             = full * (1 - (p - start)/band)     if start < p < end
             = 0                                 if p >= end

    where band = end - start. Here the hourly market price (LMP) stands in for
    the per-kWh gross receipts. The statutory amounts are inflation-adjusted
    after 2024; the defaults hold the nominal 2024 prevailing-wage values, and
    the breakpoints are overridable to use the inflation-adjusted figures.

    Accepts a scalar or a numpy array and returns the same shape.
    """
    band = phaseout_end_usd_per_mwh - phaseout_start_usd_per_mwh
    if band <= 0.0:
        raise ValueError(
            "phaseout_end must exceed phaseout_start, got "
            f"{phaseout_end_usd_per_mwh!r} <= {phaseout_start_usd_per_mwh!r}"
        )
    p = np.asarray(market_price_usd_per_mwh, dtype=float)
    ramp = full_credit_usd_per_mwh * (
        1.0 - (p - phaseout_start_usd_per_mwh) / band
    )
    credit = np.where(p <= phaseout_start_usd_per_mwh, full_credit_usd_per_mwh, ramp)
    credit = np.where(p >= phaseout_end_usd_per_mwh, 0.0, credit)
    if np.isscalar(market_price_usd_per_mwh) or np.ndim(market_price_usd_per_mwh) == 0:
        return float(credit)
    return credit
