"""Case 2 — BWRX-300 + main turbine + cascaded HP extraction + absorption (v2.6 §B).

v2.6 heat-recovery flagship. Main steam (287 °C / 7.17 MPa) enters the HP
turbine and does electrical work first. A mid-pressure tap (5-7 barg,
~160 °C) bleeds part of the flow to drive a double-effect LiBr-H2O
absorption chiller; the rest continues through the LP turbine and
condenser. The Willans-line linearization in src.milp.builder charges
the electricity loss per MWth of extracted heat — cascaded, NOT parallel,
so high-grade steam is no longer wasted on a 6 °C cooling duty.

Versus v2.5: the ORC bottoming cycle is removed (added < 1 pp Premium at
ATB-Mid CAPEX, kills the bottoming-cycle narrative). The crystallization
gate (P1-A) and time-varying COP(T_wb) carry over unchanged.
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
