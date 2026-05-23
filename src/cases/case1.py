"""Case 1 — BWRX-300 + main turbine, no heat recovery (v2.6 §B).

The reactor's full thermal output goes through the main turbine to make
electricity for the data center; cooling is from a VCC chiller exactly
like Case 0. This case quantifies how much value the cascaded extraction
+ absorption in Case 2 adds on top of "just buying the reactor".
"""

from __future__ import annotations

from typing import Optional

from src.config import RunConfig
from src.data import TimeSeries
from src.milp.builder import build_model
from src.milp.result import NuclearCaseResult, extract_result
from src.milp.solve import solve_model


def solve_case1(
    cfg: RunConfig,
    ts: TimeSeries,
    pue: Optional[float] = None,
    solver_name: str = "gurobi",
) -> NuclearCaseResult:
    if cfg.case.case_id != 1:
        raise ValueError(f"solve_case1 requires case_id=1, got {cfg.case.case_id}")
    model = build_model(cfg, ts, pue=pue)
    solve_model(model, solver_name=solver_name)
    return extract_result(model, cfg, ts)
