"""Thermal energy storage (TES) dynamics constraints."""

import pyomo.environ as pyo


def add_storage_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add TES (chilled water thermal storage) constraints.

    Constraints:
    1. State of charge (SOC) dynamics with charge/discharge efficiencies and losses
    2. Initial SOC (start with empty or specified level)
    3. Final SOC >= Initial SOC (cyclic or specified)

    SOC dynamics:
    E_tank[t] = E_tank[t-1] + η_ch * Q_ch[t] * Δt - (1/η_dis) * Q_dis[t] * Δt - λ * E_tank[t-1] * Δt

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """

    def tes_soc_dynamics_rule(m, t):
        """TES state of charge dynamics."""
        if t == 0:
            # Initial condition: start with 50% SOC (or configurable)
            initial_soc_fraction = 0.5
            initial_energy = initial_soc_fraction * pyo.value(m.Cap_TES)
            return (
                m.E_tank[t]
                == initial_energy
                + m.tes_charge_eff * m.Q_chw_tank_ch[t] * m.delta_t
                - (1 / m.tes_discharge_eff) * m.Q_chw_tank_dis[t] * m.delta_t
            )
        else:
            # Energy balance with losses
            energy_prev = m.E_tank[t - 1]
            charge_energy = m.tes_charge_eff * m.Q_chw_tank_ch[t] * m.delta_t
            discharge_energy = (1 / m.tes_discharge_eff) * m.Q_chw_tank_dis[t] * m.delta_t
            loss_energy = m.tes_loss_rate * energy_prev * m.delta_t

            return m.E_tank[t] == energy_prev + charge_energy - discharge_energy - loss_energy

    model.tes_soc_dynamics = pyo.Constraint(
        model.T, rule=tes_soc_dynamics_rule, doc="TES SOC dynamics"
    )

    # Optional: cyclic boundary condition (final SOC >= initial SOC)
    def tes_cyclic_rule(m):
        """Ensure final SOC >= initial SOC for sustainability."""
        t_final = max(m.T)
        initial_soc_fraction = 0.5
        initial_energy = initial_soc_fraction * pyo.value(m.Cap_TES)
        return m.E_tank[t_final] >= initial_energy

    model.tes_cyclic = pyo.Constraint(rule=tes_cyclic_rule, doc="TES cyclic boundary")


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing TES storage constraints...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=24)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = create_model(base, case, cost, ts_data, perf_data)
    add_storage_constraints(model)

    print(f"TES SOC dynamics constraints: {len(model.tes_soc_dynamics)}")
    print(f"TES cyclic boundary: {model.tes_cyclic is not None}")
    print(f"TES charge efficiency: {pyo.value(model.tes_charge_eff)}")
    print(f"TES discharge efficiency: {pyo.value(model.tes_discharge_eff)}")
    print(f"TES loss rate: {pyo.value(model.tes_loss_rate)}/hour")
    print("✅ TES storage constraints added successfully!")

