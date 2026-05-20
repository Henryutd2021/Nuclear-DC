"""Drive every plan-v2.5 run (baseline + S1..S5) and stage outputs/.

Run grid (51 solves total, per plan §3 and §5 Phase 2):

  main_baseline   5 runs   Cases 0-4  | year 2023 | PUE 1.30 | reactor ATB-Mid
  s1_pue          9 runs   Cases 1-3  | year 2023 | PUE in {1.10, 1.30, 1.50}
                                                  | reactor ATB-Mid
  s2_price       15 runs   Cases 0-4  | year in {2022, 2023, 2024} | PUE 1.30
                                                  | reactor ATB-Mid
  s3_battery     10 runs   Cases 0-4  | year 2023 | PUE 1.30
                                                  | bess in {off, on}
                                                  | (Cases 0/4 have no BESS block;
                                                  rows duplicated for table shape)
  s4_capex        9 runs   Cases 1-3  | year 2023 | PUE 1.30
                                                  | reactor in {FOAK, ATB_Mid, NOAK}
  s5_equipment    3 runs   Case 2     | year 2023 | PUE 1.30
                                                  | (ORC, abs) CAPEX jointly
                                                  scaled by {0.6, 1.0, 1.4}

Outputs layout:

  outputs/<group>/<run_id>/summary.json     -- scalar KPIs + metadata
  outputs/<group>/<run_id>/dispatch.csv.gz  -- hourly time series (compressed)
  outputs/master_kpi_table.csv              -- 51-row flat table
  outputs/manifest.json                     -- run grid + execution stats
"""

from __future__ import annotations

import json
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

from src.cases.case0 import Case0Result, solve_case0  # noqa: E402
from src.cases.case1 import solve_case1  # noqa: E402
from src.cases.case2 import solve_case2  # noqa: E402
from src.cases.case3 import solve_case3  # noqa: E402
from src.cases.case4 import Case4Result, solve_case4  # noqa: E402
from src.config import (  # noqa: E402
    RunConfig,
    load_config,
    with_bess,
    with_reactor_capex,
)
from src.data import TimeSeries, load_time_series  # noqa: E402
from src.kpi import heat_recovery_premium  # noqa: E402
from src.milp.result import NuclearCaseResult  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = PROJECT_ROOT / "outputs"

CASE_SOLVERS: dict[int, Callable] = {
    0: solve_case0,
    1: solve_case1,
    2: solve_case2,
    3: solve_case3,
    4: solve_case4,
}

# ---------------------------------------------------------------------------
# Result -> common DataFrame / scalar dict
# ---------------------------------------------------------------------------


def _result_to_dispatch_df(
    r: Union[Case0Result, Case4Result, NuclearCaseResult],
) -> pd.DataFrame:
    """Stack the hourly Series carried by every result type into one frame."""
    cols: dict[str, pd.Series] = {}
    # Common fields
    cols["P_IT_MW"] = r.P_IT_MW
    cols["Q_cool_MWth"] = getattr(
        r, "Q_cool_MWth", getattr(r, "Q_cool_demand_MWth", None)
    )
    cols["P_VCC_elec_MW"] = r.P_VCC_elec_MW
    # Case-specific
    if isinstance(r, Case0Result):
        cols["P_grid_buy_MW"] = r.P_grid_buy_MW
        cols["grid_cost_usd_per_h"] = r.grid_cost_usd_per_h
        cols["grid_emissions_kg_co2_per_h"] = r.grid_emissions_kg_co2_per_h
    elif isinstance(r, Case4Result):
        cols["P_NGCC_elec_MW"] = r.P_NGCC_elec_MW
        cols["fuel_consumption_MMBtu_per_h"] = r.fuel_consumption_MMBtu_per_h
        cols["fuel_cost_usd_per_h"] = r.fuel_cost_usd_per_h
        cols["direct_emissions_kg_co2_per_h"] = r.direct_emissions_kg_co2_per_h
        cols["upstream_emissions_kg_co2_per_h"] = r.upstream_emissions_kg_co2_per_h
    else:  # NuclearCaseResult
        cols["P_rx_MWth"] = r.P_rx_MWth
        cols["P_turb_net_MW"] = r.P_turb_net_MW
        cols["P_orc_MW"] = r.P_orc_MW
        cols["Q_to_abs_MWth"] = r.Q_to_abs_MWth
        cols["Q_abs_cool_MWth"] = r.Q_abs_cool_MWth
        cols["Q_VCC_cool_MWth"] = r.Q_VCC_cool_MWth
        cols["P_grid_buy_MW"] = r.P_grid_buy_MW
        cols["P_grid_sell_MW"] = r.P_grid_sell_MW
    df = pd.DataFrame(cols)
    df.index.name = "hour"
    return df


def _result_to_scalars(
    r: Union[Case0Result, Case4Result, NuclearCaseResult],
    ts: TimeSeries,
    cfg: RunConfig,
) -> dict[str, Any]:
    """Scalar KPIs, common across result types.

    LCOE denominator = IT energy delivered (MWh_e/yr).
    LCOC denominator = cooling delivered (MWh_c/yr).
    LCOC numerator (Case 0): CAPEX+FOM+VOM(VCC) + grid cost attributable to VCC.
    LCOC numerator (Cases 1-4): cooling-side equipment cost only (we don't try
    to split shared electricity-sourcing cost across IT vs VCC, so the LCOC
    here is the cooling-equipment levelized cost — the comparable cross-case
    number is total TAC and the Heat-Recovery Premium).
    """
    dt = cfg.base.time.delta_t
    n = r.P_IT_MW.shape[0]
    annual_scale = 8760.0 / n
    it_energy_annual_MWh = float(r.P_IT_MW.sum() * dt * annual_scale)
    cool_energy_annual_MWh = float(
        (r.Q_cool_MWth if hasattr(r, "Q_cool_MWth") else r.Q_cool_demand_MWth).sum()
        * dt
        * annual_scale
    )

    tac = float(r.tac_usd_per_yr)
    lcoe = tac / it_energy_annual_MWh if it_energy_annual_MWh > 0 else float("nan")

    out: dict[str, Any] = {
        "tac_usd_per_yr": tac,
        "lcoe_usd_per_mwh_e": lcoe,
        "it_energy_annual_MWh": it_energy_annual_MWh,
        "cool_energy_annual_MWh": cool_energy_annual_MWh,
        "capex_annual_usd": float(r.capex_annual_usd),
        "fom_annual_usd": float(r.fom_annual_usd),
        "vom_annual_usd": float(r.vom_annual_usd),
        "pue": float(r.pue),
    }

    if isinstance(r, Case0Result):
        out["co2_annual_tonnes"] = float(r.co2_annual_tonnes)
        out["grid_annual_usd"] = float(r.grid_annual_usd)
        out["fuel_annual_usd"] = 0.0
        # LCOC for Case 0: cooling-attributable cost
        grid_cost_cooling_annual = float(
            (ts.price_import_usd_per_mwh * r.P_VCC_elec_MW * dt).sum() * annual_scale
        )
        cost_cooling = (
            r.capex_annual_usd + r.fom_annual_usd + r.vom_annual_usd
            + grid_cost_cooling_annual
        )
        out["lcoc_usd_per_mwh_c"] = (
            cost_cooling / cool_energy_annual_MWh
            if cool_energy_annual_MWh > 0 else float("nan")
        )
        out["co2_per_mwh_kg"] = (
            r.co2_annual_tonnes * 1000.0 / it_energy_annual_MWh
            if it_energy_annual_MWh > 0 else float("nan")
        )
    elif isinstance(r, Case4Result):
        out["co2_annual_tonnes"] = float(r.co2_lifecycle_annual_tonnes)
        out["co2_direct_annual_tonnes"] = float(r.co2_direct_annual_tonnes)
        out["co2_lifecycle_annual_tonnes"] = float(r.co2_lifecycle_annual_tonnes)
        out["fuel_annual_usd"] = float(r.fuel_annual_usd)
        out["grid_annual_usd"] = 0.0
        out["ngcc_capacity_MWe"] = float(r.ngcc_capacity_MWe)
        out["delivered_fuel_usd_per_mmbtu"] = float(r.delivered_fuel_usd_per_mmbtu)
        out["lcoc_usd_per_mwh_c"] = float("nan")  # not directly split
        out["co2_per_mwh_kg"] = (
            r.co2_lifecycle_annual_tonnes * 1000.0 / it_energy_annual_MWh
            if it_energy_annual_MWh > 0 else float("nan")
        )
    else:  # NuclearCaseResult
        out["co2_annual_tonnes"] = float(r.co2_annual_tonnes)
        out["fuel_annual_usd"] = float(r.fuel_annual_usd)
        out["grid_annual_usd"] = float(r.grid_annual_usd)
        out["P_orc_annual_MWh"] = float(r.P_orc_MW.sum() * dt * annual_scale)
        out["Q_abs_cool_annual_MWh"] = float(
            r.Q_abs_cool_MWth.sum() * dt * annual_scale
        )
        out["P_grid_buy_annual_MWh"] = float(
            r.P_grid_buy_MW.sum() * dt * annual_scale
        )
        out["P_grid_sell_annual_MWh"] = float(
            r.P_grid_sell_MW.sum() * dt * annual_scale
        )
        out["lcoc_usd_per_mwh_c"] = float("nan")
        out["co2_per_mwh_kg"] = (
            r.co2_annual_tonnes * 1000.0 / it_energy_annual_MWh
            if it_energy_annual_MWh > 0 else float("nan")
        )

    return out


# ---------------------------------------------------------------------------
# Equipment-CAPEX override helper for S5
# ---------------------------------------------------------------------------


def with_equipment_capex(cfg: RunConfig, factor: float) -> RunConfig:
    """Scale ORC and absorption installed CAPEX by ``factor`` (S5 robustness).

    Plan §3: jointly scale ORC + absorption CAPEX by {0.6, 1.0, 1.4} to span
    the ±40% combined uncertainty band (ORC 1,680..3,920 $/kWe and
    absorption 450..1,050 $/kWth around the §F baselines 2,800 and 750).

    Returns a new RunConfig; the input is untouched.
    """
    if cfg.case.case_id != 2:
        raise ValueError("S5 robustness only applies to Case 2 in v2.5")
    new_orc = cfg.case.orc.model_copy(
        update={"capex_usd_per_kWe": cfg.case.orc.capex_usd_per_kWe * factor}
    )
    new_abs = cfg.case.absorption.model_copy(
        update={
            "capex_usd_per_kWth": cfg.case.absorption.capex_usd_per_kWth * factor
        }
    )
    new_case = cfg.case.model_copy(update={"orc": new_orc, "absorption": new_abs})
    return cfg.model_copy(update={"case": new_case})


# ---------------------------------------------------------------------------
# Single-run executor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunSpec:
    """One row of the 51-run grid."""

    group: str        # 'main_baseline' | 's1_pue' | ...
    run_id: str       # filesystem-safe key, unique within group
    case_id: int
    year: int
    pue: float
    reactor_scenario: Optional[str] = None   # 'FOAK' | 'ATB_Mid' | 'NOAK' | None
    bess_on: bool = False                    # only meaningful for Cases 1-3
    equipment_capex_factor: Optional[float] = None  # S5 only

    @property
    def output_dir(self) -> Path:
        return OUTPUTS / self.group / self.run_id


def execute_run(spec: RunSpec) -> dict[str, Any]:
    """Build the cfg, solve, write artifacts, and return the scalar row."""
    t0 = time.time()
    cfg = load_config(case_id=spec.case_id, project_root=PROJECT_ROOT)

    # --- Reactor CAPEX scenario (S4) ---------------------------------------
    if spec.reactor_scenario is not None and spec.case_id in (1, 2, 3):
        cfg = with_reactor_capex(cfg, spec.reactor_scenario, PROJECT_ROOT)

    # --- BESS toggle (S3) ---------------------------------------------------
    bess_supported = spec.case_id in (1, 2, 3) and cfg.case.bess is not None
    bess_applied = spec.bess_on and bess_supported
    if bess_applied:
        cfg = with_bess(cfg, True)

    # --- Equipment CAPEX scale (S5) ----------------------------------------
    if spec.equipment_capex_factor is not None:
        cfg = with_equipment_capex(cfg, spec.equipment_capex_factor)

    # --- Time series --------------------------------------------------------
    ts = load_time_series(project_root=PROJECT_ROOT, year=spec.year, num_hours=8760)

    # --- Solve --------------------------------------------------------------
    solver = CASE_SOLVERS[spec.case_id]
    result = solver(cfg, ts, pue=spec.pue)
    solve_seconds = time.time() - t0

    # --- Artifacts ----------------------------------------------------------
    spec.output_dir.mkdir(parents=True, exist_ok=True)
    dispatch_df = _result_to_dispatch_df(result)
    dispatch_df.to_csv(
        spec.output_dir / "dispatch.csv.gz", compression="gzip"
    )

    scalars = _result_to_scalars(result, ts, cfg)
    summary = {
        **scalars,
        "metadata": {
            "group": spec.group,
            "run_id": spec.run_id,
            "case_id": spec.case_id,
            "year": spec.year,
            "pue": spec.pue,
            "reactor_scenario": spec.reactor_scenario,
            "bess_on_requested": spec.bess_on,
            "bess_supported": bess_supported,
            "bess_applied": bess_applied,
            "equipment_capex_factor": spec.equipment_capex_factor,
            "num_hours": ts.num_hours,
            "solve_seconds": round(solve_seconds, 3),
        },
    }
    with (spec.output_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    # Master-table row ------------------------------------------------------
    row = {
        "group": spec.group,
        "run_id": spec.run_id,
        "case_id": spec.case_id,
        "year": spec.year,
        "pue": spec.pue,
        "reactor_scenario": spec.reactor_scenario,
        "bess_applied": bess_applied,
        "equipment_capex_factor": spec.equipment_capex_factor,
        "solve_seconds": round(solve_seconds, 3),
        **{k: v for k, v in scalars.items() if not isinstance(v, dict)},
    }
    return row


# ---------------------------------------------------------------------------
# Run-grid definition
# ---------------------------------------------------------------------------


def build_run_grid() -> list[RunSpec]:
    specs: list[RunSpec] = []

    # ---- main_baseline: 5 cases, 2023, PUE 1.30, ATB-Mid ------------------
    for cid in range(5):
        specs.append(
            RunSpec(
                group="main_baseline",
                run_id=f"case{cid}",
                case_id=cid,
                year=2023,
                pue=1.30,
                reactor_scenario="ATB_Mid" if cid in (1, 2, 3) else None,
            )
        )

    # ---- S1 PUE: Cases 1-3 × {1.10, 1.30, 1.50}, 2023, ATB-Mid ------------
    for cid in (1, 2, 3):
        for pue in (1.10, 1.30, 1.50):
            pue_tag = f"{int(round(pue * 100)):03d}"
            specs.append(
                RunSpec(
                    group="s1_pue",
                    run_id=f"case{cid}_pue{pue_tag}",
                    case_id=cid,
                    year=2023,
                    pue=pue,
                    reactor_scenario="ATB_Mid",
                )
            )

    # ---- S2 ERCOT year regime: 5 cases × {2022, 2023, 2024} ---------------
    for year in (2022, 2023, 2024):
        for cid in range(5):
            specs.append(
                RunSpec(
                    group="s2_price",
                    run_id=f"case{cid}_year{year}",
                    case_id=cid,
                    year=year,
                    pue=1.30,
                    reactor_scenario="ATB_Mid" if cid in (1, 2, 3) else None,
                )
            )

    # ---- S3 BESS: 5 cases × {off, on}, 2023, ATB-Mid ----------------------
    for cid in range(5):
        for bess_on in (False, True):
            tag = "on" if bess_on else "off"
            specs.append(
                RunSpec(
                    group="s3_battery",
                    run_id=f"case{cid}_bess_{tag}",
                    case_id=cid,
                    year=2023,
                    pue=1.30,
                    reactor_scenario="ATB_Mid" if cid in (1, 2, 3) else None,
                    bess_on=bess_on,
                )
            )

    # ---- S4 Reactor CAPEX: Cases 1-3 × {FOAK, ATB_Mid, NOAK}, 2023 -------
    for cid in (1, 2, 3):
        for scen in ("FOAK", "ATB_Mid", "NOAK"):
            specs.append(
                RunSpec(
                    group="s4_capex",
                    run_id=f"case{cid}_{scen}",
                    case_id=cid,
                    year=2023,
                    pue=1.30,
                    reactor_scenario=scen,
                )
            )

    # ---- S5 Equipment CAPEX robustness: Case 2 × {0.6, 1.0, 1.4}, 2023 ----
    for factor, tag in ((0.6, "low"), (1.0, "baseline"), (1.4, "high")):
        specs.append(
            RunSpec(
                group="s5_equipment",
                run_id=f"case2_eq_{tag}",
                case_id=2,
                year=2023,
                pue=1.30,
                reactor_scenario="ATB_Mid",
                equipment_capex_factor=factor,
            )
        )

    return specs


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


def _add_premium_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Heat-Recovery Premium against the per-(group, year, pue,
    reactor_scenario) Case-0 TAC. Premium for Case 0 itself is 0.

    The matching key is (group, year, pue, reactor_scenario) so each
    sensitivity slice picks its own Case-0 denominator. For groups where
    Case-0 doesn't vary (e.g. S1 PUE, where Case 0 is missing because we
    don't sweep PUE for it), we fall back to the main_baseline Case-0 TAC
    at the matching (year, pue) — which equals the natural denominator.
    """
    baseline_case0 = (
        df[df["case_id"] == 0]
        .set_index(["year", "pue", "bess_applied"])["tac_usd_per_yr"]
        .to_dict()
    )
    main_case0 = float(
        df[
            (df["group"] == "main_baseline") & (df["case_id"] == 0)
        ]["tac_usd_per_yr"].iloc[0]
    )

    def _premium(row) -> float:
        key = (row["year"], row["pue"], row["bess_applied"])
        denom = baseline_case0.get(key)
        if denom is None:
            # fall back to (year, pue, False) — Case 0 unaffected by BESS
            denom = baseline_case0.get((row["year"], row["pue"], False))
        if denom is None:
            denom = main_case0
        return heat_recovery_premium(denom, row["tac_usd_per_yr"])

    df = df.copy()
    df["tac_case0_baseline_usd_per_yr"] = df.apply(
        lambda r: baseline_case0.get(
            (r["year"], r["pue"], r["bess_applied"]),
            baseline_case0.get((r["year"], r["pue"], False), main_case0),
        ),
        axis=1,
    )
    df["heat_recovery_premium"] = df.apply(_premium, axis=1)
    return df


def write_master_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df = _add_premium_columns(df)
    leading = [
        "group",
        "run_id",
        "case_id",
        "year",
        "pue",
        "reactor_scenario",
        "bess_applied",
        "equipment_capex_factor",
        "tac_usd_per_yr",
        "tac_case0_baseline_usd_per_yr",
        "heat_recovery_premium",
        "lcoe_usd_per_mwh_e",
        "lcoc_usd_per_mwh_c",
        "co2_annual_tonnes",
        "co2_per_mwh_kg",
    ]
    cols = leading + [c for c in df.columns if c not in leading]
    df = df[cols]
    df.to_csv(OUTPUTS / "master_kpi_table.csv", index=False)
    return df


def write_manifest(specs: list[RunSpec], rows: list[dict[str, Any]]) -> None:
    by_group: dict[str, list[str]] = {}
    for s in specs:
        by_group.setdefault(s.group, []).append(s.run_id)
    total_seconds = float(sum(r.get("solve_seconds", 0.0) for r in rows))
    manifest = {
        "plan_version": "v2.5",
        "executed_at_utc": pd.Timestamp.utcnow().isoformat(),
        "num_runs": len(specs),
        "total_solve_seconds": round(total_seconds, 1),
        "groups": {
            g: {"num_runs": len(ids), "run_ids": ids}
            for g, ids in by_group.items()
        },
        "files": {
            "master_table_csv": "outputs/master_kpi_table.csv",
            "per_run_dir": "outputs/<group>/<run_id>/",
            "per_run_artifacts": [
                "summary.json (scalar KPIs + metadata)",
                "dispatch.csv.gz (8760 hourly rows)",
            ],
        },
        "notes": [
            "Cases 0 and 4 are deterministic LP/closed-form; Cases 1-3 are "
            "Pyomo MILP solved with Gurobi (LP relaxation in practice — no "
            "binaries are introduced by S3 BESS).",
            "S3 BESS rows for Cases 0/4 carry bess_applied=False because "
            "those cases have no BESS block; rows preserved for table shape.",
            "Premium is computed against the Case-0 TAC at matching "
            "(year, pue), falling back to (year, pue, bess=False) if needed.",
        ],
    }
    with (OUTPUTS / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    specs = build_run_grid()
    print(f"Running {len(specs)} solves (plan-v2.5)\n")
    rows: list[dict[str, Any]] = []
    t0 = time.time()
    for i, s in enumerate(specs, 1):
        row = execute_run(s)
        rows.append(row)
        print(
            f"[{i:>2}/{len(specs)}] {s.group:>14}/{s.run_id:<22} "
            f"TAC={row['tac_usd_per_yr']/1e6:7.2f} M$ "
            f"({row['solve_seconds']:.1f}s)"
        )
    print(f"\nTotal wall time: {time.time() - t0:.1f} s")
    df = write_master_table(rows)
    write_manifest(specs, rows)
    print(
        f"Wrote {len(df)} rows to outputs/master_kpi_table.csv; "
        f"manifest at outputs/manifest.json"
    )


if __name__ == "__main__":
    main()
