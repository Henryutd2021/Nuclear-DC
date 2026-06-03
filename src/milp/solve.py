"""Solver invocation for the Nuclear-DC Pyomo models.

The builder is mostly a continuous LP, but the vapor-compression chiller
is an SOS2 piecewise map of its non-convex part-load COP curve (see
`src/milp/builder.py`), which makes the model a MILP. Gurobi handles both
the LP relaxation and the SOS2 branching efficiently at this size;
per-solve and parallel-orchestration tuning lives in the workstation
memory file `reference_workstation-specs`.
"""

from __future__ import annotations

from typing import Optional

import pyomo.environ as pyo

from src.config import SolverConfig


def solve_model(
    model: pyo.ConcreteModel,
    solver_name: str = "gurobi",
    solver_config: Optional[SolverConfig] = None,
    mip_gap: float = 0.005,
    time_limit: Optional[float] = None,
    quiet: bool = True,
) -> None:
    """Solve ``model`` in-place. Raises if the solver returns non-optimal.

    Args:
        model: a Pyomo ConcreteModel built by :func:`src.milp.builder.build_model`.
        solver_name: Pyomo SolverFactory name. Defaults to ``"gurobi"``.
        solver_config: optional ``SolverConfig`` (from ``cfg.base.solver``)
            whose fields override the positional fallbacks below. Wires
            Threads / Method / Seed / MIPGap / TimeLimit / OutputFlag
            through to Gurobi so the yaml-declared values actually take
            effect.
        mip_gap: optimality gap fallback (used only when ``solver_config``
            is None). LPs ignore this.
        time_limit: optional hard timeout in seconds (fallback only).
        quiet: suppress solver console output.
    """
    solver = pyo.SolverFactory(solver_name)
    if not solver.available(exception_flag=False):
        raise RuntimeError(
            f"Solver {solver_name!r} not available on this system"
        )

    if solver_name in ("gurobi", "gurobi_direct", "gurobi_persistent"):
        opts = solver.options
        if solver_config is not None:
            opts["MIPGap"] = solver_config.mip_gap
            opts["Threads"] = max(0, solver_config.threads)
            opts["Seed"] = solver_config.seed
            opts["Method"] = solver_config.method
            opts["OutputFlag"] = 0 if quiet else 1
            if solver_config.time_limit is not None:
                opts["TimeLimit"] = solver_config.time_limit
        else:
            opts["MIPGap"] = mip_gap
            if time_limit is not None:
                opts["TimeLimit"] = time_limit

    results = solver.solve(model, tee=not quiet)
    term = results.solver.termination_condition
    if term != pyo.TerminationCondition.optimal:
        raise RuntimeError(
            f"Solver terminated with non-optimal condition: {term}"
        )
