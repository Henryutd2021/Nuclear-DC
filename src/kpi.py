"""Headline KPIs for Nuclear-DC (v2.7 — all 8 KPIs from plan §D delivered).

  1. TAC (passthrough)
  2. LCOE ($/MWh_e delivered to IT)
  3. LCOC ($/MWh_c delivered as chilled water)
  4. Heat-Recovery Premium (free function — needs two TACs)
  5. Annual CO2 (passthrough)
  6. Carbon abatement cost ($/tCO2 avoided vs Case 0)
  7. EPBT (years, energy payback time — Lenzen 2008 / IAEA 2018 method)
  8. Water footprint (L/MWh_e — NREL Macknick 2012 consumption factors)

KPIs 6-8 were marked "Deferred to Phase 2" through v2.6; v2.7 closes that
gap so the 8-KPI promise in the §0.5 D table is mechanically backed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.cases.case0 import Case0Result
from src.config import RunConfig
from src.data import TimeSeries

# ---------------------------------------------------------------------------
# Literature factors for KPIs 7-8 (one source of truth, citable in Methods).
# ---------------------------------------------------------------------------
# Embodied primary energy per kWe installed (MWh_e-equivalent), Lenzen 2008
# Table 5 + IAEA 2018 INPRO update; values consistent with a ~0.5 yr EPBT
# at 92% CF for BWR and ~0.2 yr for NGCC.
EMBODIED_ENERGY_MWH_PER_KWE: dict[str, float] = {
    "nuclear_bwr": 4.5,   # BWRX-300 proxy — Lenzen 2008 PWR/BWR midpoint
    "ngcc": 1.0,          # NREL ATB 2024 LCI screening value
}

# Water-consumption factors (L per kWh_e or kWh_c), NREL Macknick 2012.
# "Consumption" not "withdrawal" — once-through cooling withdraws much more
# but returns most of it; cooling-tower consumption is the true footprint.
WATER_L_PER_KWH: dict[str, float] = {
    "nuclear_cooling_tower": 2.54,   # Macknick 2012 median nuclear w/ tower
    "ngcc_cooling_tower":    0.78,   # Macknick 2012 median NGCC w/ tower
    "ercot_grid_blend":      1.42,   # Macknick 2012 ERCOT generation mix
    "vcc_hybrid_cooling":    0.10,   # per MWh_c — VCC tower water for DC duty
}


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


def carbon_abatement_cost_usd_per_tco2(
    tac_baseline_usd_per_yr: float,
    tac_case_usd_per_yr: float,
    co2_baseline_tonnes: float,
    co2_case_tonnes: float,
) -> Optional[float]:
    """KPI #6 — cost per tonne CO2 avoided relative to Case 0.

        $/tCO2_avoided = (TAC_case - TAC_baseline) / (CO2_baseline - CO2_case)

    Sign convention:
      - Numerator > 0  → case is more expensive (typical for nuclear/cogen)
      - Denominator > 0 → case avoids CO2 vs grid-only baseline
      - Positive result → "you pay $X to avoid 1 tCO2" (the policy-readable number)
      - Negative result → case both saves money AND emits more (or both costs more
        AND emits more) — the cost-per-avoided metric is undefined in those
        quadrants, so we return None to flag it rather than print a misleading
        negative dollar figure.

    Returns None if denominator ≤ 0 (no abatement → metric undefined).
    """
    abatement_t = co2_baseline_tonnes - co2_case_tonnes
    if abatement_t <= 0:
        return None
    return (tac_case_usd_per_yr - tac_baseline_usd_per_yr) / abatement_t


def epbt_years(
    installed_mwe: float,
    annual_electric_output_mwh: float,
    technology: str,
) -> Optional[float]:
    """KPI #7 — energy payback time (years) following Lenzen 2008 method.

        EPBT = (embodied_energy_per_kWe × installed_kWe) / annual_output_kWh

    The embodied factor is the cumulative primary-energy demand of plant
    construction + decommissioning, expressed as MWh_e-equivalent per kWe
    installed. ``technology`` keys into ``EMBODIED_ENERGY_MWH_PER_KWE`` —
    only nuclear_bwr and ngcc are populated; pass anything else to get None.
    """
    factor = EMBODIED_ENERGY_MWH_PER_KWE.get(technology)
    if factor is None or annual_electric_output_mwh <= 0:
        return None
    # factor [MWh/kWe] × installed_kWe = total embodied MWh; divide by the
    # annual output MWh to get years. Both sides are MWh, so no extra ×1000.
    embodied_mwh = factor * installed_mwe * 1000.0
    return embodied_mwh / annual_electric_output_mwh


def water_footprint_l_per_mwh(
    it_energy_annual_mwh: float,
    p_turb_net_annual_mwh: float = 0.0,
    p_ngcc_annual_mwh: float = 0.0,
    p_grid_buy_annual_mwh: float = 0.0,
    q_cool_annual_mwh: float = 0.0,
) -> Optional[float]:
    """KPI #8 — water consumption per MWh_e delivered (NREL Macknick 2012).

    Aggregates four water streams and normalises by IT energy delivered:

      L_total = factor_nuclear  × P_turb_net_total
              + factor_ngcc     × P_NGCC_total
              + factor_grid     × P_grid_buy_total
              + factor_vcc      × Q_cool_total
      L_per_MWh = L_total / IT_energy_total

    Exporting nuclear electricity *still consumes water at the tower* even
    when the kWh goes to ERCOT instead of IT, so we charge the full
    P_turb_net rather than the IT-share. Normalising by IT_energy then
    overstates the footprint vs a "delivered-MWh basis" — but this matches
    Macknick's plant-level accounting which is what reviewers will check.
    """
    if it_energy_annual_mwh <= 0:
        return None
    l_total = (
        WATER_L_PER_KWH["nuclear_cooling_tower"] * p_turb_net_annual_mwh * 1000.0
        + WATER_L_PER_KWH["ngcc_cooling_tower"]  * p_ngcc_annual_mwh    * 1000.0
        + WATER_L_PER_KWH["ercot_grid_blend"]    * p_grid_buy_annual_mwh * 1000.0
        + WATER_L_PER_KWH["vcc_hybrid_cooling"]  * q_cool_annual_mwh    * 1000.0
    )
    return l_total / it_energy_annual_mwh
