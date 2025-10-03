"""Core Pyomo model with variable declarations."""

import pyomo.environ as pyo

from src.io_config import BaseConfig, CaseConfig, CostConfig
from src.io_data import TimeSeriesData, PerformanceData
from src.sets_params import build_sets_and_params


def add_variables(model: pyo.ConcreteModel) -> None:
    """
    Add all decision variables to the model.

    Args:
        model: Pyomo ConcreteModel with sets and parameters already added
    """
    T = model.T
    case_id = pyo.value(model.case_id)
    capacity_opt = model._opt_data.base.optimization.capacity_optimization

    # ========== Electrical power flows (time-indexed, MW) ==========
    model.P_tur_g = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Turbine gross power [MW]"
    )

    model.P_ORC_g = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="ORC gross power [MW]"
    )

    model.P_elc = pyo.Var(
        T,
        domain=pyo.NonNegativeReals,
        bounds=(0, None),
        doc="Electric chiller power consumption [MW]",
    )

    model.P_aux = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Auxiliary loads (pumps, etc.) [MW]"
    )

    # Grid imports/exports (optional)
    model.P_grid_imp = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Grid import [MW]"
    )

    model.P_grid_exp = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Grid export [MW]"
    )

    # ========== Thermal/heat flows (time-indexed, MWth) ==========
    model.Q_rx = pyo.Var(
        T,
        domain=pyo.NonNegativeReals,
        bounds=(0, pyo.value(model.reactor_thermal_max)),
        doc="Reactor thermal output [MWth]",
    )

    model.Q_tur_in = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Heat to turbine [MWth]"
    )

    model.Q_ORC_in = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Heat to ORC [MWth]"
    )

    model.Q_AB_in = pyo.Var(
        T,
        domain=pyo.NonNegativeReals,
        bounds=(0, None),
        doc="Heat to absorption chiller generator [MWth]",
    )

    # ========== Cooling (chilled water) flows (time-indexed, MWth) ==========
    model.Q_chw_AB = pyo.Var(
        T,
        domain=pyo.NonNegativeReals,
        bounds=(0, None),
        doc="Chilled water from absorption chiller [MWth]",
    )

    model.Q_chw_EC = pyo.Var(
        T,
        domain=pyo.NonNegativeReals,
        bounds=(0, None),
        doc="Chilled water from electric chiller [MWth]",
    )

    model.Q_chw_tank_ch = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="TES charge rate [MWth]"
    )

    model.Q_chw_tank_dis = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="TES discharge rate [MWth]"
    )

    model.E_tank = pyo.Var(
        T,
        domain=pyo.NonNegativeReals,
        bounds=(0, pyo.value(model.tes_capacity_max)),
        doc="TES state of charge [MWh_th]",
    )

    # ========== Slack variables for unmet demand (optional, penalized) ==========
    model.P_IT_unmet = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Unmet IT load slack [MW]"
    )

    model.Q_cool_unmet = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Unmet cooling slack [MWth]"
    )

    # ========== Mass flow rates (time-indexed, kg/s) ==========
    model.mdot_steam_total = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 300), doc="Total steam from reactor [kg/s]"
    )
    
    model.mdot_tur = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 300), doc="Steam to turbine [kg/s]"
    )
    
    model.mdot_IHX = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 200), doc="Steam to IHX [kg/s]"
    )
    
    model.mdot_bypass = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 0), doc="Bypass steam (default disabled) [kg/s]"
    )
    
    model.mdot_FV_in = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 200), doc="Two-phase flow to Flash Vessel [kg/s]"
    )
    
    model.mdot_FV_steam = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 150), doc="Steam from Flash Vessel [kg/s]"
    )
    
    model.mdot_FV_liquid = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 150), doc="Liquid from Flash Vessel [kg/s]"
    )
    
    model.mdot_ARC_gen = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 150), doc="Steam to ARC generator [kg/s]"
    )
    
    model.mdot_ORC_wf = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 50), doc="ORC working fluid flow [kg/s]"
    )
    
    model.mdot_chw = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 500), doc="Chilled water circulation [kg/s]"
    )

    # ========== Temperature state points (time-indexed, °C) ==========
    model.T_main_steam = pyo.Var(
        T, domain=pyo.Reals, bounds=(295, 305), initialize=299, doc="Main steam temperature [°C]"
    )
    
    model.T_turb_exhaust = pyo.Var(
        T, domain=pyo.Reals, bounds=(30, 100), initialize=45, doc="Turbine exhaust temperature [°C]"
    )
    
    model.T_IHX_out = pyo.Var(
        T, domain=pyo.Reals, bounds=(260, 280), initialize=270, doc="IHX outlet temperature [°C]"
    )
    
    model.T_FV = pyo.Var(
        T, domain=pyo.Reals, bounds=(175, 185), initialize=180, doc="Flash Vessel temperature [°C]"
    )
    
    model.T_ARC_gen = pyo.Var(
        T, domain=pyo.Reals, bounds=(160, 180), initialize=170, doc="ARC generator temperature [°C]"
    )
    
    model.T_chw_supply = pyo.Var(
        T, domain=pyo.Reals, bounds=(6, 8), initialize=7.2, doc="Chilled water supply temperature [°C]"
    )
    
    model.T_chw_return = pyo.Var(
        T, domain=pyo.Reals, bounds=(28, 36), initialize=32, doc="Chilled water return temperature [°C]"
    )
    
    model.T_ORC_evap = pyo.Var(
        T, domain=pyo.Reals, bounds=(255, 270), initialize=262, doc="ORC evaporator temperature [°C]"
    )
    
    model.T_ORC_exhaust = pyo.Var(
        T, domain=pyo.Reals, bounds=(110, 130), initialize=120, doc="ORC turbine exhaust temperature [°C]"
    )
    
    model.T_ORC_cond = pyo.Var(
        T, domain=pyo.Reals, bounds=(40, 50), initialize=45, doc="ORC condenser temperature [°C]"
    )
    
    model.T_condenser = pyo.Var(
        T, domain=pyo.Reals, bounds=(30, 50), initialize=40, doc="Main condenser temperature [°C]"
    )

    # ========== Pressure state points (time-indexed, MPa) ==========
    model.P_main_steam = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(5.5, 5.9), initialize=5.68, doc="Main steam pressure [MPa]"
    )
    
    model.P_IHX_out = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(4.5, 5.0), initialize=4.82, doc="IHX outlet pressure [MPa]"
    )
    
    model.P_FV = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0.95, 1.05), initialize=1.0, doc="Flash Vessel pressure [MPa]"
    )
    
    model.P_ARC_gen = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0.5, 1.0), initialize=0.7, doc="ARC generator pressure [MPa]"
    )
    
    # ========== Specific enthalpy state points (time-indexed, kJ/kg) ==========
    model.h_main_steam = pyo.Var(
        T, domain=pyo.Reals, bounds=(2500, 2900), initialize=2785, doc="Main steam specific enthalpy [kJ/kg]"
    )
    
    model.h_IHX_out = pyo.Var(
        T, domain=pyo.Reals, bounds=(2500, 2850), initialize=2750, doc="IHX outlet enthalpy [kJ/kg]"
    )
    
    model.h_FV_in = pyo.Var(
        T, domain=pyo.Reals, bounds=(700, 900), initialize=762, doc="Flash Vessel inlet enthalpy [kJ/kg]"
    )
    
    model.h_FV_steam = pyo.Var(
        T, domain=pyo.Reals, bounds=(2500, 2800), initialize=2583, doc="FV steam enthalpy [kJ/kg]"
    )
    
    model.h_FV_liquid = pyo.Var(
        T, domain=pyo.Reals, bounds=(750, 800), initialize=762, doc="FV liquid enthalpy [kJ/kg]"
    )

    # ========== Heat rejection flows (time-indexed, MWth) ==========
    model.Q_cond_main = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="Main condenser heat duty [MWth]"
    )
    
    model.Q_cond_ORC = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="ORC condenser heat duty [MWth]"
    )
    
    model.Q_reject_ARC = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), 
        doc="ARC condenser+absorber heat rejection [MWth]"
    )
    
    model.Q_cond_total = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), 
        doc="Total condenser network heat duty [MWth]"
    )
    
    model.Q_FWH_recovery = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), 
        doc="Feedwater heater heat recovery [MWth]"
    )

    # ========== ORC internal flows ==========
    model.Q_ORC_recup = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="ORC recuperator duty [MWth]"
    )
    
    model.W_ORC_pump = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="ORC pump power [MW]"
    )
    
    model.W_ORC_turb_gross = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, None), doc="ORC turbine gross work [MW]"
    )

    # ========== Flash Vessel quality ==========
    model.x_FV = pyo.Var(
        T, domain=pyo.NonNegativeReals, bounds=(0, 1), doc="Flash Vessel vapor quality (dryness fraction)"
    )

    # ========== Equipment capacities (if co-design mode) ==========
    if capacity_opt:
        # Size as decision variables
        model.Cap_tur = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, pyo.value(model.turbine_capacity_max)),
            doc="Turbine capacity [MW]",
        )
        model.Cap_ORC = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, pyo.value(model.orc_capacity_max)),
            doc="ORC capacity [MW]",
        )
        model.Cap_AB = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, pyo.value(model.absorption_capacity_max)),
            doc="Absorption chiller capacity [MWth]",
        )
        model.Cap_EC = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, pyo.value(model.electric_chiller_capacity_max)),
            doc="Electric chiller capacity [MWth]",
        )
        model.Cap_TES = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, pyo.value(model.tes_capacity_max)),
            doc="TES capacity [MWh_th]",
        )
        model.Cap_IHX = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, 100),
            doc="IHX capacity [MWth]",
        )
        model.Cap_condenser = pyo.Var(
            domain=pyo.NonNegativeReals,
            bounds=(0, 200),
            doc="Condenser capacity [MWth]",
        )
    else:
        # Fixed capacities from config (as parameters)
        model.Cap_tur = pyo.Param(
            initialize=pyo.value(model.turbine_capacity_max), doc="Turbine capacity [MW]"
        )
        model.Cap_ORC = pyo.Param(
            initialize=pyo.value(model.orc_capacity_max), doc="ORC capacity [MW]"
        )
        model.Cap_AB = pyo.Param(
            initialize=pyo.value(model.absorption_capacity_max),
            doc="Absorption chiller capacity [MWth]",
        )
        model.Cap_EC = pyo.Param(
            initialize=pyo.value(model.electric_chiller_capacity_max),
            doc="Electric chiller capacity [MWth]",
        )
        model.Cap_TES = pyo.Param(
            initialize=pyo.value(model.tes_capacity_max), doc="TES capacity [MWh_th]"
        )
        model.Cap_IHX = pyo.Param(initialize=50.0, doc="IHX capacity [MWth]")
        model.Cap_condenser = pyo.Param(initialize=100.0, doc="Condenser capacity [MWth]")


def create_model(
    base_config: BaseConfig,
    case_config: CaseConfig,
    cost_config: CostConfig,
    ts_data: TimeSeriesData,
    perf_data: PerformanceData,
) -> pyo.ConcreteModel:
    """
    Create the core optimization model with sets, parameters, and variables.

    Args:
        base_config: Base configuration
        case_config: Case-specific configuration
        cost_config: Cost parameters
        ts_data: Time-series data
        perf_data: Performance curve data

    Returns:
        Pyomo ConcreteModel ready for constraint and objective attachment
    """
    # Build sets and parameters
    model = build_sets_and_params(base_config, case_config, cost_config, ts_data, perf_data)

    # Add variables
    add_variables(model)

    return model


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves

    print("Testing model_core module...")

    # Test all 3 cases
    for case_id in [1, 2, 3]:
        print(f"\n=== Case {case_id} ===")
        base, case, cost = load_config(case_id=case_id, config_dir="config")
        ts_data = load_time_series(data_dir="data", num_hours=168)
        perf_data = load_performance_curves(perf_dir="data/perf")

        model = create_model(base, case, cost, ts_data, perf_data)

        print(f"Model: {model.name}")
        print(f"Sets: {[s.name for s in model.component_objects(pyo.Set)]}")
        print(f"Vars: {[v.name for v in model.component_objects(pyo.Var)]}")
        print(f"Number of time-indexed variables: {len(model.P_tur_g)}")

        # Check capacity mode
        if model._opt_data.base.optimization.capacity_optimization:
            print("Capacity optimization: ENABLED (Cap_* are Vars)")
        else:
            print("Capacity optimization: DISABLED (Cap_* are fixed)")

    print("\n✅ Model core created successfully for all cases!")

