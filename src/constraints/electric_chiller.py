"""Electric chiller performance constraints."""

import pyomo.environ as pyo


def add_electric_chiller_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add electric chiller constraints.

    Constraints:
    1. Cooling output: Q_chw_EC = COP * P_elc (simplified constant COP or load-dependent)
    2. Capacity limit handled by capacity.py

    For simplicity, we use a fixed COP from the performance curve (average or best-case).
    For more accuracy, could implement PWL COP vs load fraction.

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """
    # Get electric chiller COP data
    ec_cop = model._perf_data.ec_cop

    # Use average COP (simple approach)
    # For more accuracy, implement PWL based on load fraction Q/Cap
    avg_cop = ec_cop["COP"].mean()

    def electric_chiller_cop_rule(m, t):
        """Electric chiller COP: Q_chw_EC = COP * P_elc."""
        return m.Q_chw_EC[t] == avg_cop * m.P_elc[t]

    model.electric_chiller_cop = pyo.Constraint(
        model.T, rule=electric_chiller_cop_rule, doc="Electric chiller COP"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing electric chiller constraints...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=24)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = create_model(base, case, cost, ts_data, perf_data)
    add_electric_chiller_constraints(model)

    print(f"Electric chiller COP constraints: {len(model.electric_chiller_cop)}")
    avg_cop = perf_data.ec_cop["COP"].mean()
    print(f"Average COP used: {avg_cop:.2f}")
    print("✅ Electric chiller constraints added successfully!")

