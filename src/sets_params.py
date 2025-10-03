"""Build Pyomo sets and parameters from configuration and data."""

from typing import Dict, Any

import pyomo.environ as pyo

from src.io_config import BaseConfig, CaseConfig, CostConfig
from src.io_data import TimeSeriesData, PerformanceData


class OptimizationData:
    """Container for all model data (sets, parameters)."""

    def __init__(
        self,
        base_config: BaseConfig,
        case_config: CaseConfig,
        cost_config: CostConfig,
        ts_data: TimeSeriesData,
        perf_data: PerformanceData,
    ):
        self.base = base_config
        self.case = case_config
        self.cost = cost_config
        self.ts = ts_data
        self.perf = perf_data

        # Computed attributes
        self.num_hours = ts_data.num_hours
        self.delta_t = base_config.time.delta_t

        # Capital recovery factor for annualization
        r = cost_config.discount_rate
        n = cost_config.project_lifetime
        if r > 0:
            self.crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
        else:
            self.crf = 1.0 / n  # No discounting

    def to_dict(self) -> Dict[str, Any]:
        """Export key parameters as dictionary for inspection."""
        return {
            "num_hours": self.num_hours,
            "delta_t": self.delta_t,
            "crf": self.crf,
            "case_id": self.case.case_id,
            "turbine_enabled": self.case.turbine_enabled,
            "orc_enabled": self.case.orc_enabled,
            "absorption_enabled": self.case.absorption_chiller_enabled,
            "capacity_opt": self.base.optimization.capacity_optimization,
        }


def build_sets(model: pyo.ConcreteModel, data: OptimizationData) -> None:
    """
    Add sets to Pyomo model.

    Args:
        model: Pyomo ConcreteModel
        data: OptimizationData container
    """
    # Time set (hours)
    model.T = pyo.Set(initialize=range(data.num_hours), ordered=True, doc="Time periods (hours)")

    # Equipment sets (for iteration if needed)
    model.EQUIPMENT = pyo.Set(
        initialize=["turbine", "orc", "absorption", "electric_chiller", "tes"],
        doc="Equipment types",
    )


def build_params(model: pyo.ConcreteModel, data: OptimizationData) -> None:
    """
    Add parameters to Pyomo model.

    Args:
        model: Pyomo ConcreteModel
        data: OptimizationData container
    """
    # ========== Time & sizing ==========
    model.delta_t = pyo.Param(initialize=data.delta_t, doc="Time step [hours]")
    model.num_hours = pyo.Param(initialize=data.num_hours, doc="Number of hours")

    # ========== Case configuration ==========
    model.case_id = pyo.Param(initialize=data.case.case_id, doc="Case ID (1/2/3)")
    model.turbine_enabled = pyo.Param(initialize=int(data.case.turbine_enabled), domain=pyo.Binary)
    model.orc_enabled = pyo.Param(initialize=int(data.case.orc_enabled), domain=pyo.Binary)
    model.absorption_enabled = pyo.Param(
        initialize=int(data.case.absorption_chiller_enabled), domain=pyo.Binary
    )
    model.electric_chiller_enabled = pyo.Param(
        initialize=int(data.case.electric_chiller_enabled), domain=pyo.Binary
    )

    # ========== Time-series demands ==========
    it_load_dict = {t: float(data.ts.it_load.iloc[t]) for t in model.T}
    model.P_IT = pyo.Param(model.T, initialize=it_load_dict, doc="IT electric load [MW]")

    cooling_load_dict = {t: float(data.ts.cooling_load.iloc[t]) for t in model.T}
    model.Q_DC_cool = pyo.Param(model.T, initialize=cooling_load_dict, doc="Cooling demand [MWth]")

    # Grid prices (if available)
    if data.ts.grid_price_import is not None:
        price_import_dict = {t: float(data.ts.grid_price_import.iloc[t]) for t in model.T}
        model.price_import = pyo.Param(
            model.T, initialize=price_import_dict, doc="Grid import price [$/MWh]"
        )
    else:
        model.price_import = pyo.Param(
            model.T, initialize=data.cost.grid_price_import, doc="Grid import price [$/MWh]"
        )

    if data.ts.grid_price_export is not None:
        price_export_dict = {t: float(data.ts.grid_price_export.iloc[t]) for t in model.T}
        model.price_export = pyo.Param(
            model.T, initialize=price_export_dict, doc="Grid export price [$/MWh]"
        )
    else:
        model.price_export = pyo.Param(
            model.T, initialize=data.cost.grid_price_export, doc="Grid export price [$/MWh]"
        )

    # ========== Equipment capacities (bounds) ==========
    model.reactor_thermal_max = pyo.Param(
        initialize=data.case.reactor_thermal_max, doc="Reactor max thermal [MWth]"
    )
    model.turbine_capacity_max = pyo.Param(
        initialize=data.case.turbine_capacity_max, doc="Turbine max capacity [MW]"
    )
    model.orc_capacity_max = pyo.Param(
        initialize=data.case.orc_capacity_max, doc="ORC max capacity [MW]"
    )
    model.absorption_capacity_max = pyo.Param(
        initialize=data.case.absorption_capacity_max, doc="Absorption chiller max [MWth]"
    )
    model.electric_chiller_capacity_max = pyo.Param(
        initialize=data.case.electric_chiller_capacity_max, doc="Electric chiller max [MWth]"
    )
    model.tes_capacity_max = pyo.Param(
        initialize=data.case.tes_capacity_max, doc="TES max capacity [MWh_th]"
    )

    # ========== Operating constraints ==========
    model.turbine_min_load_frac = pyo.Param(
        initialize=data.case.turbine_min_load_fraction, doc="Turbine min load fraction"
    )
    model.header_efficiency = pyo.Param(
        initialize=data.case.header_efficiency, doc="Steam header efficiency"
    )

    # ========== Physics parameters ==========
    model.tes_charge_eff = pyo.Param(
        initialize=data.base.physics.tes_charge_efficiency, doc="TES charge efficiency"
    )
    model.tes_discharge_eff = pyo.Param(
        initialize=data.base.physics.tes_discharge_efficiency, doc="TES discharge efficiency"
    )
    model.tes_loss_rate = pyo.Param(
        initialize=data.base.physics.tes_loss_rate_per_hour, doc="TES loss rate per hour"
    )

    model.pump_power_per_flow = pyo.Param(
        initialize=data.base.physics.pump_power_per_flow, doc="Pump power per flow [MW/MWth]"
    )
    model.pump_power_base = pyo.Param(
        initialize=data.base.physics.pump_power_base, doc="Base pump power [MW]"
    )

    # ========== Cost parameters ==========
    model.crf = pyo.Param(initialize=data.crf, doc="Capital recovery factor")

    # CAPEX ($/capacity)
    model.capex_turbine = pyo.Param(
        initialize=data.cost.capex_turbine * data.cost.capex_multiplier, doc="Turbine CAPEX [$/MW]"
    )
    model.capex_orc = pyo.Param(
        initialize=data.cost.capex_orc * data.cost.capex_multiplier, doc="ORC CAPEX [$/MW]"
    )
    model.capex_absorption = pyo.Param(
        initialize=data.cost.capex_absorption * data.cost.capex_multiplier,
        doc="Absorption CAPEX [$/MWth]",
    )
    model.capex_electric_chiller = pyo.Param(
        initialize=data.cost.capex_electric_chiller * data.cost.capex_multiplier,
        doc="Electric chiller CAPEX [$/MWth]",
    )
    model.capex_tes = pyo.Param(
        initialize=data.cost.capex_tes * data.cost.capex_multiplier, doc="TES CAPEX [$/MWh_th]"
    )

    # Fixed O&M ($/capacity/year)
    model.fom_turbine = pyo.Param(initialize=data.cost.fom_turbine, doc="Turbine FOM [$/MW/yr]")
    model.fom_orc = pyo.Param(initialize=data.cost.fom_orc, doc="ORC FOM [$/MW/yr]")
    model.fom_absorption = pyo.Param(
        initialize=data.cost.fom_absorption, doc="Absorption FOM [$/MWth/yr]"
    )
    model.fom_electric_chiller = pyo.Param(
        initialize=data.cost.fom_electric_chiller, doc="Electric chiller FOM [$/MWth/yr]"
    )
    model.fom_tes = pyo.Param(initialize=data.cost.fom_tes, doc="TES FOM [$/MWh_th/yr]")

    # Variable O&M ($/MWh)
    model.vom_turbine = pyo.Param(initialize=data.cost.vom_turbine, doc="Turbine VOM [$/MWh_e]")
    model.vom_orc = pyo.Param(initialize=data.cost.vom_orc, doc="ORC VOM [$/MWh_e]")
    model.vom_absorption = pyo.Param(
        initialize=data.cost.vom_absorption, doc="Absorption VOM [$/MWh_th]"
    )
    model.vom_electric_chiller = pyo.Param(
        initialize=data.cost.vom_electric_chiller, doc="Electric chiller VOM [$/MWh_th]"
    )

    # Fuel cost
    model.fuel_cost = pyo.Param(initialize=data.cost.fuel_cost, doc="Fuel cost [$/MWh_th]")

    # Penalties
    model.penalty_unmet_it = pyo.Param(
        initialize=data.cost.penalty_unmet_it, doc="Penalty for unmet IT [$/MWh]"
    )
    model.penalty_unmet_cooling = pyo.Param(
        initialize=data.cost.penalty_unmet_cooling, doc="Penalty for unmet cooling [$/MWh_th]"
    )

    # ========== Performance curve data (stored as params for access) ==========
    # These will be used by PWL constraints in constraint modules
    # Store as Python attributes on model for easy access
    model._perf_data = data.perf


def build_sets_and_params(
    base_config: BaseConfig,
    case_config: CaseConfig,
    cost_config: CostConfig,
    ts_data: TimeSeriesData,
    perf_data: PerformanceData,
) -> pyo.ConcreteModel:
    """
    Create a Pyomo model with sets and parameters.

    Args:
        base_config: Base configuration
        case_config: Case-specific configuration
        cost_config: Cost parameters
        ts_data: Time-series data
        perf_data: Performance curve data

    Returns:
        Pyomo ConcreteModel with sets and parameters
    """
    model = pyo.ConcreteModel(name=f"Nuclear_DC_Case{case_config.case_id}")

    # Create data container
    data = OptimizationData(base_config, case_config, cost_config, ts_data, perf_data)

    # Store data container for later access
    model._opt_data = data

    # Build sets and params
    build_sets(model, data)
    build_params(model, data)

    return model


if __name__ == "__main__":
    # Quick test
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves

    print("Testing sets_params module...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=168)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = build_sets_and_params(base, case, cost, ts_data, perf_data)

    print(f"Model name: {model.name}")
    print(f"Number of time periods: {len(model.T)}")
    print(f"Case ID: {pyo.value(model.case_id)}")
    print(f"Turbine enabled: {pyo.value(model.turbine_enabled)}")
    print(f"ORC enabled: {pyo.value(model.orc_enabled)}")
    print(f"IT load at t=0: {pyo.value(model.P_IT[0])} MW")
    print(f"Cooling demand at t=0: {pyo.value(model.Q_DC_cool[0])} MWth")
    print(f"CRF: {pyo.value(model.crf):.4f}")
    print("\nSets and parameters loaded successfully!")

