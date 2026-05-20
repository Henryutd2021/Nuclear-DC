"""Headline KPIs for Nuclear-DC (v2.5 §D subset for Phase 1).

Phase 1 covers 5 of the 8 KPIs locked in §D:
  - TAC (passthrough)
  - LCOE ($/MWh_e delivered to IT)
  - LCOC ($/MWh_c delivered as chilled water)
  - Annual CO2 (passthrough)
  - CO2 per MWh delivered (helper for LCA narrative)
  - Heat-Recovery Premium (free function — needs two TACs)

Deferred to Phase 2: EPBT, water footprint, carbon abatement cost.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.cases.case0 import Case0Result
from src.config import RunConfig
from src.data import TimeSeries


@dataclass(frozen=True)
class KPIBundle:
    tac_usd_per_yr: float
    lcoe_usd_per_mwh_e: float
    lcoc_usd_per_mwh_c: float
    co2_annual_tonnes: float
    co2_per_mwh_kg: float


def compute_kpis_case0(
    result: Case0Result, ts: TimeSeries, cfg: RunConfig
) -> KPIBundle:
    """Compute Case 0 KPIs from a solver result + the time series + config.

    LCOE denominator = IT energy delivered (MWh_e) — the useful work.
    LCOC numerator   = cooling-attributable annualized cost (capex+fom+vom of
                       VCC + the grid energy cost specifically for running VCC).
    LCOC denominator = cooling delivered (MWh_c).
    """
    dt = cfg.base.time.delta_t
    annual_scale = 8760.0 / result.P_IT_MW.shape[0]

    # ---- Energies (annualized) --------------------------------------------
    it_energy_annual_MWh = result.P_IT_MW.sum() * dt * annual_scale
    cool_energy_annual_MWh = result.Q_cool_MWth.sum() * dt * annual_scale

    # ---- LCOE / CO2 intensity -------------------------------------------
    lcoe = result.tac_usd_per_yr / it_energy_annual_MWh
    co2_per_mwh_kg = result.co2_annual_tonnes * 1000.0 / it_energy_annual_MWh

    # ---- LCOC: split grid cost between IT and VCC ------------------------
    grid_cost_cooling_annual = (
        ts.price_import_usd_per_mwh * result.P_VCC_elec_MW * dt
    ).sum() * annual_scale
    cost_cooling_annual = (
        result.capex_annual_usd
        + result.fom_annual_usd
        + result.vom_annual_usd
        + grid_cost_cooling_annual
    )
    lcoc = cost_cooling_annual / cool_energy_annual_MWh

    return KPIBundle(
        tac_usd_per_yr=result.tac_usd_per_yr,
        lcoe_usd_per_mwh_e=lcoe,
        lcoc_usd_per_mwh_c=lcoc,
        co2_annual_tonnes=result.co2_annual_tonnes,
        co2_per_mwh_kg=co2_per_mwh_kg,
    )


def heat_recovery_premium(tac_baseline: float, tac_case: float) -> float:
    """Heat-Recovery Premium (v2.5 §D headline metric).

        Premium = (TAC_baseline - TAC_case) / TAC_baseline

    Positive  → ``case`` is cheaper than the grid-only baseline.
    Zero      → break-even.
    Negative  → ``case`` is more expensive (heat recovery hurts).

    Raises ValueError if ``tac_baseline`` is not strictly positive.
    """
    if tac_baseline <= 0:
        raise ValueError(
            f"tac_baseline must be positive, got {tac_baseline!r}"
        )
    return (tac_baseline - tac_case) / tac_baseline
