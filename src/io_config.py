"""Configuration loading and validation using Pydantic."""

from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class SolverConfig(BaseModel):
    """Gurobi solver settings."""

    name: Literal["gurobi"] = "gurobi"
    mip_gap: float = Field(0.001, ge=0, le=1, description="MIP optimality gap (0.1%)")
    time_limit: Optional[float] = Field(None, gt=0, description="Max solve time in seconds")
    threads: int = Field(-1, description="-1 means use all available")
    log_to_console: bool = True
    log_to_file: bool = True
    seed: int = Field(42, description="Random seed for deterministic results")


class TimeConfig(BaseModel):
    """Time horizon and resolution."""

    num_hours: int = Field(168, gt=0, description="Number of hours in optimization horizon")
    delta_t: float = Field(1.0, gt=0, description="Time step in hours (1.0 = hourly)")


class CaseConfig(BaseModel):
    """Equipment availability and bounds for a specific case."""

    case_id: Literal[1, 2, 3] = Field(description="1=Turbine only, 2=ORC+AB, 3=Turbine+AB")
    turbine_enabled: bool = True
    orc_enabled: bool = False
    absorption_chiller_enabled: bool = False
    electric_chiller_enabled: bool = True
    tes_enabled: bool = True
    grid_import_enabled: bool = Field(False, description="Allow grid electricity imports")
    grid_export_enabled: bool = Field(False, description="Allow grid electricity exports")

    # Equipment capacity bounds (MW or MWth); 0 means disabled
    reactor_thermal_max: float = Field(100.0, gt=0, description="Reactor max thermal output [MWth]")
    turbine_capacity_max: float = Field(40.0, ge=0, description="Turbine max capacity [MW]")
    orc_capacity_max: float = Field(10.0, ge=0, description="ORC max capacity [MW]")
    absorption_capacity_max: float = Field(20.0, ge=0, description="Absorption chiller max [MWth]")
    electric_chiller_capacity_max: float = Field(
        20.0, ge=0, description="Electric chiller max [MWth]"
    )
    tes_capacity_max: float = Field(50.0, ge=0, description="TES max capacity [MWh_th]")

    # Operating constraints
    turbine_min_load_fraction: float = Field(0.3, ge=0, le=1)
    turbine_ramp_rate: Optional[float] = Field(
        None, gt=0, description="Max ramp rate [MW/hour]; None = no limit"
    )
    header_efficiency: float = Field(0.98, gt=0, le=1, description="Steam header efficiency")

    @field_validator("case_id")
    @classmethod
    def validate_case_logic(cls, v: int, info) -> int:
        """Validate case-specific equipment availability."""
        # Note: info.data may not have all fields yet during validation
        return v


class PhysicsConfig(BaseModel):
    """Physical parameters and efficiencies."""

    # TES (Thermal Energy Storage)
    tes_charge_efficiency: float = Field(0.95, gt=0, le=1)
    tes_discharge_efficiency: float = Field(0.95, gt=0, le=1)
    tes_loss_rate_per_hour: float = Field(0.001, ge=0, description="Fractional loss per hour")

    # Chilled water
    chw_supply_temp: float = Field(7.0, description="Chilled water supply temp [°C]")
    chw_return_temp: float = Field(12.0, description="Chilled water return temp [°C]")

    # Pump parasitics (P_pump = a * flow + b)
    pump_power_per_flow: float = Field(0.01, ge=0, description="[MW per MWth flow]")
    pump_power_base: float = Field(0.1, ge=0, description="Base pump power [MW]")

    # PUE for cooling load derivation (if cooling_load.csv missing)
    pue_default: float = Field(1.5, ge=1.0, description="Power Usage Effectiveness")
    cooling_chain_efficiency: float = Field(
        0.9, gt=0, le=1, description="Efficiency to convert PUE to cooling load"
    )


class CostConfig(BaseModel):
    """Cost parameters (all in $/unit)."""

    # Financial
    discount_rate: float = Field(0.05, ge=0, description="Annual discount rate")
    project_lifetime: int = Field(20, gt=0, description="Project lifetime [years]")

    # CAPEX ($/capacity_unit)
    capex_turbine: float = Field(1_000_000, ge=0, description="[$/MW]")
    capex_orc: float = Field(1_500_000, ge=0, description="[$/MW]")
    capex_absorption: float = Field(500_000, ge=0, description="[$/MWth]")
    capex_electric_chiller: float = Field(300_000, ge=0, description="[$/MWth]")
    capex_tes: float = Field(50_000, ge=0, description="[$/MWh_th]")
    capex_multiplier: float = Field(1.3, ge=1.0, description="EPC, contingency, indirect")

    # Fixed O&M ($/capacity_unit/year)
    fom_turbine: float = Field(20_000, ge=0, description="[$/MW/yr]")
    fom_orc: float = Field(30_000, ge=0, description="[$/MW/yr]")
    fom_absorption: float = Field(10_000, ge=0, description="[$/MWth/yr]")
    fom_electric_chiller: float = Field(5_000, ge=0, description="[$/MWth/yr]")
    fom_tes: float = Field(1_000, ge=0, description="[$/MWh_th/yr]")

    # Variable O&M ($/MWh)
    vom_turbine: float = Field(2.0, ge=0, description="[$/MWh_e]")
    vom_orc: float = Field(3.0, ge=0, description="[$/MWh_e]")
    vom_absorption: float = Field(0.5, ge=0, description="[$/MWh_th]")
    vom_electric_chiller: float = Field(1.0, ge=0, description="[$/MWh_th]")

    # Fuel cost
    fuel_cost: float = Field(5.0, ge=0, description="Reactor fuel cost [$/MWh_th]")

    # Grid electricity price ($/MWh; can be time-varying via CSV)
    grid_price_import: float = Field(50.0, ge=0, description="[$/MWh]")
    grid_price_export: float = Field(30.0, ge=0, description="[$/MWh]")

    # Penalty costs (large values; should be zero in feasible solutions)
    penalty_unmet_it: float = Field(10_000, ge=0, description="[$/MWh unmet IT load]")
    penalty_unmet_cooling: float = Field(5_000, ge=0, description="[$/MWh_th unmet cooling]")


class OptimizationConfig(BaseModel):
    """Optimization mode settings."""

    capacity_optimization: bool = Field(
        False, description="True = co-design (size equipment); False = dispatch only"
    )
    enable_ramping: bool = Field(False, description="Enforce turbine ramping constraints")
    enable_unit_commitment: bool = Field(False, description="Add binary on/off variables")


class BaseConfig(BaseModel):
    """Master configuration merging all sub-configs."""

    time: TimeConfig = Field(default_factory=TimeConfig)
    solver: SolverConfig = Field(default_factory=SolverConfig)
    physics: PhysicsConfig = Field(default_factory=PhysicsConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)


def load_yaml(path: Path | str) -> Dict[str, Any]:
    """Load a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge multiple config dicts (later values override earlier)."""
    result: Dict[str, Any] = {}
    for cfg in configs:
        for key, value in cfg.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value
    return result


def load_config(case_id: int, config_dir: Path | str = "config") -> tuple[BaseConfig, CaseConfig, CostConfig]:
    """
    Load and merge configuration files for a specific case.

    Args:
        case_id: 1, 2, or 3
        config_dir: Path to config directory

    Returns:
        (base_config, case_config, cost_config)
    """
    config_dir = Path(config_dir)

    # Load YAMLs
    base_yaml = load_yaml(config_dir / "base.yaml")
    case_yaml = load_yaml(config_dir / f"plant_case{case_id}.yaml")
    cost_yaml = load_yaml(config_dir / "costs.yaml")

    # Validate
    base_config = BaseConfig(**base_yaml)
    case_config = CaseConfig(**case_yaml)
    cost_config = CostConfig(**cost_yaml)

    # Consistency check
    if case_config.case_id != case_id:
        raise ValueError(f"Case ID mismatch: requested {case_id}, config has {case_config.case_id}")

    return base_config, case_config, cost_config


if __name__ == "__main__":
    # Quick test
    print("Configuration schemas loaded successfully.")
    print(f"BaseConfig fields: {list(BaseConfig.model_fields.keys())}")
    print(f"CaseConfig fields: {list(CaseConfig.model_fields.keys())}")
    print(f"CostConfig fields: {list(CostConfig.model_fields.keys())}")

