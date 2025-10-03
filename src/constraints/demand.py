"""Demand balance constraints for IT electricity and cooling."""

import pyomo.environ as pyo


def add_demand_constraints(model: pyo.ConcreteModel) -> None:
    """
    Add IT electricity and cooling demand balance constraints.

    Constraints:
    1. IT electricity balance (supply >= demand)
    2. Cooling (chilled water) balance (supply >= demand)

    Args:
        model: Pyomo ConcreteModel with variables and parameters
    """

    def it_electricity_balance_rule(m, t):
        """
        IT electricity balance at each hour.

        Generation + Grid Import - Grid Export - Chillers - Auxiliaries - Unmet >= IT Load
        """
        supply = m.P_tur_g[t] + m.P_ORC_g[t] + m.P_grid_imp[t]
        consumption = m.P_IT[t] + m.P_elc[t] + m.P_aux[t] + m.P_grid_exp[t]
        slack = m.P_IT_unmet[t]

        return supply + slack >= consumption

    model.IT_electricity_balance = pyo.Constraint(
        model.T, rule=it_electricity_balance_rule, doc="IT electricity balance"
    )

    def cooling_balance_rule(m, t):
        """
        Cooling (chilled water) balance at each hour.

        Chiller Output + TES Discharge - TES Charge + Unmet >= Cooling Demand
        """
        supply = m.Q_chw_AB[t] + m.Q_chw_EC[t] + m.Q_chw_tank_dis[t]
        demand = m.Q_DC_cool[t] + m.Q_chw_tank_ch[t]
        slack = m.Q_cool_unmet[t]

        return supply + slack >= demand

    model.cooling_balance = pyo.Constraint(
        model.T, rule=cooling_balance_rule, doc="Cooling balance"
    )


if __name__ == "__main__":
    from src.io_config import load_config
    from src.io_data import load_time_series, load_performance_curves
    from src.model_core import create_model

    print("Testing demand constraints...")

    base, case, cost = load_config(case_id=1, config_dir="config")
    ts_data = load_time_series(data_dir="data", num_hours=24)
    perf_data = load_performance_curves(perf_dir="data/perf")

    model = create_model(base, case, cost, ts_data, perf_data)
    add_demand_constraints(model)

    print(f"IT electricity balance: {len(model.IT_electricity_balance)} constraints")
    print(f"Cooling balance: {len(model.cooling_balance)} constraints")
    print("✅ Demand constraints added successfully!")

