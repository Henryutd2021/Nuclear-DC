"""Results post-processing and KPI calculation."""

import pyomo.environ as pyo


def calculate_kpis(model: pyo.ConcreteModel) -> dict:
    """
    Calculate key performance indicators.

    Args:
        model: Solved Pyomo model

    Returns:
        Dictionary of KPIs
    """
    # Total energy produced/consumed
    total_it_load_MWh = sum(pyo.value(model.P_IT[t]) * pyo.value(model.delta_t) for t in model.T)
    total_cooling_MWh = sum(
        pyo.value(model.Q_DC_cool[t]) * pyo.value(model.delta_t) for t in model.T
    )

    total_turbine_MWh = sum(
        pyo.value(model.P_tur_g[t]) * pyo.value(model.delta_t) for t in model.T
    )
    total_orc_MWh = sum(pyo.value(model.P_ORC_g[t]) * pyo.value(model.delta_t) for t in model.T)

    total_ab_cooling_MWh = sum(
        pyo.value(model.Q_chw_AB[t]) * pyo.value(model.delta_t) for t in model.T
    )
    total_ec_cooling_MWh = sum(
        pyo.value(model.Q_chw_EC[t]) * pyo.value(model.delta_t) for t in model.T
    )

    # Capacity factors
    hours = pyo.value(model.num_hours)
    turbine_cf = total_turbine_MWh / (pyo.value(model.Cap_tur) * hours) if pyo.value(model.Cap_tur) > 0 else 0
    orc_cf = total_orc_MWh / (pyo.value(model.Cap_ORC) * hours) if pyo.value(model.Cap_ORC) > 0 else 0

    # Levelized costs
    tac = pyo.value(model.objective)
    lcoe = tac / (total_turbine_MWh + total_orc_MWh) if (total_turbine_MWh + total_orc_MWh) > 0 else 0
    lcoc = tac / total_cooling_MWh if total_cooling_MWh > 0 else 0

    # TES metrics
    max_tes_soc = max(pyo.value(model.E_tank[t]) for t in model.T)
    avg_tes_soc = sum(pyo.value(model.E_tank[t]) for t in model.T) / len(model.T)

    kpis = {
        "total_annualized_cost_$/yr": tac,
        "lcoe_$/MWh": lcoe,
        "lcoc_$/MWh_th": lcoc,
        "turbine_capacity_factor": turbine_cf,
        "orc_capacity_factor": orc_cf,
        "total_it_load_MWh": total_it_load_MWh,
        "total_cooling_MWh": total_cooling_MWh,
        "absorption_fraction": total_ab_cooling_MWh / total_cooling_MWh if total_cooling_MWh > 0 else 0,
        "electric_chiller_fraction": total_ec_cooling_MWh / total_cooling_MWh if total_cooling_MWh > 0 else 0,
        "tes_max_soc_MWh": max_tes_soc,
        "tes_avg_soc_MWh": avg_tes_soc,
        "tes_utilization": max_tes_soc / pyo.value(model.Cap_TES) if pyo.value(model.Cap_TES) > 0 else 0,
    }

    return kpis


def print_kpis(kpis: dict) -> None:
    """Print KPIs in formatted table."""
    print(f"\n{'='*60}")
    print("KEY PERFORMANCE INDICATORS")
    print(f"{'='*60}")
    print(f"Total Annualized Cost:     ${kpis['total_annualized_cost_$/yr']:,.0f}/year")
    print(f"LCOE (Levelized Cost):     ${kpis['lcoe_$/MWh']:.2f}/MWh")
    print(f"LCOC (Cooling Cost):       ${kpis['lcoc_$/MWh_th']:.2f}/MWh_th")
    print(f"\nCapacity Factors:")
    print(f"  Turbine:                 {kpis['turbine_capacity_factor']*100:.1f}%")
    print(f"  ORC:                     {kpis['orc_capacity_factor']*100:.1f}%")
    print(f"\nCooling Mix:")
    print(f"  Absorption fraction:     {kpis['absorption_fraction']*100:.1f}%")
    print(f"  Electric chiller:        {kpis['electric_chiller_fraction']*100:.1f}%")
    print(f"\nTES Utilization:           {kpis['tes_utilization']*100:.1f}%")
    print(f"  Max SOC:                 {kpis['tes_max_soc_MWh']:.1f} MWh")
    print(f"  Avg SOC:                 {kpis['tes_avg_soc_MWh']:.1f} MWh")

