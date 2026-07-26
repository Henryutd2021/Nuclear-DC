"""Task B2 — G9 sensitivity: Section 45Y credit levelized over the 40-yr
reactor amortization window instead of the 20-yr comparison window.

One parameter changes: financial.project_lifetime_years 20 -> 40 for the
nuclear cases (see audit_runner docstring; c_45Y falls from $19.70 to
$15.47/MWh_e and, because the credit sits in the objective, dispatch is
re-optimized rather than rescaled).  The baseline runs are NOT replaced:
everything lands under submission_audit/runs_b2/ as scenario group G9.

Scope: all 70 nuclear (Cases 1-2) runs of the production grid re-solved
under G9, plus two extra Case-2 capital points ($3,500 and $4,500/kWe,
2023, absorption at the $750 baseline) so the re-located parity threshold
is bracketed more tightly than the S4/S5 axis alone allows.
"""

from __future__ import annotations

import dataclasses
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
    set_g9,
    set_output_root,
)
from src.finance import levelized_ptc_usd_per_mwh  # noqa: E402

OUT = set_output_root("runs_b2")
set_g9(True)

C45Y_G9 = levelized_ptc_usd_per_mwh(30.0, 0.067, 10, 40)
C45Y_BASE = levelized_ptc_usd_per_mwh(30.0, 0.067, 10, 20)
print(f"c_45Y: baseline {C45Y_BASE:.4f} -> G9 {C45Y_G9:.4f} $/MWh_e", flush=True)

nuclear = [s for s in raa.build_run_grid() if s.case_id in (1, 2)]
assert len(nuclear) == 70, len(nuclear)
specs = [dataclasses.replace(s, group=f"g9_{s.group}") for s in nuclear]
specs += [
    raa.RunSpec(
        group="g9_capital_extra",
        run_id=f"case2_USD{cap}",
        case_id=2,
        year=2023,
        pue=raa.BASELINE_FULL_LOAD_PUE,
        reactor_scenario=f"CUSTOM:{cap}",
    )
    for cap in (3500, 4500)
]

rows = run_specs(specs, workers=16, tag="B2/G9")
save_rows(rows, OUT / "g9_rows.csv")

# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------
new = {(r["group"], r["run_id"]): r for r in rows}
hist = pd.read_csv(PROJECT_ROOT / "outputs" / "master_kpi_table.csv")


def hist_row(group: str, run_id: str) -> pd.Series:
    m = hist[(hist.group == group) & (hist.run_id == run_id)]
    assert len(m) == 1, (group, run_id)
    return m.iloc[0]


case0_2023 = float(hist_row("main_baseline", "case0")["tac_usd_per_yr"])
margin = lambda tac, base=case0_2023: 100.0 * (1.0 - tac / base)  # noqa: E731

# Old (baseline-PTC) margins for the delta columns.
old_m1 = margin(float(hist_row("main_baseline", "case1")["tac_usd_per_yr"]))
old_m2 = margin(float(hist_row("main_baseline", "case2")["tac_usd_per_yr"]))

g9_m1 = margin(new[("g9_main_baseline", "case1")]["tac_usd_per_yr"])
g9_m2 = margin(new[("g9_main_baseline", "case2")]["tac_usd_per_yr"])

# ---- Case 2 capital scan (2023, absorption $750) --------------------------
scan_cells = [
    (2250.0, ("g9_s4_capex", "case2_NOAK")),
    (3500.0, ("g9_capital_extra", "case2_USD3500")),
    (4500.0, ("g9_capital_extra", "case2_USD4500")),
    (5000.0, ("g9_s5_feasibility_2d", "case2_smr_Low_Mid_abs_Baseline")),
    (7615.0, ("g9_s4_capex", "case2_ATB_Mid")),
    (11000.0, ("g9_s5_feasibility_2d", "case2_smr_High_Mid_abs_Baseline")),
    (14700.0, ("g9_s4_capex", "case2_FOAK")),
]
capital_scan = [
    {
        "capital_usd_per_kwe": cap,
        "case2_tac_musd_yr": new[key]["tac_usd_per_yr"] / 1e6,
        "case2_margin_pct": margin(new[key]["tac_usd_per_yr"]),
        "output_file": f"submission_audit/runs_b2/{key[0]}/{key[1]}/summary.json",
    }
    for cap, key in scan_cells
]


def zero_crossing(xy: list[tuple[float, float]]) -> float | None:
    """Linear-interpolated x where y crosses 0 between adjacent solved points."""
    for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
        if (y0 >= 0.0) != (y1 >= 0.0):
            return x0 + (x1 - x0) * (0.0 - y0) / (y1 - y0)
    return None


parity = zero_crossing(
    [(c["capital_usd_per_kwe"], c["case2_margin_pct"]) for c in capital_scan]
)

# Case-1 parity threshold on the same G9 axis (S4 anchors only).
case1_scan = [
    (2250.0, new[("g9_s4_capex", "case1_NOAK")]["tac_usd_per_yr"]),
    (7615.0, new[("g9_s4_capex", "case1_ATB_Mid")]["tac_usd_per_yr"]),
    (14700.0, new[("g9_s4_capex", "case1_FOAK")]["tac_usd_per_yr"]),
]
parity_case1 = zero_crossing([(c, margin(t)) for c, t in case1_scan])

# ---- Carbon-price crossovers (2023 ATB-Mid, G9 PTC) -----------------------
case0_carbon = {
    p: float(hist_row("s6_carbon_price", f"case0_co2_{p}")["tac_usd_per_yr"])
    for p in (0, 50, 100)
}
crossovers = {}
for cid in (1, 2):
    diffs = [
        (
            float(p),
            new[("g9_s6_carbon_price", f"case{cid}_co2_{p}")]["tac_usd_per_yr"]
            - case0_carbon[p],
        )
        for p in (0, 50, 100)
    ]
    crossovers[f"case{cid}"] = zero_crossing(diffs)

# ---- Realized credit rate sanity check ------------------------------------
import gzip  # noqa: E402

d1 = pd.read_csv(
    gzip.open(OUT / "g9_main_baseline" / "case1" / "dispatch.csv.gz")
)
p_tn_annual = float(d1["P_turb_net_MW"].sum())
rate_realized = -new[("g9_main_baseline", "case1")]["ptc_annual_usd"] / p_tn_annual

b2 = {
    "c45y_alt_usd_per_mwh": round(C45Y_G9, 4),
    "c45y_alt_exact": C45Y_G9,
    "c45y_realized_from_dispatch_usd_per_mwh": rate_realized,
    "scope": "all 70 nuclear runs of the production grid re-solved under G9 "
             "+ 2 extra Case-2 capital points (3500, 4500)",
    "baseline_margins": {
        "case1_pct": g9_m1,
        "case2_pct": g9_m2,
        "case1_delta_pp": g9_m1 - old_m1,
        "case2_delta_pp": g9_m2 - old_m2,
        "case1_tac_musd_yr": new[("g9_main_baseline", "case1")]["tac_usd_per_yr"] / 1e6,
        "case2_tac_musd_yr": new[("g9_main_baseline", "case2")]["tac_usd_per_yr"] / 1e6,
    },
    "parity_threshold_usd_per_kwe": parity,
    "parity_threshold_case1_usd_per_kwe": parity_case1,
    "carbon_crossovers_usd_per_tco2": crossovers,
    "capital_scan": capital_scan,
    "output_dir": "submission_audit/runs_b2/",
}

with (OUT / "B2_results.json").open("w") as f:
    json.dump(b2, f, indent=2)
print(json.dumps(b2, indent=2))
