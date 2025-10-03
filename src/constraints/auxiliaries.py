"""Auxiliary load (pump, fan, control) constraints."""

import pyomo.environ as pyo


def add_auxiliary_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add auxiliary/parasitic load constraints.

    Parasitics include:
    - VFD pump power (cubic law: P ~ ṁ³)
    - ARC solution pumps
    - ORC working fluid pump (already in ORC constraints)
    - Cooling tower fans
    - Control systems
    - Other fixed auxiliaries

    Simplified approach:
    P_aux = k_linear * Q_chw + k_quadratic * Q_chw² + P_base
    
    For VFD pumps, ideally P ~ ṁ³, but we linearize or use PWL approximation.

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """

    # Pump affinity law parameters
    # P_pump = k * (ṁ / ṁ_rated)³ * P_rated
    # Simplified: P_pump ≈ k_cubic * ṁ³ (linearized via PWL or approximation)
    
    # For simplicity, use a quadratic approximation that captures nonlinearity
    # P_pump ≈ k1 * Q + k2 * Q² + P_base
    k_quadratic = 0.0005  # MW/(MWth)² - quadratic coefficient for VFD pump

    def auxiliary_power_rule(m, t):
        """
        Auxiliary power as function of chilled water flow.

        Total CHW thermal flow: Q_chw_AB + Q_chw_EC
        Pump power includes:
        - VFD chilled water circulation pump (nonlinear)
        - ARC solution pumps (proportional to ARC operation)
        - Base loads (controls, fans, etc.)
        
        P_aux = k_linear * Q_chw + k_quadratic * Q_chw² + P_ARC_pumps + P_base
        """
        chw_thermal_flow = m.Q_chw_AB[t] + m.Q_chw_EC[t]
        
        # Linear component (first-order approximation)
        P_linear = m.pump_power_per_flow * chw_thermal_flow
        
        # Quadratic component (captures cubic law trend via approximation)
        P_quadratic = k_quadratic * chw_thermal_flow * chw_thermal_flow
        
        # ARC solution pump power (proportional to ARC generator heat input)
        # Typical: 0.5-1% of ARC generator heat input
        P_ARC_pumps = 0.008 * m.Q_AB_in[t]  # 0.8% of Q_AB_in
        
        # Total auxiliary power
        return m.P_aux[t] == P_linear + P_quadratic + P_ARC_pumps + m.pump_power_base

    model.auxiliary_power = pyo.Constraint(
        model.T, rule=auxiliary_power_rule, doc="Auxiliary/pump power"
    )

    def chw_pump_power_vfd_rule(m, t):
        """
        VFD pump power using affinity law (cubic relationship).
        
        P_pump = k * (Q / Q_rated)³ * P_rated
        
        For better accuracy, could implement PWL approximation.
        For now, captured in quadratic approximation above.
        """
        return pyo.Constraint.Skip  # Captured in auxiliary_power
    
    model.chw_pump_power_vfd = pyo.Constraint(
        model.T, rule=chw_pump_power_vfd_rule, doc="VFD pump affinity law"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing auxiliary constraints...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=24)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = create_model(base, case, cost, ts_data, perf_data)
    add_auxiliary_constraints(model)

    print(f"Auxiliary power constraints: {len(model.auxiliary_power)}")
    print(f"Pump power per flow: {pyo.value(model.pump_power_per_flow)} MW/MWth")
    print(f"Base pump power: {pyo.value(model.pump_power_base)} MW")
    print("✅ Auxiliary constraints added successfully!")

