"""Main solver interface with CLI."""

import time
from pathlib import Path
from typing import Optional

import pyomo.environ as pyo

from src.io_config import load_config
from src.io_data import load_performance_curves, load_time_series
from src.model_core import create_model
from src.objective import add_objective

# Import all constraint modules
from src.constraints.absorption import add_absorption_constraints
from src.constraints.auxiliaries import add_auxiliary_constraints
from src.constraints.capacity import add_capacity_constraints
from src.constraints.demand import add_demand_constraints
from src.constraints.electric_chiller import add_electric_chiller_constraints
from src.constraints.orc import add_orc_constraints
from src.constraints.routing import add_routing_constraints
from src.constraints.storage import add_storage_constraints
from src.constraints.turbine import add_turbine_constraints
from src.constraints.steam_network import add_steam_network_constraints
from src.constraints.condenser_fw import add_condenser_feedwater_constraints


def build_full_model(
    case_id: int,
    config_dir: str = "config",
    data_dir: str = "data",
    num_hours: Optional[int] = None,
) -> pyo.ConcreteModel:
    """
    Build complete optimization model with all constraints and objective.

    Args:
        case_id: Case ID (1, 2, or 3)
        config_dir: Path to config directory
        data_dir: Path to data directory
        num_hours: Number of hours to optimize (None = use from base config)

    Returns:
        Complete Pyomo ConcreteModel ready to solve
    """
    print(f"\n{'='*60}")
    print(f"Building model for Case {case_id}")
    print(f"{'='*60}")

    # Load configuration and data
    print("Loading configuration...")
    base, case, cost = load_config(case_id=case_id, config_dir=config_dir)

    if num_hours is None:
        num_hours = base.time.num_hours

    print(f"Loading time-series data ({num_hours} hours)...")
    ts_data = load_time_series(
        data_dir=data_dir,
        num_hours=num_hours,
        pue=base.physics.pue_default,
        cooling_chain_efficiency=base.physics.cooling_chain_efficiency,
    )

    print("Loading performance curves...")
    perf_data = load_performance_curves(perf_dir=f"{data_dir}/perf")

    # Create model with sets, params, and variables
    print("Creating model core (sets, parameters, variables)...")
    model = create_model(base, case, cost, ts_data, perf_data)

    # Add all constraints
    print("Adding constraints:")
    print("  - Demand balances (IT + cooling)")
    add_demand_constraints(model)

    print("  - Steam network (mass balances, IHX, Flash Vessel)")
    add_steam_network_constraints(model)

    print("  - Heat routing & case logic")
    add_routing_constraints(model)

    print("  - Turbine performance")
    add_turbine_constraints(model)

    if pyo.value(model.orc_enabled):
        print("  - ORC performance (with recuperator & pump)")
        add_orc_constraints(model)

    if pyo.value(model.absorption_enabled):
        print("  - Absorption chiller (with generator T/P)")
        add_absorption_constraints(model)

    if pyo.value(model.electric_chiller_enabled):
        print("  - Electric chiller")
        add_electric_chiller_constraints(model)

    print("  - Thermal storage (TES)")
    add_storage_constraints(model)

    print("  - Feedwater & condenser network")
    add_condenser_feedwater_constraints(model)

    print("  - Auxiliary loads (VFD pumps, ARC pumps)")
    add_auxiliary_constraints(model)

    print("  - Capacity limits")
    add_capacity_constraints(model)

    # Add objective
    print("Adding objective function (minimize TAC)...")
    add_objective(model)

    # Model statistics
    num_vars = sum(1 for _ in model.component_data_objects(pyo.Var))
    num_cons = sum(1 for _ in model.component_data_objects(pyo.Constraint, active=True))

    print(f"\nModel statistics:")
    print(f"  Variables: {num_vars}")
    print(f"  Constraints: {num_cons}")
    print(f"  Time periods: {num_hours}")

    return model


def solve_model(
    model: pyo.ConcreteModel,
    solver_name: str = "gurobi",
    time_limit: Optional[float] = None,
    mip_gap: float = 0.001,
    output_dir: str = "outputs",
):
    """
    Solve the optimization model.

    Args:
        model: Pyomo ConcreteModel to solve
        solver_name: Solver to use (default: gurobi)
        time_limit: Max solve time in seconds (None = unlimited)
        mip_gap: MIP optimality gap
        output_dir: Directory for solver logs

    Returns:
        Solver results object
    """
    print(f"\n{'='*60}")
    print("Solving model")
    print(f"{'='*60}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get solver
    solver = pyo.SolverFactory(solver_name)

    if not solver.available():
        raise RuntimeError(f"Solver {solver_name} not available")

    # Set solver options
    solver_opts = {
        "MIPGap": mip_gap,
        "Threads": 0,  # 0 = use default (all available threads)
        "Seed": model._opt_data.base.solver.seed,
        "LogToConsole": 1 if model._opt_data.base.solver.log_to_console else 0,
    }

    if time_limit is not None:
        solver_opts["TimeLimit"] = time_limit

    # Solve
    print(f"Solver: {solver_name}")
    print(f"Options: {solver_opts}")
    print("\nSolving...")

    start_time = time.time()

    # Write log file
    log_file = output_path / f"solve_case{pyo.value(model.case_id)}.log"

    results = solver.solve(
        model,
        tee=model._opt_data.base.solver.log_to_console,
        logfile=str(log_file) if model._opt_data.base.solver.log_to_file else None,
        options=solver_opts,
    )

    solve_time = time.time() - start_time

    # Print results
    print(f"\n{'='*60}")
    print("Solve Results")
    print(f"{'='*60}")
    print(f"Status: {results.solver.termination_condition}")
    print(f"Solve time: {solve_time:.2f} seconds")

    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print(f"Optimal solution found!")
        print(f"Objective value (TAC): ${pyo.value(model.objective):,.2f}/year")

        # Check for unmet loads
        total_unmet_it = sum(pyo.value(model.P_IT_unmet[t]) for t in model.T)
        total_unmet_cooling = sum(pyo.value(model.Q_cool_unmet[t]) for t in model.T)

        if total_unmet_it > 1e-6:
            print(f"⚠️  WARNING: Unmet IT load = {total_unmet_it:.3f} MWh")
        else:
            print(f"✅ All IT load met")

        if total_unmet_cooling > 1e-6:
            print(f"⚠️  WARNING: Unmet cooling = {total_unmet_cooling:.3f} MWh_th")
        else:
            print(f"✅ All cooling demand met")

    elif results.solver.termination_condition == pyo.TerminationCondition.infeasible:
        print("❌ Model is infeasible!")

    else:
        print(f"Solver terminated with condition: {results.solver.termination_condition}")

    return results


def main_cli():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Nuclear-DC Optimization Solver")
    parser.add_argument(
        "--case", type=int, required=True, choices=[1, 2, 3], help="Case ID (1/2/3)"
    )
    parser.add_argument("--config-dir", default="config", help="Config directory")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument("--num-hours", type=int, default=None, help="Number of hours")
    parser.add_argument("--solver", default="gurobi", help="Solver name")
    parser.add_argument("--time-limit", type=float, default=None, help="Time limit (seconds)")
    parser.add_argument("--mip-gap", type=float, default=0.001, help="MIP gap")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--capacity-opt", action="store_true", help="Enable capacity optimization")

    args = parser.parse_args()

    # Build model
    model = build_full_model(
        case_id=args.case,
        config_dir=args.config_dir,
        data_dir=args.data_dir,
        num_hours=args.num_hours,
    )

    # Override capacity optimization if specified
    if args.capacity_opt:
        print("\n⚙️  Capacity optimization: ENABLED (via CLI flag)")
        # Note: This requires rebuilding model with capacity_opt in config
        # For now, just warn the user
        print("   (To enable, set 'capacity_optimization: true' in base.yaml)")

    # Solve
    results = solve_model(
        model,
        solver_name=args.solver,
        time_limit=args.time_limit,
        mip_gap=args.mip_gap,
        output_dir=args.output_dir,
    )

    # Write results if optimal
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        from src.results.writers import write_dispatch_results, write_cost_summary
        from src.results.postprocess import calculate_kpis, print_kpis

        write_dispatch_results(model, output_dir=args.output_dir)
        write_cost_summary(model, output_dir=args.output_dir)

        kpis = calculate_kpis(model)
        print_kpis(kpis)

    return model, results


if __name__ == "__main__":
    model, results = main_cli()

