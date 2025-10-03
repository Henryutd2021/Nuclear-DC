"""Objective function: minimize total annualized cost."""

import pyomo.environ as pyo


def add_objective(model: pyo.ConcreteModel) -> None:
    """
    Add total annualized cost (TAC) objective to the model.

    TAC = Annualized CAPEX + Annual FOM + Annual VOM + Annual Fuel + Grid Costs + Penalties

    Args:
        model: Pyomo ConcreteModel with variables, parameters, and constraints
    """
    capacity_opt = model._opt_data.base.optimization.capacity_optimization

    # ========== CAPEX (annualized) ==========
    if capacity_opt:
        # Capacity decision variables
        capex_annual = (
            model.crf * model.capex_turbine * model.Cap_tur
            + model.crf * model.capex_orc * model.Cap_ORC
            + model.crf * model.capex_absorption * model.Cap_AB
            + model.crf * model.capex_electric_chiller * model.Cap_EC
            + model.crf * model.capex_tes * model.Cap_TES
        )
    else:
        # Fixed capacities
        capex_annual = (
            model.crf * model.capex_turbine * pyo.value(model.Cap_tur)
            + model.crf * model.capex_orc * pyo.value(model.Cap_ORC)
            + model.crf * model.capex_absorption * pyo.value(model.Cap_AB)
            + model.crf * model.capex_electric_chiller * pyo.value(model.Cap_EC)
            + model.crf * model.capex_tes * pyo.value(model.Cap_TES)
        )

    # ========== Fixed O&M (annual) ==========
    if capacity_opt:
        fom_annual = (
            model.fom_turbine * model.Cap_tur
            + model.fom_orc * model.Cap_ORC
            + model.fom_absorption * model.Cap_AB
            + model.fom_electric_chiller * model.Cap_EC
            + model.fom_tes * model.Cap_TES
        )
    else:
        fom_annual = (
            model.fom_turbine * pyo.value(model.Cap_tur)
            + model.fom_orc * pyo.value(model.Cap_ORC)
            + model.fom_absorption * pyo.value(model.Cap_AB)
            + model.fom_electric_chiller * pyo.value(model.Cap_EC)
            + model.fom_tes * pyo.value(model.Cap_TES)
        )

    # ========== Variable O&M (based on energy produced/consumed) ==========
    # Annualize: sum over horizon, then scale to annual
    hours_per_year = 8760.0
    horizon_hours = pyo.value(model.num_hours)
    scaling_factor = hours_per_year / horizon_hours

    vom_turbine_total = sum(
        model.vom_turbine * model.P_tur_g[t] * model.delta_t for t in model.T
    )
    vom_orc_total = sum(model.vom_orc * model.P_ORC_g[t] * model.delta_t for t in model.T)
    vom_absorption_total = sum(
        model.vom_absorption * model.Q_chw_AB[t] * model.delta_t for t in model.T
    )
    vom_electric_chiller_total = sum(
        model.vom_electric_chiller * model.Q_chw_EC[t] * model.delta_t for t in model.T
    )

    vom_annual = (
        vom_turbine_total + vom_orc_total + vom_absorption_total + vom_electric_chiller_total
    ) * scaling_factor

    # ========== Fuel cost (reactor thermal energy consumed) ==========
    fuel_total = sum(model.fuel_cost * model.Q_rx[t] * model.delta_t for t in model.T)
    fuel_annual = fuel_total * scaling_factor

    # ========== Grid energy costs/revenues ==========
    grid_import_cost = sum(
        model.price_import[t] * model.P_grid_imp[t] * model.delta_t for t in model.T
    )
    grid_export_revenue = sum(
        model.price_export[t] * model.P_grid_exp[t] * model.delta_t for t in model.T
    )
    grid_annual = (grid_import_cost - grid_export_revenue) * scaling_factor

    # ========== Penalty costs (should be zero in feasible solutions) ==========
    penalty_it = sum(
        model.penalty_unmet_it * model.P_IT_unmet[t] * model.delta_t for t in model.T
    )
    penalty_cooling = sum(
        model.penalty_unmet_cooling * model.Q_cool_unmet[t] * model.delta_t for t in model.T
    )
    penalty_annual = (penalty_it + penalty_cooling) * scaling_factor

    # ========== Total Annualized Cost ==========
    total_cost = (
        capex_annual + fom_annual + vom_annual + fuel_annual + grid_annual + penalty_annual
    )

    model.objective = pyo.Objective(expr=total_cost, sense=pyo.minimize, doc="Minimize TAC")

    # Store cost components as expressions for post-processing
    model.capex_annual_expr = pyo.Expression(expr=capex_annual)
    model.fom_annual_expr = pyo.Expression(expr=fom_annual)
    model.vom_annual_expr = pyo.Expression(expr=vom_annual)
    model.fuel_annual_expr = pyo.Expression(expr=fuel_annual)
    model.grid_annual_expr = pyo.Expression(expr=grid_annual)
    model.penalty_annual_expr = pyo.Expression(expr=penalty_annual)


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model
    from src.constraints.demand import add_demand_constraints
    from src.constraints.capacity import add_capacity_constraints

    print("Testing objective function...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=24)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = create_model(base, case, cost, ts_data, perf_data)
    add_demand_constraints(model)
    add_capacity_constraints(model)
    add_objective(model)

    print(f"Objective: {model.objective}")
    print(f"Objective sense: minimize")
    print("Cost components available:")
    print("  - capex_annual_expr")
    print("  - fom_annual_expr")
    print("  - vom_annual_expr")
    print("  - fuel_annual_expr")
    print("  - grid_annual_expr")
    print("  - penalty_annual_expr")
    print("✅ Objective function added successfully!")

