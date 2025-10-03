"""Physics validation checks for energy and mass balances."""

import pyomo.environ as pyo
import pandas as pd
from typing import Dict, List, Tuple


def check_mass_balances(model: pyo.ConcreteModel, tolerance: float = 1e-4) -> Dict[str, List[float]]:
    """
    Check mass balance residuals at each node and timestep.

    Args:
        model: Solved Pyomo model
        tolerance: Relative tolerance for residual (default 1e-4 = 0.01%)

    Returns:
        Dictionary of node names to list of residuals per timestep
    """
    residuals = {}

    for t in model.T:
        # Steam header mass balance
        # ṁ_total = ṁ_turbine + ṁ_IHX + ṁ_bypass
        lhs = pyo.value(model.mdot_steam_total[t])
        rhs = pyo.value(model.mdot_tur[t]) + pyo.value(model.mdot_IHX[t]) + pyo.value(model.mdot_bypass[t])
        residual = abs(lhs - rhs) / (abs(lhs) + 1e-10)  # Relative residual
        
        if "steam_header" not in residuals:
            residuals["steam_header"] = []
        residuals["steam_header"].append(residual)

        # Flash Vessel mass balance
        # ṁ_FV_in = ṁ_FV_steam + ṁ_FV_liquid
        lhs = pyo.value(model.mdot_FV_in[t])
        rhs = pyo.value(model.mdot_FV_steam[t]) + pyo.value(model.mdot_FV_liquid[t])
        residual = abs(lhs - rhs) / (abs(lhs) + 1e-10)
        
        if "flash_vessel" not in residuals:
            residuals["flash_vessel"] = []
        residuals["flash_vessel"].append(residual)

    return residuals


def check_energy_balances(model: pyo.ConcreteModel, tolerance: float = 1e-3) -> Dict[str, List[float]]:
    """
    Check energy balance residuals for each subsystem.

    Args:
        model: Solved Pyomo model
        tolerance: Relative tolerance for residual (default 1e-3 = 0.1%)

    Returns:
        Dictionary of subsystem names to list of residuals per timestep
    """
    residuals = {}

    for t in model.T:
        # Overall system energy balance
        # Q_rx = Q_tur_in + Q_ORC_in + Q_AB_in + losses
        heat_in = pyo.value(model.Q_rx[t])
        heat_consumed = (
            pyo.value(model.Q_tur_in[t]) 
            + pyo.value(model.Q_ORC_in[t]) 
            + pyo.value(model.Q_AB_in[t])
        )
        residual = abs(heat_in - heat_consumed) / (abs(heat_in) + 1e-10)
        
        if "reactor_heat_split" not in residuals:
            residuals["reactor_heat_split"] = []
        residuals["reactor_heat_split"].append(residual)

        # Turbine energy balance
        # Q_tur_in = P_tur_g + Q_cond_main
        lhs = pyo.value(model.Q_tur_in[t])
        rhs = pyo.value(model.P_tur_g[t]) + pyo.value(model.Q_cond_main[t])
        residual = abs(lhs - rhs) / (abs(lhs) + 1e-10)
        
        if "turbine" not in residuals:
            residuals["turbine"] = []
        residuals["turbine"].append(residual)

        # ORC energy balance (if enabled)
        if pyo.value(model.orc_enabled):
            # Q_ORC_in = P_ORC_g + Q_cond_ORC
            lhs = pyo.value(model.Q_ORC_in[t])
            rhs = pyo.value(model.P_ORC_g[t]) + pyo.value(model.Q_cond_ORC[t])
            residual = abs(lhs - rhs) / (abs(lhs) + 1e-10)
            
            if "orc" not in residuals:
                residuals["orc"] = []
            residuals["orc"].append(residual)

        # Absorption chiller energy balance (if enabled)
        if pyo.value(model.absorption_enabled):
            # Q_reject_ARC = Q_AB_in + Q_chw_AB
            lhs = pyo.value(model.Q_reject_ARC[t])
            rhs = pyo.value(model.Q_AB_in[t]) + pyo.value(model.Q_chw_AB[t])
            residual = abs(lhs - rhs) / (abs(lhs) + 1e-10)
            
            if "absorption" not in residuals:
                residuals["absorption"] = []
            residuals["absorption"].append(residual)

        # Condenser network total
        # Q_cond_total = Q_cond_main + Q_cond_ORC + Q_reject_ARC
        lhs = pyo.value(model.Q_cond_total[t])
        rhs = (
            pyo.value(model.Q_cond_main[t]) 
            + pyo.value(model.Q_cond_ORC[t]) 
            + pyo.value(model.Q_reject_ARC[t])
        )
        residual = abs(lhs - rhs) / (abs(lhs) + 1e-10)
        
        if "condenser_total" not in residuals:
            residuals["condenser_total"] = []
        residuals["condenser_total"].append(residual)

    return residuals


def check_temperature_bounds(model: pyo.ConcreteModel) -> Dict[str, Tuple[float, float, bool]]:
    """
    Check if temperature variables are within physical bounds.

    Args:
        model: Solved Pyomo model

    Returns:
        Dictionary of {variable_name: (min_value, max_value, in_bounds)}
    """
    results = {}

    temp_vars = {
        "T_main_steam": (295, 305),
        "T_FV": (175, 185),
        "T_ARC_gen": (160, 180),
        "T_chw_supply": (6, 8),
        "T_chw_return": (28, 36),
        "T_ORC_evap": (255, 270),
        "T_ORC_exhaust": (110, 130),
        "T_ORC_cond": (40, 50),
    }

    for var_name, (lb_expected, ub_expected) in temp_vars.items():
        if hasattr(model, var_name):
            var = getattr(model, var_name)
            values = [pyo.value(var[t]) for t in model.T if pyo.value(var[t]) is not None]
            
            if values:
                min_val = min(values)
                max_val = max(values)
                in_bounds = (min_val >= lb_expected - 0.1) and (max_val <= ub_expected + 0.1)
                results[var_name] = (min_val, max_val, in_bounds)

    return results


def check_pressure_bounds(model: pyo.ConcreteModel) -> Dict[str, Tuple[float, float, bool]]:
    """
    Check if pressure variables are within physical bounds.

    Args:
        model: Solved Pyomo model

    Returns:
        Dictionary of {variable_name: (min_value, max_value, in_bounds)}
    """
    results = {}

    pressure_vars = {
        "P_main_steam": (5.5, 5.9),
        "P_IHX_out": (4.5, 5.0),
        "P_FV": (0.95, 1.05),
        "P_ARC_gen": (0.5, 1.0),
    }

    for var_name, (lb_expected, ub_expected) in pressure_vars.items():
        if hasattr(model, var_name):
            var = getattr(model, var_name)
            values = [pyo.value(var[t]) for t in model.T if pyo.value(var[t]) is not None]
            
            if values:
                min_val = min(values)
                max_val = max(values)
                in_bounds = (min_val >= lb_expected - 0.01) and (max_val <= ub_expected + 0.01)
                results[var_name] = (min_val, max_val, in_bounds)

    return results


def check_demand_satisfaction(model: pyo.ConcreteModel) -> Dict[str, float]:
    """
    Check if IT and cooling demands are satisfied.

    Args:
        model: Solved Pyomo model

    Returns:
        Dictionary with total unmet loads
    """
    total_unmet_it = sum(pyo.value(model.P_IT_unmet[t]) for t in model.T)
    total_unmet_cooling = sum(pyo.value(model.Q_cool_unmet[t]) for t in model.T)

    return {
        "unmet_IT_load_MWh": total_unmet_it * pyo.value(model.delta_t),
        "unmet_cooling_MWh_th": total_unmet_cooling * pyo.value(model.delta_t),
    }


def check_storage_soc(model: pyo.ConcreteModel) -> Dict[str, Tuple[float, float, bool]]:
    """
    Check if storage SOC is within bounds.

    Args:
        model: Solved Pyomo model

    Returns:
        Dictionary with SOC statistics
    """
    soc_values = [pyo.value(model.E_tank[t]) for t in model.T]
    cap_tes = pyo.value(model.Cap_TES)

    min_soc = min(soc_values)
    max_soc = max(soc_values)
    in_bounds = (min_soc >= 0) and (max_soc <= cap_tes + 1e-6)

    return {
        "min_SOC_MWh": min_soc,
        "max_SOC_MWh": max_soc,
        "capacity_MWh": cap_tes,
        "in_bounds": in_bounds,
    }


def run_all_checks(model: pyo.ConcreteModel, verbose: bool = True) -> pd.DataFrame:
    """
    Run all physics validation checks and generate report.

    Args:
        model: Solved Pyomo model
        verbose: Print detailed results

    Returns:
        DataFrame with validation summary
    """
    print("\n" + "="*80)
    print("PHYSICS VALIDATION CHECKS")
    print("="*80)

    # Mass balances
    print("\n1. Mass Balance Residuals:")
    mass_residuals = check_mass_balances(model)
    for node, residuals in mass_residuals.items():
        max_residual = max(residuals)
        avg_residual = sum(residuals) / len(residuals)
        status = "✅ PASS" if max_residual < 1e-4 else "❌ FAIL"
        print(f"   {node:20s}: max={max_residual:.2e}, avg={avg_residual:.2e} {status}")

    # Energy balances
    print("\n2. Energy Balance Residuals:")
    energy_residuals = check_energy_balances(model)
    for subsystem, residuals in energy_residuals.items():
        max_residual = max(residuals)
        avg_residual = sum(residuals) / len(residuals)
        status = "✅ PASS" if max_residual < 1e-3 else "❌ FAIL"
        print(f"   {subsystem:20s}: max={max_residual:.2e}, avg={avg_residual:.2e} {status}")

    # Temperature bounds
    print("\n3. Temperature Bounds:")
    temp_results = check_temperature_bounds(model)
    for var_name, (min_val, max_val, in_bounds) in temp_results.items():
        status = "✅ PASS" if in_bounds else "❌ FAIL"
        print(f"   {var_name:20s}: [{min_val:6.1f}, {max_val:6.1f}] °C {status}")

    # Pressure bounds
    print("\n4. Pressure Bounds:")
    pressure_results = check_pressure_bounds(model)
    for var_name, (min_val, max_val, in_bounds) in pressure_results.items():
        status = "✅ PASS" if in_bounds else "❌ FAIL"
        print(f"   {var_name:20s}: [{min_val:6.2f}, {max_val:6.2f}] MPa {status}")

    # Demand satisfaction
    print("\n5. Demand Satisfaction:")
    demand_results = check_demand_satisfaction(model)
    for key, value in demand_results.items():
        status = "✅ PASS" if value < 1e-6 else "❌ FAIL"
        print(f"   {key:25s}: {value:8.3f} {status}")

    # Storage SOC
    print("\n6. Storage State of Charge:")
    soc_results = check_storage_soc(model)
    status = "✅ PASS" if soc_results["in_bounds"] else "❌ FAIL"
    print(f"   SOC range: [{soc_results['min_SOC_MWh']:.2f}, {soc_results['max_SOC_MWh']:.2f}] MWh_th")
    print(f"   Capacity:  {soc_results['capacity_MWh']:.2f} MWh_th {status}")

    print("\n" + "="*80)

    # Create summary DataFrame
    summary_data = []
    
    for node, residuals in mass_residuals.items():
        summary_data.append({
            "Check": f"Mass Balance: {node}",
            "Max Residual": max(residuals),
            "Avg Residual": sum(residuals) / len(residuals),
            "Pass": max(residuals) < 1e-4,
        })
    
    for subsystem, residuals in energy_residuals.items():
        summary_data.append({
            "Check": f"Energy Balance: {subsystem}",
            "Max Residual": max(residuals),
            "Avg Residual": sum(residuals) / len(residuals),
            "Pass": max(residuals) < 1e-3,
        })

    summary_df = pd.DataFrame(summary_data)
    
    return summary_df


if __name__ == "__main__":
    """Demo run with validation checks."""
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.solve import build_full_model, solve_model

    print("Running physics validation demo...")

    # Test Case 2 (full integrated system)
    case_id = 2
    num_hours = 24

    model = build_full_model(case_id=case_id, num_hours=num_hours)
    results = solve_model(model, solver_name="gurobi", time_limit=300)

    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("\n✅ Model solved successfully! Running physics checks...\n")
        summary_df = run_all_checks(model, verbose=True)
        
        # Save summary
        summary_df.to_csv("outputs/physics_check_summary.csv", index=False)
        print("\n📊 Validation summary saved to: outputs/physics_check_summary.csv")
    else:
        print("\n❌ Model did not solve to optimality. Cannot run physics checks.")
