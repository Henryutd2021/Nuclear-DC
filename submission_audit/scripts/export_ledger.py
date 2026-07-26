"""Export the unrounded 100-run ledger to submission_audit/audit/ledger_full.csv.

Source of truth: outputs/<group>/<run_id>/summary.json (per-run artifacts of
the archived 2026-06-10 grid).  outputs/master_kpi_table.csv is used for the
derived margin columns and cross-checked field-by-field against every
summary.json so any divergence between the two artifact layers is surfaced
instead of silently trusted.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"
AUDIT = ROOT / "submission_audit" / "audit"
AUDIT.mkdir(parents=True, exist_ok=True)

master = pd.read_csv(OUTPUTS / "master_kpi_table.csv")
assert len(master) == 100, f"expected 100 rows, got {len(master)}"

# ---------------------------------------------------------------------------
# Cross-check master rows against per-run summary.json
# ---------------------------------------------------------------------------
CHECK_FIELDS = [
    "tac_usd_per_yr",
    "capex_annual_usd",
    "fom_annual_usd",
    "vom_annual_usd",
    "grid_annual_usd",
    "fuel_annual_usd",
    "carbon_annual_usd",
    "ptc_annual_usd",
    "co2_annual_tonnes",
    "it_energy_annual_MWh",
    "cool_energy_annual_MWh",
    "Q_abs_cool_annual_MWh",
    "P_grid_buy_annual_MWh",
    "P_grid_sell_annual_MWh",
    "epbt_years",
    "water_total_l_per_mwh_e",
]

mismatches = []
paths = []
for _, row in master.iterrows():
    p = OUTPUTS / row["group"] / row["run_id"] / "summary.json"
    paths.append(str(p.relative_to(ROOT)))
    with p.open() as f:
        s = json.load(f)
    for field in CHECK_FIELDS:
        if field not in s:
            continue
        mv, sv = row.get(field), s[field]
        if sv is None and (mv is None or (isinstance(mv, float) and math.isnan(mv))):
            continue
        if isinstance(sv, (int, float)) and isinstance(mv, (int, float)):
            if math.isnan(mv) and sv is not None and math.isnan(float(sv)):
                continue
            denom = max(1.0, abs(float(sv)))
            if abs(float(mv) - float(sv)) / denom > 1e-9:
                mismatches.append(
                    {"run": f"{row['group']}/{row['run_id']}", "field": field,
                     "master": mv, "summary": sv}
                )

# Margin self-consistency: premium == 1 - tac/tac_case0_baseline
bad_margin = []
for _, row in master.iterrows():
    m = 1.0 - row["tac_usd_per_yr"] / row["tac_case0_baseline_usd_per_yr"]
    if abs(m - row["heat_recovery_premium"]) > 1e-9:
        bad_margin.append(f"{row['group']}/{row['run_id']}")

ledger = master.copy()
ledger.insert(0, "scenario_group_paper", ledger["group"].map({
    "main_baseline": "G0", "s1_pue": "G1", "s2_price": "G2",
    "s3_battery": "G3", "s4_capex": "G4", "s5_feasibility_2d": "G5",
    "s6_carbon_price": "G6", "s7_wacc": "G7", "s8_size_matching": "G8",
}))
ledger["output_file"] = paths
# Effective reactor capital of each run, resolved: explicit S5 value, else
# the named scenario anchor, else the plant-yaml ATB-Mid default.
_SCEN = {"FOAK": 14700.0, "ATB_Mid": 7615.0, "NOAK": 2250.0}
ledger["reactor_capex_effective_usd_per_kwe"] = [
    row["smr_capex_usd_per_kWe"]
    if not (isinstance(row["smr_capex_usd_per_kWe"], float)
            and math.isnan(row["smr_capex_usd_per_kWe"]))
    else _SCEN.get(row["reactor_scenario"],
                   7615.0 if row["case_id"] in (1, 2) else float("nan"))
    for _, row in ledger.iterrows()
]

ledger.to_csv(AUDIT / "ledger_full.csv", index=False)

summary = {
    "rows": len(ledger),
    "master_vs_summary_mismatches": mismatches,
    "margin_inconsistencies": bad_margin,
}
with (AUDIT / "ledger_crosscheck.json").open("w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2)[:2000])
print("ledger written:", AUDIT / "ledger_full.csv")
