"""Case 2 — BWRX-300 + main turbine + ORC + double-effect absorption (v2.5 §B).

Full heat-recovery configuration. The reactor produces main steam; the
main turbine generates electricity from the bulk of it; medium-pressure
extraction (~165 °C) drives a LiBr-H2O double-effect absorption chiller
that supplies the DC chilled water; lower-pressure extraction (~120 °C)
drives an ORC bottoming cycle that scavenges additional electricity. A
small VCC chiller covers absorption outages (P1-A crystallization gate
when Houston wet bulb is too high).

This is the "heat recovery upper bound" reference case.
"""

from __future__ import annotations

from typing import Optional

from src.config import RunConfig
from src.data import TimeSeries
from src.milp.builder import build_model
from src.milp.result import NuclearCaseResult, extract_result
from src.milp.solve import solve_model


def solve_case2(
    cfg: RunConfig,
    ts: TimeSeries,
    pue: Optional[float] = None,
    solver_name: str = "gurobi",
) -> NuclearCaseResult:
    if cfg.case.case_id != 2:
        raise ValueError(f"solve_case2 requires case_id=2, got {cfg.case.case_id}")
    model = build_model(cfg, ts, pue=pue)
    solve_model(model, solver_name=solver_name)
    return extract_result(model, cfg, ts)
