"""Shared driver for the submission-audit supplementary solves.

Reuses scripts/run_all_analyses.py verbatim (same configs, same solver
settings, same artifact layout) but redirects every artifact into
submission_audit/ so no existing run output is ever touched, and layers
two audit-scoped overrides on top:

  * reactor_scenario "CUSTOM:<usd_per_kwe>" — a literal overnight-capital
    override for the B1 $5,000/kWe anchor (Cases 1-2), bypassing the
    three named scenarios in data/reactor/bwrx300_economic.yaml.
  * G9 mode — overrides financial.project_lifetime_years 20 -> 40 for the
    nuclear cases only, which changes exactly one number in the model:
    the Section 45Y levelization window in src/milp/builder.py:552-558
    (c_45Y = 30 * A(6.7%,10)/A(6.7%,40) = $15.47/MWh_e instead of
    A(10)/A(20) = $19.70/MWh_e).  grep confirms project_lifetime_years
    has no other consumer on the Cases 1-2 path (src/config.py:405 is
    with_wacc, which these runs never call; capital_recovery_factor is
    metadata only).

Everything else — per-asset amortization lives, fuel, PUE, WACC, solver
Method/Seed/MIPGap/Threads — is untouched.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Match the production grid exactly: 16 workers x 4 Gurobi threads.
os.environ.setdefault("NDC_THREADS_PER_SOLVE", "4")

import scripts.run_all_analyses as raa  # noqa: E402
from src.config import RunConfig  # noqa: E402

AUDIT_ROOT = PROJECT_ROOT / "submission_audit"

# ---------------------------------------------------------------------------
# Patch 1 — CUSTOM:<value> reactor-capital scenarios (B1 / B2 extras)
# ---------------------------------------------------------------------------
_orig_with_reactor_capex = raa.with_reactor_capex


def _with_reactor_capex_custom(cfg: RunConfig, scenario: str, project_root):
    if isinstance(scenario, str) and scenario.startswith("CUSTOM:"):
        occ = float(scenario.split(":", 1)[1])
        new_reactor = cfg.case.reactor.model_copy(
            update={"capex_usd_per_kWe": occ}
        )
        new_case = cfg.case.model_copy(update={"reactor": new_reactor})
        return cfg.model_copy(update={"case": new_case})
    return _orig_with_reactor_capex(cfg, scenario, project_root)


raa.with_reactor_capex = _with_reactor_capex_custom

# ---------------------------------------------------------------------------
# Patch 2 — G9: 45Y levelized over the 40-yr reactor amortization window
# ---------------------------------------------------------------------------
_orig_load_config = raa.load_config
_G9_MODE = {"on": False}


def _load_config_maybe_g9(case_id: int, project_root):
    cfg = _orig_load_config(case_id, project_root)
    if _G9_MODE["on"] and case_id in (1, 2):
        fin = cfg.financial.model_copy(update={"project_lifetime_years": 40})
        cfg = cfg.model_copy(update={"financial": fin})
    return cfg


raa.load_config = _load_config_maybe_g9


def set_g9(on: bool) -> None:
    _G9_MODE["on"] = bool(on)


def set_output_root(subdir: str) -> Path:
    """Redirect all artifacts to submission_audit/<subdir>/ (never outputs/)."""
    out = AUDIT_ROOT / subdir
    out.mkdir(parents=True, exist_ok=True)
    raa.OUTPUTS = out
    return out


def run_specs(specs, workers: int = 16, tag: str = "") -> list[dict]:
    """Execute RunSpecs against the patched module; fork inherits patches."""
    rows = []
    t0 = time.time()
    if workers <= 1:
        for i, s in enumerate(specs, 1):
            row = raa.execute_run(s)
            rows.append(row)
            print(
                f"[{i:>2}/{len(specs)}] {s.group}/{s.run_id:<34} "
                f"TAC={row['tac_usd_per_yr'] / 1e6:8.3f} M$ "
                f"({row['solve_seconds']:.1f}s)",
                flush=True,
            )
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(raa.execute_run, s): s for s in specs}
            for i, fut in enumerate(as_completed(futs), 1):
                s = futs[fut]
                row = fut.result()
                rows.append(row)
                print(
                    f"[{i:>2}/{len(specs)}] {s.group}/{s.run_id:<34} "
                    f"TAC={row['tac_usd_per_yr'] / 1e6:8.3f} M$ "
                    f"({row['solve_seconds']:.1f}s)",
                    flush=True,
                )
    print(f"{tag} wall time: {time.time() - t0:.1f}s", flush=True)
    return rows


def save_rows(rows: list[dict], path: Path) -> None:
    import pandas as pd

    df = pd.DataFrame(rows).sort_values(["group", "run_id"], kind="mergesort")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_summary(run_dir: Path) -> dict:
    with (run_dir / "summary.json").open() as f:
        return json.load(f)
