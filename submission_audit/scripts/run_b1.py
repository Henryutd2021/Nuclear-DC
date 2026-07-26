"""Task B1 — solve the capital x market-year interaction that the manuscript
currently only extrapolates.

Grid: capital {NOAK $2,250, Low-Mid $5,000} x year {2022, 2024} x Case {1, 2}
      -> 8 runs, everything else at the baseline (full-load PUE 1.35, WACC
      6.7%, carbon $0, 45Y at the unchanged $19.70/MWh_e, no BESS, 1.0x DC).

Plus one anchor run outside the required 8: Case 1 @ $5,000 @ 2023.  The
archived grid has 2023 anchors for NOAK (G4) and for Case 2 @ $5,000 (G5
Low_Mid x Baseline absorption), but Case 1 @ $5,000 @ 2023 was never solved,
and without it the separability check cannot cover the two Case-1 $5,000
cells.  The anchor makes the additivity test complete for all 8 cells.

Separability test:  TAC(K, year) =? TAC(K, 2023) + [TAC(ATB-Mid, year) -
TAC(ATB-Mid, 2023)] — exact if capital is a dispatch-neutral constant.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_runner import (  # noqa: E402
    PROJECT_ROOT,
    raa,
    run_specs,
    save_rows,
    set_output_root,
)

OUT = set_output_root("runs_b1")

CAP_TAGS = {2250.0: "NOAK", 5000.0: "USD5000"}
SCEN = {2250.0: "NOAK", 5000.0: "CUSTOM:5000"}

specs = []
for cid in (1, 2):
    for year in (2022, 2024):
        for cap in (2250.0, 5000.0):
            specs.append(
                raa.RunSpec(
                    group="b1_capital_year",
                    run_id=f"case{cid}_{CAP_TAGS[cap]}_{year}",
                    case_id=cid,
                    year=year,
                    pue=raa.BASELINE_FULL_LOAD_PUE,
                    reactor_scenario=SCEN[cap],
                )
            )
# Anchor: Case 1 @ $5,000 @ 2023 (completes the separability test).
specs.append(
    raa.RunSpec(
        group="b1_capital_year",
        run_id="case1_USD5000_2023",
        case_id=1,
        year=2023,
        pue=raa.BASELINE_FULL_LOAD_PUE,
        reactor_scenario="CUSTOM:5000",
    )
)

rows = run_specs(specs, workers=9, tag="B1")
save_rows(rows, OUT / "b1_rows.csv")

# ---------------------------------------------------------------------------
# Post-processing against the unchanged archived ledger
# ---------------------------------------------------------------------------
hist = pd.read_csv(PROJECT_ROOT / "outputs" / "master_kpi_table.csv")


def hist_tac(group: str, run_id: str) -> float:
    m = hist[(hist.group == group) & (hist.run_id == run_id)]
    assert len(m) == 1, (group, run_id, len(m))
    return float(m.iloc[0]["tac_usd_per_yr"])


case0_tac = {  # unchanged Case-0 anchors from the archived G2 rows
    2022: hist_tac("s2_price", "case0_year2022"),
    2023: hist_tac("s2_price", "case0_year2023"),
    2024: hist_tac("s2_price", "case0_year2024"),
}
atbmid_tac = {
    (cid, yr): hist_tac("s2_price", f"case{cid}_year{yr}")
    for cid in (1, 2)
    for yr in (2022, 2023, 2024)
}
anchor_2023 = {  # capital-specific 2023 anchors
    (1, 2250.0): hist_tac("s4_capex", "case1_NOAK"),
    (2, 2250.0): hist_tac("s4_capex", "case2_NOAK"),
    (2, 5000.0): hist_tac("s5_feasibility_2d", "case2_smr_Low_Mid_abs_Baseline"),
}

new = {r["run_id"]: r for r in rows}
anchor_2023[(1, 5000.0)] = new["case1_USD5000_2023"]["tac_usd_per_yr"]
anchor_2023_src = {
    (1, 2250.0): "outputs/s4_capex/case1_NOAK/summary.json",
    (2, 2250.0): "outputs/s4_capex/case2_NOAK/summary.json",
    (2, 5000.0): "outputs/s5_feasibility_2d/case2_smr_Low_Mid_abs_Baseline/summary.json",
    (1, 5000.0): "submission_audit/runs_b1/b1_capital_year/case1_USD5000_2023/summary.json",
}

runs_out, sep_rows = [], []
for cid in (1, 2):
    for year in (2022, 2024):
        for cap in (2250.0, 5000.0):
            r = new[f"case{cid}_{CAP_TAGS[cap]}_{year}"]
            tac = r["tac_usd_per_yr"]
            c0 = case0_tac[year]
            predicted = anchor_2023[(cid, cap)] + (
                atbmid_tac[(cid, year)] - atbmid_tac[(cid, 2023)]
            )
            sep_rows.append(
                {
                    "cell": r["run_id"],
                    "predicted_tac_usd": predicted,
                    "solved_tac_usd": tac,
                    "abs_dev_usd": abs(predicted - tac),
                    "anchor_2023_source": anchor_2023_src[(cid, cap)],
                }
            )
            runs_out.append(
                {
                    "case": cid,
                    "year": year,
                    "capital_usd_per_kwe": cap,
                    "tac_musd_yr": tac / 1e6,
                    "case0_tac_musd_yr": c0 / 1e6,
                    "margin_pct": 100.0 * (1.0 - tac / c0),
                    "net_export_twh_yr": (
                        r["P_grid_sell_annual_MWh"] - r["P_grid_buy_annual_MWh"]
                    )
                    / 1e6,
                    "ptc_musd_yr": -r["ptc_annual_usd"] / 1e6,
                    "output_file": f"submission_audit/runs_b1/b1_capital_year/{r['run_id']}/summary.json",
                }
            )

nk24 = new["case1_NOAK_2024"]["tac_usd_per_yr"]
nk24_pred = anchor_2023[(1, 2250.0)] + (
    atbmid_tac[(1, 2024)] - atbmid_tac[(1, 2023)]
)
b1 = {
    "runs": runs_out,
    "atb_mid_year_deltas": {
        "case1_2023_to_2024_musd_yr": (atbmid_tac[(1, 2024)] - atbmid_tac[(1, 2023)]) / 1e6,
        "case2_2023_to_2024_musd_yr": (atbmid_tac[(2, 2024)] - atbmid_tac[(2, 2023)]) / 1e6,
        "case1_2023_to_2022_musd_yr": (atbmid_tac[(1, 2022)] - atbmid_tac[(1, 2023)]) / 1e6,
        "case2_2023_to_2022_musd_yr": (atbmid_tac[(2, 2022)] - atbmid_tac[(2, 2023)]) / 1e6,
    },
    "separability_check": {
        "note": (
            "TAC(capital, year) additivity: predicted = TAC(capital, 2023) + "
            "[TAC(ATB-Mid, year) - TAC(ATB-Mid, 2023)] from the unchanged "
            "archived ledger (plus the case1@$5,000 2023 anchor solved here); "
            "solved = the fresh B1 run. Exact separability is expected because "
            "reactor capital enters TAC only as a dispatch-neutral constant."
        ),
        "predicted_noak_2024_case1_tac": nk24_pred / 1e6,
        "solved_noak_2024_case1_tac": nk24 / 1e6,
        "max_abs_deviation_musd_yr": max(s["abs_dev_usd"] for s in sep_rows) / 1e6,
        "all_cells": [
            {
                "cell": s["cell"],
                "predicted_musd_yr": s["predicted_tac_usd"] / 1e6,
                "solved_musd_yr": s["solved_tac_usd"] / 1e6,
                "abs_dev_musd_yr": s["abs_dev_usd"] / 1e6,
                "anchor_2023_source": s["anchor_2023_source"],
            }
            for s in sep_rows
        ],
    },
    "anchor_run_case1_usd5000_2023": {
        "tac_musd_yr": anchor_2023[(1, 5000.0)] / 1e6,
        "margin_pct": 100.0 * (1.0 - anchor_2023[(1, 5000.0)] / case0_tac[2023]),
        "output_file": "submission_audit/runs_b1/b1_capital_year/case1_USD5000_2023/summary.json",
    },
}

with (OUT / "B1_results.json").open("w") as f:
    json.dump(b1, f, indent=2)
print(json.dumps(b1, indent=2))
