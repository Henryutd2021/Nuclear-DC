"""Gate test: re-solve the 2023 baseline (Cases 0-3) with today's code and
compare against the manuscript-reported values. Abort criterion: any
deviation > 0.5%.

Also cross-checks the fresh solves against the historical
outputs/master_kpi_table.csv rows so silent code drift since the archived
run grid (2026-06-10) is detected explicitly, and counts the absorption
operating hours from the fresh dispatch trace.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_runner import (  # noqa: E402
    PROJECT_ROOT,
    load_summary,
    raa,
    run_specs,
    save_rows,
    set_output_root,
)

OUT = set_output_root("runs_gate")

# The four G0 rows exactly as build_run_grid() defines them.
specs = [s for s in raa.build_run_grid() if s.group == "main_baseline"]
assert len(specs) == 4, specs

rows = run_specs(specs, workers=4, tag="gate")
save_rows(rows, OUT / "gate_rows.csv")

by_case = {r["case_id"]: r for r in rows}

# Absorption operating hours + cooling share from the fresh Case-2 dispatch.
disp = pd.read_csv(
    gzip.open(OUT / "main_baseline" / "case2" / "dispatch.csv.gz")
)
abs_hours = int((disp["Q_abs_cool_MWth"] > 1e-6).sum())
c2 = by_case[2]
abs_share = c2["Q_abs_cool_annual_MWh"] / c2["cool_energy_annual_MWh"]

# ---------------------------------------------------------------------------
# Manuscript-reported values (rounded as printed) vs fresh solves
# ---------------------------------------------------------------------------
checks = [
    ("Case 0 TAC (M$/yr)", 75.9, by_case[0]["tac_usd_per_yr"] / 1e6),
    ("Case 1 TAC (M$/yr)", 113.4, by_case[1]["tac_usd_per_yr"] / 1e6),
    ("Case 2 TAC (M$/yr)", 122.6, by_case[2]["tac_usd_per_yr"] / 1e6),
    ("Case 3 TAC (M$/yr)", 55.6, by_case[3]["tac_usd_per_yr"] / 1e6),
    ("Case 1 45Y credit (M$/yr)", 42.9, -by_case[1]["ptc_annual_usd"] / 1e6),
    ("Case 2 45Y credit (M$/yr)", 41.8, -by_case[2]["ptc_annual_usd"] / 1e6),
    ("Absorption supply (GWh_c/yr)", 352.0, c2["Q_abs_cool_annual_MWh"] / 1e3),
    ("Absorption share of cooling (%)", 38.0, abs_share * 100.0),
    ("Absorption operating hours (h)", 5300.0, float(abs_hours)),
]

report = []
worst = 0.0
for name, printed, solved in checks:
    dev = abs(solved - printed) / abs(printed)
    worst = max(worst, dev)
    report.append(
        {
            "check": name,
            "manuscript_value": printed,
            "solved_value": solved,
            "rel_dev_pct": 100.0 * dev,
            "pass_0p5pct": bool(dev <= 0.005),
        }
    )

# ---------------------------------------------------------------------------
# Drift check vs the archived 2026-06-10 master table (exact-level match)
# ---------------------------------------------------------------------------
hist = pd.read_csv(PROJECT_ROOT / "outputs" / "master_kpi_table.csv")
hist_g0 = hist[hist.group == "main_baseline"].set_index("case_id")
drift = []
for cid, r in by_case.items():
    h = hist_g0.loc[cid]
    drift.append(
        {
            "case_id": cid,
            "tac_new_usd": r["tac_usd_per_yr"],
            "tac_2026_06_10_usd": float(h["tac_usd_per_yr"]),
            "rel_diff": abs(r["tac_usd_per_yr"] - float(h["tac_usd_per_yr"]))
            / float(h["tac_usd_per_yr"]),
        }
    )

result = {
    "gate_passed": all(c["pass_0p5pct"] for c in report),
    "worst_rel_dev_pct": 100.0 * worst,
    "checks": report,
    "drift_vs_archived_grid": drift,
    "solver": {
        "gurobi_threads_per_solve": 4,
        "mip_gap_target": 1e-4,
        "mip_gap_achieved": {
            str(cid): load_summary(OUT / "main_baseline" / f"case{cid}")[
                "metadata"
            ].get("mip_gap_achieved")
            for cid in (1, 2)
        },
    },
    "unrounded": {
        "case0_tac_usd": by_case[0]["tac_usd_per_yr"],
        "case1_tac_usd": by_case[1]["tac_usd_per_yr"],
        "case2_tac_usd": by_case[2]["tac_usd_per_yr"],
        "case3_tac_usd": by_case[3]["tac_usd_per_yr"],
        "case1_ptc_usd": by_case[1]["ptc_annual_usd"],
        "case2_ptc_usd": by_case[2]["ptc_annual_usd"],
        "case2_q_abs_mwh": c2["Q_abs_cool_annual_MWh"],
        "case2_cooling_mwh": c2["cool_energy_annual_MWh"],
        "case2_abs_hours": abs_hours,
        "case1_margin": 1.0
        - by_case[1]["tac_usd_per_yr"] / by_case[0]["tac_usd_per_yr"],
        "case2_margin": 1.0
        - by_case[2]["tac_usd_per_yr"] / by_case[0]["tac_usd_per_yr"],
    },
}

with (OUT / "gate_check.json").open("w") as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
print("\nGATE:", "PASS" if result["gate_passed"] else "FAIL")
