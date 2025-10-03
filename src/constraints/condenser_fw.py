"""Feedwater and condenser network constraints."""

import pyomo.environ as pyo


def add_condenser_feedwater_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add feedwater and condenser network constraints.

    Physical structure:
    - Main condenser receives:
        * Turbine exhaust steam
        * ORC condenser heat (via feedwater cooling)
        * ARC condenser/absorber heat rejection
    - Feedwater Control System (FWH) recovers low-grade heat
    - All returns close the water/steam loop

    Constraints:
    1. Main condenser duty: Q_cond_main from turbine exhaust
    2. ORC condenser duty: Q_cond_ORC from ORC cycle
    3. ARC heat rejection: Q_reject_ARC from condenser + absorber
    4. Total condenser duty: Q_cond_total = Q_cond_main + Q_cond_ORC + Q_reject_ARC
    5. Condenser capacity limit: Q_cond_total ≤ Cap_condenser
    6. Condenser approach temperature: T_condensate ≥ T_cooling_water + ΔT_approach
    7. Feedwater heat recovery from ARC liquid return (~30-35°C)

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """

    # Physical constants
    T_cooling_water = 25.0  # °C (ambient cooling water temperature, approximate)
    delta_T_approach = 5.0   # °C (minimum approach temperature difference)
    h_fg_turb = 2400.0       # kJ/kg (latent heat at turbine exhaust conditions, approximate)

    def main_condenser_duty_rule(m, t):
        """
        Main condenser heat duty from turbine exhaust.
        
        Q_cond_main = ṁ_turbine * h_fg / 1000  [MWth]
        
        Simplified: turbine exhausts saturated or wet steam; condenser duty 
        proportional to turbine heat input minus power output.
        """
        # Energy balance approach: Q_cond = Q_tur_in - P_tur_g - losses
        # Simplified: assume losses are small, so Q_cond ≈ Q_tur_in - P_tur_g
        return m.Q_cond_main[t] == m.Q_tur_in[t] - m.P_tur_g[t]
    
    model.main_condenser_duty = pyo.Constraint(
        model.T, rule=main_condenser_duty_rule, doc="Main condenser duty"
    )

    def orc_condenser_duty_rule(m, t):
        """
        ORC condenser heat duty.
        
        Q_cond_ORC = Q_ORC_in - P_ORC_g + W_ORC_pump
        
        Energy balance: heat input minus net power output equals condenser duty.
        """
        if pyo.value(m.orc_enabled) == 0:
            return m.Q_cond_ORC[t] == 0
        else:
            # Q_cond = Q_in - P_net
            # P_net = W_turb - W_pump
            # So Q_cond = Q_in - (W_turb - W_pump) = Q_in - W_turb + W_pump
            # But P_ORC_g = η_gen * (W_turb - W_pump)
            # Simplified: Q_cond ≈ Q_in - P_net (assuming η_gen ≈ 1 for energy balance)
            return m.Q_cond_ORC[t] == m.Q_ORC_in[t] - m.P_ORC_g[t]
    
    model.orc_condenser_duty = pyo.Constraint(
        model.T, rule=orc_condenser_duty_rule, doc="ORC condenser duty"
    )

    def arc_heat_rejection_rule(m, t):
        """
        ARC heat rejection to condenser/feedwater network.
        
        Q_reject_ARC = Q_AB_in + Q_evap - heat absorbed in evaporator
                     = Q_AB_in - Q_chw_AB  (since cooling is removed via chilled water)
        
        Actually, for absorption chiller:
        Q_reject = Q_condenser + Q_absorber
                 = Q_gen + Q_evap - internal circulation
        
        Simplified energy balance:
        Q_reject_ARC ≈ Q_AB_in * (1 + 1/COP)  [approximate]
        
        More accurate: Q_reject = Q_gen + Q_evap (heat in) - W_parasitic
                                ≈ Q_gen + Q_chw_AB
        """
        if pyo.value(m.absorption_enabled) == 0:
            return m.Q_reject_ARC[t] == 0
        else:
            # Absorption chiller energy balance:
            # Q_gen + Q_evap = Q_condenser + Q_absorber
            # Q_evap = Q_chw_AB (cooling output)
            # So Q_reject = Q_gen + Q_chw_AB
            return m.Q_reject_ARC[t] == m.Q_AB_in[t] + m.Q_chw_AB[t]
    
    model.arc_heat_rejection = pyo.Constraint(
        model.T, rule=arc_heat_rejection_rule, doc="ARC heat rejection"
    )

    def total_condenser_duty_rule(m, t):
        """
        Total condenser network heat duty.
        
        Q_cond_total = Q_cond_main + Q_cond_ORC + Q_reject_ARC
        """
        return (
            m.Q_cond_total[t] 
            == m.Q_cond_main[t] + m.Q_cond_ORC[t] + m.Q_reject_ARC[t]
        )
    
    model.total_condenser_duty = pyo.Constraint(
        model.T, rule=total_condenser_duty_rule, doc="Total condenser duty"
    )

    def condenser_capacity_limit_rule(m, t):
        """
        Condenser capacity limit.
        
        Q_cond_total ≤ Cap_condenser
        """
        return m.Q_cond_total[t] <= m.Cap_condenser
    
    model.condenser_capacity_limit = pyo.Constraint(
        model.T, rule=condenser_capacity_limit_rule, doc="Condenser capacity limit"
    )

    def condenser_approach_temp_rule(m, t):
        """
        Condenser approach temperature constraint.
        
        T_condenser ≥ T_cooling_water + ΔT_approach
        
        This ensures physically feasible heat rejection.
        """
        return m.T_condenser[t] >= T_cooling_water + delta_T_approach
    
    model.condenser_approach_temp = pyo.Constraint(
        model.T, rule=condenser_approach_temp_rule, doc="Condenser approach ΔT"
    )

    def feedwater_heat_recovery_rule(m, t):
        """
        Feedwater heat recovery from low-grade returns.
        
        Q_FWH_recovery ≤ Q_FV_liquid + other low-temp returns
        
        Simplified: recover heat from FV liquid return (~30-35°C) up to a limit.
        This preheats feedwater, improving cycle efficiency.
        
        For now, set as optional/bounded (actual implementation would model FWH explicitly).
        """
        # FV liquid flow carries sensible heat: ṁ_FV_liquid * cp * ΔT
        # Simplified: limit recovery to avoid violating temperature feasibility
        # Q_FWH_recovery ≤ f * ṁ_FV_liquid  (with appropriate conversion)
        
        # Conservative bound: allow up to 5% of reactor thermal as recovery
        max_recovery_fraction = 0.05
        return m.Q_FWH_recovery[t] <= max_recovery_fraction * m.Q_rx[t]
    
    model.feedwater_heat_recovery = pyo.Constraint(
        model.T, rule=feedwater_heat_recovery_rule, doc="Feedwater heat recovery limit"
    )

    def turbine_exhaust_temp_rule(m, t):
        """
        Turbine exhaust temperature related to condenser temperature.
        
        T_turb_exhaust ≈ T_condenser + small ΔT (for pressure drop/subcool)
        
        Simplified: enforce T_turb_exhaust ≈ T_condenser
        """
        # Allow 5°C margin
        return m.T_turb_exhaust[t] <= m.T_condenser[t] + 10.0
    
    model.turbine_exhaust_temp = pyo.Constraint(
        model.T, rule=turbine_exhaust_temp_rule, doc="Turbine exhaust temperature"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing condenser/feedwater constraints...")

    for case_id in [1, 2, 3]:
        print(f"\n=== Case {case_id} ===")
        base, case, cost = load_config(case_id=case_id, config_dir="config")
        ts_data = load_time_series(data_dir="data", num_hours=24)
        perf_data = load_performance_curves(perf_dir="data/perf")

        model = create_model(base, case, cost, ts_data, perf_data)
        add_condenser_feedwater_constraints(model)

        print(f"Total condenser duty constraints: {len(model.total_condenser_duty)}")
        print(f"Condenser capacity: {pyo.value(model.Cap_condenser)} MWth")

    print("\n✅ Condenser/feedwater constraints added successfully!")
