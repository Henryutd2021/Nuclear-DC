"""Case 3 — BWRX-300 + main turbine + absorption (no ORC) (v2.5 §B).

Same as Case 2 but without the ORC bottoming cycle. Tests whether the
ORC step actually pays for itself — Case 2 vs Case 3 isolates the
incremental value of the ~$2,800/kWe ORC capex at the system level.
"""

from __future__ import annotations

from typing import Optional

from src.config import RunConfig
from src.data import TimeSeries
from src.milp.builder import build_model
from src.milp.result import NuclearCaseResult, extract_result
from src.milp.solve import solve_model


def solve_case3(
    cfg: RunConfig,
    ts: TimeSeries,
    pue: Optional[float] = None,
    solver_name: str = "gurobi",
) -> NuclearCaseResult:
    if cfg.case.case_id != 3:
        raise ValueError(f"solve_case3 requires case_id=3, got {cfg.case.case_id}")
    model = build_model(cfg, ts, pue=pue)
    solve_model(model, solver_name=solver_name)
    return extract_result(model, cfg, ts)
