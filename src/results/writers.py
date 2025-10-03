"""Results output writers (CSV, JSON)."""

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import pyomo.environ as pyo


def write_dispatch_results(model: pyo.ConcreteModel, output_dir: str = "outputs") -> None:
    """
    Write hourly dispatch results to CSV.

    Args:
        model: Solved Pyomo model
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract time-indexed variables
    data = {
        "hour": list(model.T),
        "P_tur_g_MW": [pyo.value(model.P_tur_g[t]) for t in model.T],
        "P_ORC_g_MW": [pyo.value(model.P_ORC_g[t]) for t in model.T],
        "P_elc_MW": [pyo.value(model.P_elc[t]) for t in model.T],
        "P_aux_MW": [pyo.value(model.P_aux[t]) for t in model.T],
        "Q_rx_MWth": [pyo.value(model.Q_rx[t]) for t in model.T],
        "Q_chw_AB_MWth": [pyo.value(model.Q_chw_AB[t]) for t in model.T],
        "Q_chw_EC_MWth": [pyo.value(model.Q_chw_EC[t]) for t in model.T],
        "E_tank_MWh": [pyo.value(model.E_tank[t]) for t in model.T],
        "P_IT_MW": [pyo.value(model.P_IT[t]) for t in model.T],
        "Q_cool_MWth": [pyo.value(model.Q_DC_cool[t]) for t in model.T],
    }

    df = pd.DataFrame(data)

    case_id = pyo.value(model.case_id)
    output_file = output_path / f"dispatch_case{case_id}.csv"
    df.to_csv(output_file, index=False, float_format="%.4f")

    print(f"\n📊 Dispatch results written to {output_file}")


def write_cost_summary(model: pyo.ConcreteModel, output_dir: str = "outputs") -> Dict[str, Any]:
    """
    Write cost breakdown to JSON.

    Args:
        model: Solved Pyomo model
        output_dir: Output directory

    Returns:
        Cost summary dictionary
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary = {
        "case_id": pyo.value(model.case_id),
        "total_annualized_cost_$_per_year": pyo.value(model.objective),
        "cost_breakdown": {
            "capex_annualized_$_per_year": pyo.value(model.capex_annual_expr),
            "fixed_om_$_per_year": pyo.value(model.fom_annual_expr),
            "variable_om_$_per_year": pyo.value(model.vom_annual_expr),
            "fuel_$_per_year": pyo.value(model.fuel_annual_expr),
            "grid_net_$_per_year": pyo.value(model.grid_annual_expr),
            "penalties_$_per_year": pyo.value(model.penalty_annual_expr),
        },
        "capacities": {
            "turbine_MW": pyo.value(model.Cap_tur),
            "orc_MW": pyo.value(model.Cap_ORC),
            "absorption_MWth": pyo.value(model.Cap_AB),
            "electric_chiller_MWth": pyo.value(model.Cap_EC),
            "tes_MWh": pyo.value(model.Cap_TES),
        },
    }

    case_id = pyo.value(model.case_id)
    output_file = output_path / f"cost_summary_case{case_id}.json"

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"💰 Cost summary written to {output_file}")

    return summary

