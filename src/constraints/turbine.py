"""Turbine performance and operating constraints."""

import pyomo.environ as pyo
from src.pwl_helper import add_pwl_constraint


def add_turbine_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add turbine constraints.

    Constraints:
    1. Heat rate curve (piecewise linear): Q_tur_in = HR(P_tur_g)
    2. Minimum load fraction (if turbine operating)
    3. Ramping limits (optional, if enabled)

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """
    # Get turbine heat rate performance data
    turbine_hr = model._perf_data.turbine_hr
    P_pts = turbine_hr["P_MW"].tolist()
    HR_pts = turbine_hr["HR_MWth_per_MWe"].tolist()

    # For each time period, add PWL constraint for turbine heat rate
    # Q_tur_in[t] = HR(P_tur_g[t]) is implemented as separate PWL per time period
    # However, for efficiency, we create a single set of lambda variables per timestep

    for t in model.T:
        # Q_tur_in = HR * P_tur_g
        # Since HR is heat rate (MWth/MWe), we have Q = HR * P
        # PWL: Q as function of P
        Q_pts = [P_pts[i] * HR_pts[i] for i in range(len(P_pts))]

        add_pwl_constraint(
            model,
            f"turbine_hr_t{t}",
            model.P_tur_g[t],
            model.Q_tur_in[t],
            P_pts,
            Q_pts,
            constraint_type="EQ",
        )

    # Minimum load constraint: if turbine enabled and producing, P >= min_load * Cap
    # Simplified: enforce P_tur_g[t] >= min_frac * Cap_tur OR P_tur_g[t] = 0
    # Without binary variables, we use: if turbine_enabled, allow full range
    # With ramping/UC enabled, would add binary on/off variables here

    def turbine_min_load_rule(m, t):
        """Turbine minimum load (simplified without UC binaries)."""
        # If turbine is running (P > 0), it should be at least min_load_frac * Cap
        # Without binaries, this is hard to enforce strictly; we skip for now
        # In a full UC model, this would be: P >= min_frac * Cap * u_on
        return pyo.Constraint.Skip

    model.turbine_min_load = pyo.Constraint(
        model.T, rule=turbine_min_load_rule, doc="Turbine min load (UC mode)"
    )

    # Ramping constraints (optional)
    enable_ramping = model._opt_data.base.optimization.enable_ramping
    ramp_rate = model._opt_data.case.turbine_ramp_rate

    if enable_ramping and ramp_rate is not None:

        def turbine_ramp_up_rule(m, t):
            if t == 0:
                return pyo.Constraint.Skip
            return m.P_tur_g[t] - m.P_tur_g[t - 1] <= ramp_rate * m.delta_t

        def turbine_ramp_down_rule(m, t):
            if t == 0:
                return pyo.Constraint.Skip
            return m.P_tur_g[t - 1] - m.P_tur_g[t] <= ramp_rate * m.delta_t

        model.turbine_ramp_up = pyo.Constraint(
            model.T, rule=turbine_ramp_up_rule, doc="Turbine ramp up limit"
        )
        model.turbine_ramp_down = pyo.Constraint(
            model.T, rule=turbine_ramp_down_rule, doc="Turbine ramp down limit"
        )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing turbine constraints...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=24)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = create_model(base, case, cost, ts_data, perf_data)
    add_turbine_constraints(model)

    print(f"Turbine heat rate PWL constraints: {len(model.T)} timesteps")
    print("✅ Turbine constraints added successfully!")

