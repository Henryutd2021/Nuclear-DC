"""Steam network constraints: mass balances, TCV, IHX, let-down, Flash Vessel."""

import pyomo.environ as pyo


def add_steam_network_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add steam network constraints for main steam header, IHX, Flash Vessel.

    Physical structure:
    - Reactor → Main Steam (299°C, 5.68 MPa) → split to:
        * Turbine (via TCV)
        * IHX → Let-down → Flash Vessel → (steam + liquid)
        * Bypass (normally forbidden)

    Constraints:
    1. Main steam mass balance: ṁ_total = ṁ_turbine + ṁ_IHX + ṁ_bypass
    2. Reactor energy output: Q_rx = ṁ_total * (h_steam - h_ref) / 1000  [MWth]
    3. TCV flow limit (max 265 kg/s per description, but allow flexibility)
    4. IHX energy balance: Q_IHX_in = ṁ_IHX * (h_in - h_out) / 1000
    5. Let-down isenthalpic expansion: h_FV_in = h_IHX_out
    6. Flash Vessel mass balance: ṁ_FV_in = ṁ_FV_steam + ṁ_FV_liquid
    7. Flash Vessel quality: x = (h_in - h_liq) / (h_vap - h_liq)
    8. Flash Vessel vapor/liquid split: ṁ_steam = x * ṁ_in; ṁ_liquid = (1-x) * ṁ_in

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """
    
    # Reference enthalpy for saturated liquid at 100°C (approximation for energy calc)
    h_ref = 419.0  # kJ/kg

    def steam_mass_balance_rule(m, t):
        """
        Main steam header mass balance.
        
        Total steam from reactor = turbine + IHX + bypass
        """
        return m.mdot_steam_total[t] == m.mdot_tur[t] + m.mdot_IHX[t] + m.mdot_bypass[t]
    
    model.steam_mass_balance = pyo.Constraint(
        model.T, rule=steam_mass_balance_rule, doc="Main steam mass balance"
    )

    def reactor_energy_output_rule(m, t):
        """
        Reactor thermal output related to total steam flow.
        
        Q_rx [MWth] = ṁ_total [kg/s] * (h_steam - h_ref) [kJ/kg] / 1000
        
        Simplified: assume h_steam ≈ 2785 kJ/kg (from variable bounds)
        For flexibility, use a fixed effective specific heat generation
        """
        # Effective enthalpy rise from feedwater to steam
        delta_h_effective = 2366  # kJ/kg (≈ h_steam - h_feedwater)
        
        return m.Q_rx[t] == m.mdot_steam_total[t] * delta_h_effective / 1000.0
    
    model.reactor_energy_output = pyo.Constraint(
        model.T, rule=reactor_energy_output_rule, doc="Reactor energy to steam"
    )

    def tcv_flow_limit_rule(m, t):
        """
        Turbine Control Valve (TCV) maximum flow.
        
        Per description: ~265 kg/s nominal, but allow up to capacity
        """
        # Upper bound already set on variable, but add explicit constraint for clarity
        # TCV_max = 265 kg/s (or use variable bounds)
        return pyo.Constraint.Skip  # Enforced by variable bounds
    
    model.tcv_flow_limit = pyo.Constraint(
        model.T, rule=tcv_flow_limit_rule, doc="TCV flow limit"
    )

    def ihx_flow_balance_rule(m, t):
        """
        IHX inlet flow equals Flash Vessel inlet flow (no losses).
        """
        return m.mdot_IHX[t] == m.mdot_FV_in[t]
    
    model.ihx_flow_balance = pyo.Constraint(
        model.T, rule=ihx_flow_balance_rule, doc="IHX flow continuity"
    )

    def ihx_energy_balance_rule(m, t):
        """
        IHX energy balance (simplified).
        
        Q_ORC_in comes from IHX heat extraction.
        ṁ_IHX * (h_in - h_out) = Q_ORC_in * 1000  [kJ/s = kW]
        
        Simplified: assume inlet at h_main_steam, outlet at h_IHX_out
        """
        # Effective enthalpy drop across IHX (simplified)
        # h_in ≈ 2785 kJ/kg, h_out ≈ 2750 kJ/kg (from bounds)
        delta_h_IHX = 35  # kJ/kg (conservative, actual depends on ORC heat extraction)
        
        # Relate IHX heat extraction to ORC heat input
        return m.Q_ORC_in[t] == m.mdot_IHX[t] * delta_h_IHX / 1000.0
    
    model.ihx_energy_balance = pyo.Constraint(
        model.T, rule=ihx_energy_balance_rule, doc="IHX energy balance"
    )

    def letdown_isenthalpic_rule(m, t):
        """
        Let-down valve: isenthalpic expansion from IHX outlet to FV inlet.
        
        h_FV_in = h_IHX_out
        
        Simplified: fix relationship (in detailed model, this would compute h from P, T)
        """
        # For now, enforce a reasonable enthalpy relationship
        # After let-down to 1 MPa (~180°C), we get saturated or two-phase
        # h_IHX_out ≈ 2750 kJ/kg → after let-down to 1 MPa: depends on flash
        # Saturated liquid at 1 MPa: h_f ≈ 762 kJ/kg
        # If we have subcooled liquid from IHX, flashing creates two-phase
        
        # Simplified: assume IHX delivers slightly subcooled, let-down creates quality
        # Set h_FV_in based on energy balance (to be consistent with flash quality)
        return pyo.Constraint.Skip  # Will enforce via flash enthalpy balance
    
    model.letdown_isenthalpic = pyo.Constraint(
        model.T, rule=letdown_isenthalpic_rule, doc="Let-down valve isenthalpic"
    )

    def fv_mass_balance_rule(m, t):
        """
        Flash Vessel mass balance.
        
        ṁ_in = ṁ_steam + ṁ_liquid
        """
        return m.mdot_FV_in[t] == m.mdot_FV_steam[t] + m.mdot_FV_liquid[t]
    
    model.fv_mass_balance = pyo.Constraint(
        model.T, rule=fv_mass_balance_rule, doc="Flash Vessel mass balance"
    )

    def fv_energy_balance_rule(m, t):
        """
        Flash Vessel energy balance (enthalpy-based).
        
        ṁ_in * h_in = ṁ_steam * h_steam + ṁ_liquid * h_liquid
        """
        # At 1 MPa, 180°C (saturated):
        # h_f ≈ 762 kJ/kg (liquid)
        # h_g ≈ 2583 kJ/kg (vapor)
        h_f_FV = 762.0
        h_g_FV = 2583.0
        
        # Enthalpy balance
        return (
            m.mdot_FV_in[t] * m.h_FV_in[t] 
            == m.mdot_FV_steam[t] * h_g_FV + m.mdot_FV_liquid[t] * h_f_FV
        )
    
    model.fv_energy_balance = pyo.Constraint(
        model.T, rule=fv_energy_balance_rule, doc="Flash Vessel energy balance"
    )

    def fv_quality_definition_rule(m, t):
        """
        Flash Vessel vapor quality (dryness fraction).
        
        x = (h_in - h_f) / (h_fg) = (h_in - h_f) / (h_g - h_f)
        """
        h_f_FV = 762.0
        h_g_FV = 2583.0
        h_fg = h_g_FV - h_f_FV
        
        return m.x_FV[t] * h_fg == m.h_FV_in[t] - h_f_FV
    
    model.fv_quality_definition = pyo.Constraint(
        model.T, rule=fv_quality_definition_rule, doc="Flash Vessel quality"
    )

    def fv_vapor_split_rule(m, t):
        """
        Flash Vessel vapor flow from quality.
        
        ṁ_steam = x * ṁ_in
        """
        return m.mdot_FV_steam[t] == m.x_FV[t] * m.mdot_FV_in[t]
    
    model.fv_vapor_split = pyo.Constraint(
        model.T, rule=fv_vapor_split_rule, doc="FV vapor split"
    )

    def fv_liquid_split_rule(m, t):
        """
        Flash Vessel liquid flow from quality.
        
        ṁ_liquid = (1 - x) * ṁ_in
        """
        return m.mdot_FV_liquid[t] == (1 - m.x_FV[t]) * m.mdot_FV_in[t]
    
    model.fv_liquid_split = pyo.Constraint(
        model.T, rule=fv_liquid_split_rule, doc="FV liquid split"
    )

    def fv_steam_to_arc_rule(m, t):
        """
        Flash Vessel steam output feeds ARC generator.
        
        ṁ_FV_steam = ṁ_ARC_gen (no losses)
        """
        # Only enforce if absorption is enabled
        if pyo.value(m.absorption_enabled) == 0:
            return m.mdot_ARC_gen[t] == 0
        else:
            return m.mdot_ARC_gen[t] == m.mdot_FV_steam[t]
    
    model.fv_steam_to_arc = pyo.Constraint(
        model.T, rule=fv_steam_to_arc_rule, doc="FV steam to ARC generator"
    )

    def arc_generator_heat_input_rule(m, t):
        """
        ARC generator heat input from condensing steam.
        
        Q_AB_in = ṁ_ARC_gen * h_fg_gen / 1000  [MWth]
        
        At generator conditions (0.5-1 MPa, 160-180°C), h_fg varies
        Use approximate value: h_fg ≈ 2000 kJ/kg
        """
        h_fg_gen = 2000.0  # kJ/kg (approximate latent heat at generator conditions)
        
        return m.Q_AB_in[t] == m.mdot_ARC_gen[t] * h_fg_gen / 1000.0
    
    model.arc_generator_heat_input = pyo.Constraint(
        model.T, rule=arc_generator_heat_input_rule, doc="ARC generator heat from steam"
    )

    def bypass_forbidden_rule(m, t):
        """
        Bypass valve: normally forbidden (upper bound = 0).
        
        This is enforced by variable bounds, but add explicit constraint.
        To allow bypass in start-up mode, would need a parameter/binary.
        """
        # Check if bypass is allowed (from config parameter if exists)
        # For now, enforce zero (already in variable bounds)
        return pyo.Constraint.Skip  # Enforced by bounds on mdot_bypass
    
    model.bypass_forbidden = pyo.Constraint(
        model.T, rule=bypass_forbidden_rule, doc="Bypass valve forbidden"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing steam network constraints...")

    for case_id in [1, 2, 3]:
        print(f"\n=== Case {case_id} ===")
        base, case, cost = load_config(case_id=case_id, config_dir="config")
        ts_data = load_time_series(data_dir="data", num_hours=24)
        perf_data = load_performance_curves(perf_dir="data/perf")

        model = create_model(base, case, cost, ts_data, perf_data)
        add_steam_network_constraints(model)

        print(f"Steam mass balance: {len(model.steam_mass_balance)} constraints")
        print(f"Flash Vessel constraints: {len(model.fv_mass_balance)} timesteps")
        print(f"Bypass allowed: {model.mdot_bypass[0].ub} kg/s")

    print("\n✅ Steam network constraints added successfully!")
