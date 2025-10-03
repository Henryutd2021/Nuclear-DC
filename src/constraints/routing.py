"""Heat/steam routing and case-specific equipment availability constraints."""

import pyomo.environ as pyo


def add_routing_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add heat/steam routing constraints and case-specific logic.

    Constraints:
    1. Reactor heat availability
    2. Heat split to turbine + ORC + AB <= available heat (with header losses)
    3. Case-specific equipment enablement (Case 1: no ORC/AB; Case 2: all; Case 3: no ORC)

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """

    def heat_split_balance_rule(m, t):
        """
        Total heat consumed <= reactor output * header efficiency.

        Q_tur_in + Q_ORC_in + Q_AB_in <= η_header * Q_rx
        """
        heat_consumed = m.Q_tur_in[t] + m.Q_ORC_in[t] + m.Q_AB_in[t]
        heat_available = m.header_efficiency * m.Q_rx[t]

        return heat_consumed <= heat_available

    model.heat_split_balance = pyo.Constraint(
        model.T, rule=heat_split_balance_rule, doc="Heat split to equipment"
    )

    # Case-specific equipment constraints
    # If equipment is disabled, force corresponding heat flows and power to zero

    def orc_availability_rule(m, t):
        """If ORC disabled (Case 1, 3), Q_ORC_in = 0."""
        if pyo.value(m.orc_enabled) == 0:
            return m.Q_ORC_in[t] == 0
        else:
            return pyo.Constraint.Skip

    model.orc_availability = pyo.Constraint(
        model.T, rule=orc_availability_rule, doc="ORC availability by case"
    )

    def absorption_availability_rule(m, t):
        """If absorption disabled (Case 1), Q_AB_in = 0."""
        if pyo.value(m.absorption_enabled) == 0:
            return m.Q_AB_in[t] == 0
        else:
            return pyo.Constraint.Skip

    model.absorption_availability = pyo.Constraint(
        model.T, rule=absorption_availability_rule, doc="Absorption availability by case"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing routing constraints...")

    for case_id in [1, 2, 3]:
        print(f"\n=== Case {case_id} ===")
        base, case, cost = load_config(case_id=case_id, config_dir="config")
        ts_data = load_time_series(data_dir="data", num_hours=24)
        perf_data = load_performance_curves(perf_dir="data/perf")

        model = create_model(base, case, cost, ts_data, perf_data)
        add_routing_constraints(model)

        print(f"Heat split balance: {len(model.heat_split_balance)} constraints")
        print(f"ORC enabled: {pyo.value(model.orc_enabled)}")
        print(f"Absorption enabled: {pyo.value(model.absorption_enabled)}")

    print("\n✅ Routing constraints added successfully!")

