"""Piecewise-linear function utilities for Pyomo models using SOS2."""

from typing import List, Tuple

import pyomo.environ as pyo
from pyomo.core.base.block import BlockData


def add_pwl_constraint(
    block: BlockData,
    name: str,
    x_var: pyo.Var,
    y_var: pyo.Var,
    breakpoints_x: List[float],
    breakpoints_y: List[float],
    constraint_type: str = "EQ",
) -> None:
    """
    Add piecewise-linear relationship between x and y using SOS2.

    Creates: y = f(x) where f is defined by piecewise-linear segments.
    Uses lambda variables with SOS2 for convex combination.

    Args:
        block: Pyomo block to add constraints to
        name: Unique name for this PWL constraint set
        x_var: Independent variable (input)
        y_var: Dependent variable (output)
        breakpoints_x: X-coordinates of PWL breakpoints (must be sorted)
        breakpoints_y: Y-coordinates of PWL breakpoints
        constraint_type: "EQ" (y = f(x)), "LE" (y <= f(x)), or "GE" (y >= f(x))

    Example:
        # Turbine heat rate: Q_in = HR(P_out)
        add_pwl_constraint(
            model, "turbine_hr", P_tur, Q_tur_in,
            [0, 10, 20, 30, 40], [0, 28, 56, 84, 112], "EQ"
        )
    """
    # Validate inputs
    if len(breakpoints_x) != len(breakpoints_y):
        raise ValueError("breakpoints_x and breakpoints_y must have same length")

    if len(breakpoints_x) < 2:
        raise ValueError("Need at least 2 breakpoints for PWL")

    if list(breakpoints_x) != sorted(breakpoints_x):
        raise ValueError("breakpoints_x must be sorted in ascending order")

    n_points = len(breakpoints_x)
    point_indices = list(range(n_points))

    # Create lambda variables (convex combination weights)
    lambda_set = pyo.Set(initialize=point_indices, name=f"{name}_lambda_set")
    setattr(block, f"{name}_lambda_set", lambda_set)

    lambda_var = pyo.Var(lambda_set, domain=pyo.NonNegativeReals, bounds=(0, 1), name=f"{name}_lambda")
    setattr(block, f"{name}_lambda", lambda_var)

    # Lambda sum = 1 constraint
    def lambda_sum_rule(b):
        return sum(lambda_var[i] for i in lambda_set) == 1

    lambda_sum_con = pyo.Constraint(rule=lambda_sum_rule, name=f"{name}_lambda_sum")
    setattr(block, f"{name}_lambda_sum", lambda_sum_con)

    # SOS2 constraint (at most 2 adjacent lambdas can be nonzero)
    sos2_con = pyo.SOSConstraint(var=lambda_var, sos=2, name=f"{name}_sos2")
    setattr(block, f"{name}_sos2", sos2_con)

    # X convex combination constraint
    def x_convex_rule(b):
        return x_var == sum(lambda_var[i] * breakpoints_x[i] for i in lambda_set)

    x_convex_con = pyo.Constraint(rule=x_convex_rule, name=f"{name}_x_convex")
    setattr(block, f"{name}_x_convex", x_convex_con)

    # Y convex combination constraint
    def y_convex_rule(b):
        y_expr = sum(lambda_var[i] * breakpoints_y[i] for i in lambda_set)
        if constraint_type == "EQ":
            return y_var == y_expr
        elif constraint_type == "LE":
            return y_var <= y_expr
        elif constraint_type == "GE":
            return y_var >= y_expr
        else:
            raise ValueError(f"constraint_type must be 'EQ', 'LE', or 'GE', got {constraint_type}")

    y_convex_con = pyo.Constraint(rule=y_convex_rule, name=f"{name}_y_convex")
    setattr(block, f"{name}_y_convex", y_convex_con)


def create_pwl_segments(x_data: List[float], y_data: List[float]) -> Tuple[List[float], List[float]]:
    """
    Prepare data for PWL constraint.

    Args:
        x_data: X-coordinates
        y_data: Y-coordinates

    Returns:
        (sorted_x, sorted_y) ready for add_pwl_constraint
    """
    # Sort by x
    sorted_pairs = sorted(zip(x_data, y_data), key=lambda p: p[0])
    sorted_x = [p[0] for p in sorted_pairs]
    sorted_y = [p[1] for p in sorted_pairs]

    return sorted_x, sorted_y


if __name__ == "__main__":
    # Quick test: create a simple PWL model
    import numpy as np

    model = pyo.ConcreteModel()

    # Test: y = x^2 approximated by PWL
    x_pts = [0, 1, 2, 3, 4]
    y_pts = [xi**2 for xi in x_pts]

    model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 4))
    model.y = pyo.Var(domain=pyo.NonNegativeReals)

    add_pwl_constraint(model, "test_pwl", model.x, model.y, x_pts, y_pts, "EQ")

    # Objective: minimize y (should give x=0, y=0)
    model.obj = pyo.Objective(expr=model.y, sense=pyo.minimize)

    # Check model builds
    print("PWL helper test model created successfully.")
    print(f"Components: {list(model.component_map().keys())}")
    print("PWL constraints added: test_pwl_lambda, test_pwl_sos2, test_pwl_x_convex, test_pwl_y_convex")

