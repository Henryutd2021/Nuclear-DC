"""Configuration loading for Nuclear-DC v2.5.

Three sources of truth merged into a single ``RunConfig``:

1. ``config/base.yaml``           — runtime knobs (time horizon, solver, physics).
2. ``config/plant_case{N}.yaml``  — per-case equipment toggles + capacities.
3. ``data/economics/financial_parameters.yaml`` — financial constants (WACC, CRF).

Equipment cost/perf parameters (BWRX-300, ORC, absorption, BESS, NGCC) live in
``data/reactor/`` and ``data/equipment/`` and are loaded lazily by ``src.data``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field

CaseId = Literal[0, 1, 2, 3, 4]
_VALID_CASE_IDS: set[int] = {0, 1, 2, 3, 4}


# ---------------------------------------------------------------------------
# config/plant_case{N}.yaml
# ---------------------------------------------------------------------------
class CaseEquipment(BaseModel):
    reactor_enabled: bool = False
    turbine_enabled: bool = False
    orc_enabled: bool = False
    absorption_chiller_enabled: bool = False
    electric_chiller_enabled: bool = False
    tes_enabled: bool = False
    bess_enabled: bool = False
    ngcc_enabled: bool = False
    grid_import_enabled: bool = True
    grid_export_enabled: bool = False


class CaseCapacities(BaseModel):
    model_config = ConfigDict(extra="allow")

    reactor_thermal_capacity_MWth: Optional[float] = None
    turbine_capacity_MWe: Optional[float] = None
    orc_capacity_MWe: Optional[float] = None
    absorption_capacity_MWth: Optional[float] = None
    electric_chiller_capacity_MWth: Optional[float] = None
    tes_capacity_MWh_th: Optional[float] = None
    bess_capacity_MWh: Optional[float] = None
    bess_power_MW: Optional[float] = None
    ngcc_capacity_MWe: Optional[float] = None


class VccConfig(BaseModel):
    cop_baseline: float = Field(gt=1.0)
    cop_houston: float = Field(gt=1.0)
    fixed_om_usd_per_kWth_year: float = Field(ge=0.0)
    variable_om_usd_per_mwh_th: float = Field(ge=0.0)
    capex_usd_per_kWth: float = Field(ge=0.0)
    lifetime_years: int = Field(gt=0)


class CaseConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    case_id: CaseId
    label: str
    equipment: CaseEquipment
    capacities: CaseCapacities
    vcc: Optional[VccConfig] = None


# ---------------------------------------------------------------------------
# config/base.yaml
# ---------------------------------------------------------------------------
class TimeConfig(BaseModel):
    num_hours: int = Field(gt=0)
    delta_t: float = Field(gt=0.0)


class SolverConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Literal["gurobi", "highs", "cbc"]
    mip_gap: float = Field(gt=0.0, lt=1.0)
    time_limit: Optional[float] = None
    threads: int = -1
    log_to_console: bool = True
    log_to_file: bool = True
    seed: int = 42


class PhysicsConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    pue_default: float = Field(1.5, ge=1.0)
    cooling_chain_efficiency: float = Field(0.9, gt=0.0, le=1.0)


class OptimizationConfig(BaseModel):
    model_config = ConfigDict(extra="allow")


class BaseConfig(BaseModel):
    time: TimeConfig
    solver: SolverConfig
    physics: PhysicsConfig
    optimization: OptimizationConfig


# ---------------------------------------------------------------------------
# data/economics/financial_parameters.yaml
# ---------------------------------------------------------------------------
class FinancialParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    WACC_nominal: float = Field(gt=0.0, lt=1.0)
    WACC_real: float = Field(gt=0.0, lt=1.0)
    inflation_rate: float
    project_lifetime_years: int = Field(gt=0)
    capital_recovery_factor: float = Field(gt=0.0, lt=1.0)
    capital_recovery_factor_formula: str
    reactor_physical_life_years: int = Field(gt=0)
    reactor_lcoe_amortization_years: int = Field(gt=0)
    reactor_crf_40yr_at_67: float
    itc_rate_assumed: float
    ptc_usd_per_mwh_assumed: float
    ptc_phaseout_year: int


class RunConfig(BaseModel):
    case: CaseConfig
    base: BaseConfig
    financial: FinancialParams


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open() as f:
        return yaml.safe_load(f) or {}


def load_config(case_id: int, project_root: Union[Path, str]) -> RunConfig:
    """Load and validate the configuration for a specific case.

    Args:
        case_id: One of {0, 1, 2, 3, 4}.
        project_root: Path to the Nuclear-DC repo root.

    Returns:
        A validated ``RunConfig`` bundling case, base, and financial parameters.

    Raises:
        ValueError: if ``case_id`` is not in {0, 1, 2, 3, 4} or the yaml's
            internal ``case_id`` does not match the caller's.
        FileNotFoundError: if the per-case yaml does not exist on disk.
    """
    if case_id not in _VALID_CASE_IDS:
        raise ValueError(
            f"case_id must be one of {sorted(_VALID_CASE_IDS)}, got {case_id!r}"
        )

    project_root = Path(project_root)
    base_path = project_root / "config" / "base.yaml"
    case_path = project_root / "config" / f"plant_case{case_id}.yaml"
    fin_path = project_root / "data" / "economics" / "financial_parameters.yaml"

    base = BaseConfig(**_load_yaml(base_path))
    case = CaseConfig(**_load_yaml(case_path))
    financial_raw = _load_yaml(fin_path)
    financial = FinancialParams(**financial_raw["financial"])

    if case.case_id != case_id:
        raise ValueError(
            f"Case ID mismatch: yaml {case_path} declares case_id={case.case_id}, "
            f"caller requested {case_id}"
        )

    return RunConfig(case=case, base=base, financial=financial)
