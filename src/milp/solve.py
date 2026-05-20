"""Solver invocation for the Nuclear-DC Pyomo models."""

from __future__ import annotations

import pyomo.environ as pyo


def solve_model(
    model: pyo.ConcreteModel,
    solver_name: str = "gurobi",
    mip_gap: float = 0.005,
    time_limit: float | None = None,
    quiet: bool = True,
) -> None:
    """Solve ``model`` in-place. Raises if the solver returns non-optimal.

    Args:
        model: a Pyomo ConcreteModel built by :func:`src.milp.builder.build_model`.
        solver_name: Pyomo SolverFactory name. Defaults to ``"gurobi"``.
        mip_gap: optimality gap for MILP solves (LPs ignore this).
        time_limit: optional hard timeout in seconds.
        quiet: suppress solver console output.
    """
    solver = pyo.SolverFactory(solver_name)
    if not solver.available(exception_flag=False):
        raise RuntimeError(
            f"Solver {solver_name!r} not available on this system"
        )

    if solver_name in ("gurobi", "gurobi_direct"):
        solver.options["MIPGap"] = mip_gap
        if time_limit is not None:
            solver.options["TimeLimit"] = time_limit

    results = solver.solve(model, tee=not quiet)
    term = results.solver.termination_condition
    if term != pyo.TerminationCondition.optimal:
        raise RuntimeError(
            f"Solver terminated with non-optimal condition: {term}"
        )
