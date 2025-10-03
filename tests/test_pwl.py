"""Tests for piecewise-linear helper functions."""

import pytest
import pyomo.environ as pyo

from src.pwl_helper import add_pwl_constraint, create_pwl_segments


class TestPWLHelper:
    """Test piecewise-linear constraint generation."""

    def test_create_pwl_segments_sorting(self):
        """Test that PWL segments are sorted correctly."""
        x = [3, 1, 2, 0]
        y = [9, 1, 4, 0]

        sorted_x, sorted_y = create_pwl_segments(x, y)

        assert sorted_x == [0, 1, 2, 3]
        assert sorted_y == [0, 1, 4, 9]

    def test_add_pwl_constraint_builds(self):
        """Test that PWL constraint adds components correctly."""
        model = pyo.ConcreteModel()
        model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 10))
        model.y = pyo.Var(domain=pyo.NonNegativeReals)

        x_pts = [0, 5, 10]
        y_pts = [0, 25, 100]

        add_pwl_constraint(model, "test", model.x, model.y, x_pts, y_pts, "EQ")

        # Check components created
        assert hasattr(model, "test_lambda_set")
        assert hasattr(model, "test_lambda")
        assert hasattr(model, "test_lambda_sum")
        assert hasattr(model, "test_sos2")
        assert hasattr(model, "test_x_convex")
        assert hasattr(model, "test_y_convex")

    def test_pwl_linear_function(self):
        """Test PWL approximation of linear function y = 2x."""
        try:
            solver = pyo.SolverFactory("gurobi")
            if not solver.available():
                pytest.skip("Gurobi not available")
        except Exception:
            pytest.skip("Gurobi not available")

        model = pyo.ConcreteModel()
        model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 10))
        model.y = pyo.Var(domain=pyo.NonNegativeReals)

        # y = 2x represented as PWL
        x_pts = [0, 2, 5, 10]
        y_pts = [0, 4, 10, 20]

        add_pwl_constraint(model, "linear", model.x, model.y, x_pts, y_pts, "EQ")

        # Set x = 3, minimize y
        model.x.fix(3)
        model.obj = pyo.Objective(expr=model.y, sense=pyo.minimize)

        results = solver.solve(model, tee=False)
        assert results.solver.termination_condition == pyo.TerminationCondition.optimal

        # y should be 6 (2*3)
        assert abs(pyo.value(model.y) - 6.0) < 0.01

    def test_pwl_quadratic_approximation(self):
        """Test PWL approximation of quadratic function y = x^2."""
        try:
            solver = pyo.SolverFactory("gurobi")
            if not solver.available():
                pytest.skip("Gurobi not available")
        except Exception:
            pytest.skip("Gurobi not available")

        model = pyo.ConcreteModel()
        model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 4))
        model.y = pyo.Var(domain=pyo.NonNegativeReals)

        # y = x^2 with PWL approximation
        x_pts = [0, 1, 2, 3, 4]
        y_pts = [xi**2 for xi in x_pts]

        add_pwl_constraint(model, "quadratic", model.x, model.y, x_pts, y_pts, "EQ")

        # Set x = 2.5, check y ≈ 6.25
        model.x.fix(2.5)
        model.obj = pyo.Objective(expr=model.y, sense=pyo.minimize)

        results = solver.solve(model, tee=False)
        assert results.solver.termination_condition == pyo.TerminationCondition.optimal

        # PWL approximation: y should be between 4 and 9, close to 6.25
        y_val = pyo.value(model.y)
        assert 6.0 <= y_val <= 6.5  # Linear interpolation gives exactly 6.5

    def test_pwl_constraint_type_le(self):
        """Test PWL with LE constraint (y <= f(x))."""
        try:
            solver = pyo.SolverFactory("gurobi")
            if not solver.available():
                pytest.skip("Gurobi not available")
        except Exception:
            pytest.skip("Gurobi not available")

        model = pyo.ConcreteModel()
        model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 10))
        model.y = pyo.Var(domain=pyo.NonNegativeReals)

        x_pts = [0, 5, 10]
        y_pts = [0, 10, 20]

        # y <= f(x)
        add_pwl_constraint(model, "le_test", model.x, model.y, x_pts, y_pts, "LE")

        # Maximize y with x = 5
        model.x.fix(5)
        model.obj = pyo.Objective(expr=model.y, sense=pyo.maximize)

        results = solver.solve(model, tee=False)
        assert results.solver.termination_condition == pyo.TerminationCondition.optimal

        # y should be at most 10
        assert pyo.value(model.y) <= 10.01

    def test_pwl_validation_errors(self):
        """Test PWL validation catches errors."""
        model = pyo.ConcreteModel()
        model.x = pyo.Var()
        model.y = pyo.Var()

        # Mismatched lengths
        with pytest.raises(ValueError, match="same length"):
            add_pwl_constraint(model, "bad", model.x, model.y, [0, 1], [0, 1, 2], "EQ")

        # Too few points
        with pytest.raises(ValueError, match="at least 2"):
            add_pwl_constraint(model, "bad", model.x, model.y, [0], [0], "EQ")

        # Unsorted x
        with pytest.raises(ValueError, match="sorted"):
            add_pwl_constraint(model, "bad", model.x, model.y, [0, 2, 1], [0, 4, 1], "EQ")

        # Invalid constraint type
        with pytest.raises(ValueError, match="EQ.*LE.*GE"):
            add_pwl_constraint(model, "bad", model.x, model.y, [0, 1], [0, 1], "INVALID")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

