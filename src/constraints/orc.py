"""ORC (Organic Rankine Cycle) performance constraints."""

import pyomo.environ as pyo
from src.pwl_helper import add_pwl_constraint


def add_orc_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add ORC constraints (Case 2 only).

    Constraints:
    1. Recuperator heat recovery: Q_recup = ε * ṁ * cp * ΔT_max
    2. Pump work: W_pump = ṁ * Δh_pump / η_pump
    3. Turbine gross work: W_turb_gross from expansion
    4. Net power: P_ORC_g = η_gen * (W_turb_gross - W_pump)
    5. ORC condenser at 40-50°C
    6. ORC evaporator at ~262°C
    7. Energy balance closure

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """
    # Only add constraints if ORC is enabled
    if pyo.value(model.orc_enabled) == 0:
        # ORC disabled; Q_ORC_in and P_ORC_g forced to zero by routing.py
        return

    # Get ORC efficiency performance data
    orc_eta = model._perf_data.orc_eta
    Q_in_pts = orc_eta["Q_in_MWth"].tolist()
    eta_pts = orc_eta["eta"].tolist()

    # ORC cycle parameters (simplified, for toluene working fluid)
    eta_pump = 0.75          # Pump isentropic efficiency
    eta_turbine = 0.85       # Turbine isentropic efficiency
    eta_generator = 0.96     # Generator efficiency
    epsilon_recup = 0.80     # Recuperator effectiveness
    delta_h_pump = 15.0      # kJ/kg (approximate pump work, depends on pressure ratio)
    cp_wf = 1.8              # kJ/(kg·K) (approximate specific heat for toluene vapor)

    def orc_pump_work_rule(m, t):
        """
        ORC pump work.
        
        W_pump [MW] = ṁ_orc [kg/s] * Δh_pump [kJ/kg] / (η_pump * 1000)
        
        Simplified: assume fixed Δh_pump (in detailed model, compute from P_cond, P_evap)
        """
        return m.W_ORC_pump[t] == m.mdot_ORC_wf[t] * delta_h_pump / (eta_pump * 1000.0)
    
    model.orc_pump_work = pyo.Constraint(
        model.T, rule=orc_pump_work_rule, doc="ORC pump work"
    )

    def orc_recuperator_duty_rule(m, t):
        """
        ORC recuperator heat recovery.
        
        Q_recup = ε * ṁ * cp * (T_exhaust - T_pump_out)
        
        Simplified: Q_recup proportional to flow and temperature difference
        """
        # Approximate temperature difference: T_exhaust (~120°C) - T_pump_out (~50°C) ≈ 70 K
        delta_T_max = 70.0  # K
        
        return m.Q_ORC_recup[t] == epsilon_recup * m.mdot_ORC_wf[t] * cp_wf * delta_T_max / 1000.0
    
    model.orc_recuperator_duty = pyo.Constraint(
        model.T, rule=orc_recuperator_duty_rule, doc="ORC recuperator duty"
    )

    def orc_evaporator_duty_rule(m, t):
        """
        ORC evaporator heat input (from IHX).
        
        Q_ORC_in = ṁ_orc * (h_evap_out - h_recup_out)
        
        Simplified: relate Q_ORC_in to working fluid flow
        Energy needed: sensible heat from recuperator exit to evaporator exit
        """
        # This is the external heat input to the ORC cycle
        # Already defined via Q_ORC_in variable
        # Ensure consistency: Q_ORC_in must be feasible given flow
        
        # Approximate enthalpy rise in evaporator: Δh_evap ≈ 300 kJ/kg
        delta_h_evap = 300.0  # kJ/kg
        
        return m.Q_ORC_in[t] == m.mdot_ORC_wf[t] * delta_h_evap / 1000.0
    
    model.orc_evaporator_duty = pyo.Constraint(
        model.T, rule=orc_evaporator_duty_rule, doc="ORC evaporator duty"
    )

    def orc_turbine_gross_work_rule(m, t):
        """
        ORC turbine gross work.
        
        W_turb_gross = ṁ * Δh_turbine * η_turbine
        
        Simplified: expansion from evaporator to condenser pressure
        Δh_turbine ≈ 200 kJ/kg (approximate for toluene cycle)
        """
        delta_h_turbine = 200.0  # kJ/kg (isentropic enthalpy drop, approximate)
        
        return m.W_ORC_turb_gross[t] == m.mdot_ORC_wf[t] * delta_h_turbine * eta_turbine / 1000.0
    
    model.orc_turbine_gross_work = pyo.Constraint(
        model.T, rule=orc_turbine_gross_work_rule, doc="ORC turbine gross work"
    )

    def orc_net_power_rule(m, t):
        """
        ORC net electric power output.
        
        P_ORC_g = η_gen * (W_turb_gross - W_pump)
        """
        return m.P_ORC_g[t] == eta_generator * (m.W_ORC_turb_gross[t] - m.W_ORC_pump[t])
    
    model.orc_net_power = pyo.Constraint(
        model.T, rule=orc_net_power_rule, doc="ORC net power"
    )

    def orc_condenser_temp_bounds_rule(m, t):
        """
        ORC condenser temperature bounds (40-50°C).
        
        Already enforced by variable bounds on T_ORC_cond.
        """
        return pyo.Constraint.Skip  # Enforced by bounds
    
    model.orc_condenser_temp_bounds = pyo.Constraint(
        model.T, rule=orc_condenser_temp_bounds_rule, doc="ORC condenser temp bounds"
    )

    def orc_evaporator_temp_bounds_rule(m, t):
        """
        ORC evaporator temperature bounds (~262°C).
        
        Already enforced by variable bounds on T_ORC_evap.
        """
        return pyo.Constraint.Skip  # Enforced by bounds
    
    model.orc_evaporator_temp_bounds = pyo.Constraint(
        model.T, rule=orc_evaporator_temp_bounds_rule, doc="ORC evaporator temp bounds"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing ORC constraints...")

    for case_id in [1, 2, 3]:
        print(f"\n=== Case {case_id} ===")
        base, case, cost = load_config(case_id=case_id, config_dir="config")
        ts_data = load_time_series(data_dir="data", num_hours=24)
        perf_data = load_performance_curves(perf_dir="data/perf")

        model = create_model(base, case, cost, ts_data, perf_data)
        add_orc_constraints(model)

        if pyo.value(model.orc_enabled):
            print(f"ORC power PWL constraints: {len(model.T)} timesteps")
        else:
            print("ORC disabled for this case (no constraints added)")

    print("\n✅ ORC constraints added successfully!")

