"""Case 3 — NGCC on-site, off-grid baseline (v2.6 §B, was Case 4 in v2.5).

Plain English: an NGCC plant sized to cover the data center's worst hour
provides 100% of the electricity. A vapor-compression chiller handles
cooling. No grid imports. This is the deployment-realistic non-nuclear
on-site alternative against which Heat-Recovery Premium is benchmarked.

Standalone computation (matches Case 0 style; not part of the Cases 1-2
nuclear MILP):

    P_NGCC(t) = P_IT(t) + P_VCC(t)              [off-grid balance]
    Q_cool(t) = (PUE - 1) * P_IT(t) / eta_chain [v2.6 §F definition]
    P_VCC(t)  = Q_cool(t) / COP_VCC_Houston     [Houston wet-bulb derating]

    Fuel(t) [MMBtu] = P_NGCC(t) * 3.412 / eta_HHV
    Fuel cost(t) = Fuel(t) * (HenryHub_annual_mean + Houston_basis)

CO2 is tracked as both direct combustion (~360 g/kWh_e) and lifecycle
including upstream methane leakage (Alvarez 2018, +60 g/kWh_e equivalent).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.config import RunConfig
from src.data import TimeSeries

_MMBTU_PER_MWh: float = 3.412  # HHV basis conversion


@dataclass(frozen=True)
class Case3NgccResult:
    """Outputs of a Case 3 (NGCC on-site) solve."""

    # Hourly dispatch (length == ts.num_hours)
    P_IT_MW: pd.Series
    Q_cool_MWth: pd.Series
    P_VCC_elec_MW: pd.Series
    P_NGCC_elec_MW: pd.Series
    fuel_consumption_MMBtu_per_h: pd.Series
    fuel_cost_usd_per_h: pd.Series
    direct_emissions_kg_co2_per_h: pd.Series
    upstream_emissions_kg_co2_per_h: pd.Series

    # Scalars
    ngcc_capacity_MWe: float
    vcc_capacity_MWth: float
    pue: float
    delivered_fuel_usd_per_mmbtu: float

    # Annualized
    capex_annual_usd: float
    fom_annual_usd: float
    vom_annual_usd: float
    fuel_annual_usd: float
    carbon_annual_usd: float
    tac_usd_per_yr: float
    co2_direct_annual_tonnes: float
    co2_lifecycle_annual_tonnes: float


def solve_case3(
    cfg: RunConfig,
    ts: TimeSeries,
    pue: Optional[float] = None,
) -> Case3NgccResult:
    """Compute Case 3 NGCC on-site dispatch and TAC.

    Args:
        cfg: ``RunConfig`` loaded for ``case_id=3``.
        ts: Aligned hourly time series (one ERCOT year).
        pue: Override the PUE setpoint (defaults to ``cfg.base.physics.pue_default``).

    Returns:
        ``Case3NgccResult`` with per-hour dispatch + annualized accounting.

    Raises:
        ValueError: missing required config blocks, or any-hour demand
            exceeds installed NGCC or VCC capacity.
    """
    if cfg.case.case_id != 3:
        raise ValueError(f"solve_case3 requires case_id=3, got {cfg.case.case_id}")
    if cfg.case.ngcc is None or cfg.case.vcc is None:
        raise ValueError("Case 3 requires both ngcc and vcc blocks in plant_case3.yaml")

    ngcc = cfg.case.ngcc
    vcc = cfg.case.vcc
    pue_used = float(pue if pue is not None else cfg.base.physics.pue_default)
    eta_chain = cfg.base.physics.cooling_chain_efficiency
    dt = cfg.base.time.delta_t

    # ---- Hourly dispatch (off-grid: NGCC covers everything) ----------------
    P_IT = ts.it_load_MW
    Q_cool = (pue_used - 1.0) * P_IT / eta_chain
    P_VCC = Q_cool / vcc.cop_houston
    P_NGCC = P_IT + P_VCC

    Q_capacity = cfg.case.capacities.electric_chiller_capacity_MWth
    NGCC_capacity = cfg.case.capacities.ngcc_capacity_MWe
    if Q_capacity is None or NGCC_capacity is None:
        raise ValueError(
            "Case 3 requires capacities.electric_chiller_capacity_MWth and "
            "capacities.ngcc_capacity_MWe in plant_case3.yaml"
        )
    if Q_cool.max() > Q_capacity + 1e-6:
        raise ValueError(
            f"VCC capacity {Q_capacity} MWth insufficient for max Q_cool "
            f"{Q_cool.max():.2f} MWth at PUE={pue_used}"
        )
    if P_NGCC.max() > NGCC_capacity + 1e-6:
        raise ValueError(
            f"NGCC capacity {NGCC_capacity} MWe insufficient for max demand "
            f"{P_NGCC.max():.2f} MWe at PUE={pue_used}"
        )

    # ---- Fuel ---------------------------------------------------------------
    # v2.7: drive NGCC fuel cost from the *hourly* HH broadcast (EIA daily
    # ffilled to 24-h blocks) rather than the annual mean. Captures the
    # Jan 2024 cold-snap spike to $13/MMBtu, which the year-mean $2.19
    # silently averaged into Case 3 in v2.6.
    fuel_MMBtu_h = P_NGCC * _MMBTU_PER_MWh / ngcc.net_efficiency_hhv
    delivered_fuel_h = (
        ts.henry_hub_usd_per_mmbtu_hourly + ngcc.henry_hub_basis_usd_per_mmbtu
    )
    fuel_cost_h = fuel_MMBtu_h * delivered_fuel_h
    delivered_fuel_mean = float(delivered_fuel_h.mean())

    # ---- Emissions ----------------------------------------------------------
    direct_kg_h = P_NGCC * dt * ngcc.co2_direct_g_per_kwh_e
    upstream_kg_h = P_NGCC * dt * ngcc.co2_upstream_ch4_g_per_kwh_e

    # ---- Annualization ------------------------------------------------------
    annual_scale = 8760.0 / ts.num_hours
    crf = cfg.financial.capital_recovery_factor

    capex_annual = (
        ngcc.capex_usd_per_kWe * NGCC_capacity * 1000.0 * crf
        + vcc.capex_usd_per_kWth * Q_capacity * 1000.0 * crf
    )
    fom_annual = (
        ngcc.fixed_om_usd_per_kWe_year * NGCC_capacity * 1000.0
        + vcc.fixed_om_usd_per_kWth_year * Q_capacity * 1000.0
    )
    vom_annual = (
        ngcc.variable_om_usd_per_mwh_e * P_NGCC.sum() * dt * annual_scale
        + vcc.variable_om_usd_per_mwh_th * Q_cool.sum() * dt * annual_scale
    )
    fuel_annual = fuel_cost_h.sum() * annual_scale

    co2_direct_annual_tonnes = direct_kg_h.sum() * annual_scale / 1000.0
    co2_lifecycle_annual_tonnes = (
        (direct_kg_h + upstream_kg_h).sum() * annual_scale / 1000.0
    )

    # v2.7 §S6: carbon cost applied to lifecycle (direct + upstream methane)
    # emissions. Lifecycle is the policy-relevant denominator because CBAM,
    # EU ETS Scope 1+3, and most US state programs price upstream leakage.
    carbon_price = cfg.base.physics.carbon_price_usd_per_tco2
    carbon_annual = carbon_price * co2_lifecycle_annual_tonnes

    tac = capex_annual + fom_annual + vom_annual + fuel_annual + carbon_annual

    return Case3NgccResult(
        P_IT_MW=P_IT,
        Q_cool_MWth=Q_cool,
        P_VCC_elec_MW=P_VCC,
        P_NGCC_elec_MW=P_NGCC,
        fuel_consumption_MMBtu_per_h=fuel_MMBtu_h,
        fuel_cost_usd_per_h=fuel_cost_h,
        direct_emissions_kg_co2_per_h=direct_kg_h,
        upstream_emissions_kg_co2_per_h=upstream_kg_h,
        ngcc_capacity_MWe=NGCC_capacity,
        vcc_capacity_MWth=Q_capacity,
        pue=pue_used,
        delivered_fuel_usd_per_mmbtu=delivered_fuel_mean,
        capex_annual_usd=capex_annual,
        fom_annual_usd=fom_annual,
        vom_annual_usd=vom_annual,
        fuel_annual_usd=fuel_annual,
        carbon_annual_usd=carbon_annual,
        tac_usd_per_yr=tac,
        co2_direct_annual_tonnes=co2_direct_annual_tonnes,
        co2_lifecycle_annual_tonnes=co2_lifecycle_annual_tonnes,
    )
