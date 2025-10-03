"""Equipment capacity constraints."""

import pyomo.environ as pyo


def add_capacity_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add equipment capacity constraints.

    Constraints:
    1. Power/cooling output <= equipment capacity
    2. For disabled equipment, force capacity to zero

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """

    def turbine_capacity_rule(m, t):
        """Turbine power <= capacity."""
        return m.P_tur_g[t] <= m.Cap_tur

    model.turbine_capacity_limit = pyo.Constraint(
        model.T, rule=turbine_capacity_rule, doc="Turbine capacity limit"
    )

    def orc_capacity_rule(m, t):
        """ORC power <= capacity."""
        return m.P_ORC_g[t] <= m.Cap_ORC

    model.orc_capacity_limit = pyo.Constraint(
        model.T, rule=orc_capacity_rule, doc="ORC capacity limit"
    )

    def absorption_capacity_rule(m, t):
        """Absorption chiller cooling <= capacity."""
        return m.Q_chw_AB[t] <= m.Cap_AB

    model.absorption_capacity_limit = pyo.Constraint(
        model.T, rule=absorption_capacity_rule, doc="Absorption capacity limit"
    )

    def electric_chiller_capacity_rule(m, t):
        """Electric chiller cooling <= capacity."""
        return m.Q_chw_EC[t] <= m.Cap_EC

    model.electric_chiller_capacity_limit = pyo.Constraint(
        model.T, rule=electric_chiller_capacity_rule, doc="Electric chiller capacity limit"
    )

    # TES capacity already bounded by variable bounds on E_tank

    # Force disabled equipment capacities to zero
    capacity_opt = model._opt_data.base.optimization.capacity_optimization

    if capacity_opt:
        # If capacity optimization, enforce equipment availability via capacity bounds
        if pyo.value(model.orc_enabled) == 0:
            model.Cap_ORC.fix(0)

        if pyo.value(model.absorption_enabled) == 0:
            model.Cap_AB.fix(0)


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing capacity constraints...")

    for case_id in [1, 2, 3]:
        print(f"\n=== Case {case_id} ===")
        base, case, cost = load_config(case_id=case_id, config_dir="config")
        ts_data = load_time_series(data_dir="data", num_hours=24)
        perf_data = load_performance_curves(perf_dir="data/perf")

        model = create_model(base, case, cost, ts_data, perf_data)
        add_capacity_constraints(model)

        print(f"Turbine capacity limit: {len(model.turbine_capacity_limit)} constraints")
        print(f"Cap_tur: {pyo.value(model.Cap_tur)} MW")
        print(f"Cap_ORC: {pyo.value(model.Cap_ORC)} MW")
        print(f"Cap_AB: {pyo.value(model.Cap_AB)} MWth")

    print("\n✅ Capacity constraints added successfully!")

