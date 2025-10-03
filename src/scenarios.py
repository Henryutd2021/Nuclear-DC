"""Scenario management and sensitivity analysis."""

from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from src.solve import build_full_model, solve_model


def compare_cases(
    cases: List[int] = [1, 2, 3],
    num_hours: int = 168,
    config_dir: str = "config",
    data_dir: str = "data",
    output_dir: str = "outputs",
) -> pd.DataFrame:
    """
    Run all cases and compare results.

    Args:
        cases: List of case IDs to run
        num_hours: Number of hours to optimize
        config_dir: Config directory
        data_dir: Data directory
        output_dir: Output directory

    Returns:
        DataFrame with comparison results
    """
    print(f"\n{'='*70}")
    print("CASE COMPARISON")
    print(f"{'='*70}")

    results_list = []

    for case_id in cases:
        print(f"\n>>> Running Case {case_id}")

        # Build and solve
        model = build_full_model(
            case_id=case_id,
            config_dir=config_dir,
            data_dir=data_dir,
            num_hours=num_hours,
        )

        solver_results = solve_model(model, output_dir=output_dir)

        # Extract key metrics
        if solver_results.solver.termination_condition.value == "optimal":
            import pyomo.environ as pyo

            metrics = {
                "Case": case_id,
                "Status": "Optimal",
                "TAC [$/yr]": pyo.value(model.objective),
                "CAPEX [$/yr]": pyo.value(model.capex_annual_expr),
                "FOM [$/yr]": pyo.value(model.fom_annual_expr),
                "VOM [$/yr]": pyo.value(model.vom_annual_expr),
                "Fuel [$/yr]": pyo.value(model.fuel_annual_expr),
                "Grid [$/yr]": pyo.value(model.grid_annual_expr),
                "Turbine Cap [MW]": pyo.value(model.Cap_tur),
                "ORC Cap [MW]": pyo.value(model.Cap_ORC),
                "AB Cap [MWth]": pyo.value(model.Cap_AB),
                "EC Cap [MWth]": pyo.value(model.Cap_EC),
                "TES Cap [MWh]": pyo.value(model.Cap_TES),
            }
        else:
            metrics = {
                "Case": case_id,
                "Status": str(solver_results.solver.termination_condition),
                "TAC [$/yr]": None,
            }

        results_list.append(metrics)

    # Create comparison dataframe
    df = pd.DataFrame(results_list)

    print(f"\n{'='*70}")
    print("COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(df.to_string(index=False))

    # Save to CSV
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path / "case_comparison.csv", index=False)
    print(f"\nResults saved to {output_path / 'case_comparison.csv'}")

    return df


def main_cli():
    """CLI for scenario runs."""
    import argparse

    parser = argparse.ArgumentParser(description="Nuclear-DC Scenario Runner")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Compare cases
    compare_parser = subparsers.add_parser("compare-cases", help="Run and compare all cases")
    compare_parser.add_argument("--num-hours", type=int, default=168, help="Number of hours")
    compare_parser.add_argument("--config-dir", default="config", help="Config directory")
    compare_parser.add_argument("--data-dir", default="data", help="Data directory")
    compare_parser.add_argument("--output-dir", default="outputs", help="Output directory")

    args = parser.parse_args()

    if args.command == "compare-cases":
        compare_cases(
            num_hours=args.num_hours,
            config_dir=args.config_dir,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main_cli()

