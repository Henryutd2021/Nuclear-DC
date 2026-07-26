"""Task C5 — weather-year / carbon-intensity-year pairing audit.

Code evidence (src/data.py:load_time_series, lines 115-148): every run's
TimeSeries loads
    data/weather/houston_ambient_{year}.csv
    data/ercot/{year}_dam_lmp_houston.csv
    data/environmental/ercot_carbon_intensity_hourly_{year}.csv
keyed by the market year, i.e. price, weather and carbon are co-sampled
per year (the IT trace is the 2018 measurement circularly day-shifted to
align weekday phase with each market year, data.py lines 43-60, 126-131).

This script quantifies the crystallization-gate exposure per weather year:
gate engages when T_wb + dT_cw > T_cry with dT_cw = 5 K, T_cry = 34 C
(config/plant_case2.yaml), i.e. T_wb > 29 C, plus the whole refueling
outage window (builder.py). Counts are reported for the raw weather gate
alone and for gate-hours outside the outage window.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data import load_time_series  # noqa: E402
from src.milp.builder import _outage_hours  # noqa: E402

T_CRY = 34.0
DT_CW = 5.0
GATE_WB = T_CRY - DT_CW  # 29 C

out = {
    "weather_pairing": "per-year",
    "evidence_file_and_lines": (
        "src/data.py:116-148 (load_time_series builds per-year paths "
        "houston_ambient_{year}.csv / {year}_dam_lmp_houston.csv / "
        "ercot_carbon_intensity_hourly_{year}.csv); scripts/run_all_analyses.py:468 "
        "passes spec.year for every run; data/weather holds houston_ambient_"
        "2022/2023/2024.csv (all present and loaded)."
    ),
    "carbon_intensity_pairing": "per-year",
    "gate_hours": {},
    "gate_hours_outside_outage": {},
    "wetbulb_peak_c": {},
    "gate_hours_by_month": {},
    "it_load_alignment_note": (
        "The IT trace is a calendar-2018 measurement; src/data.py:43-60 "
        "circularly shifts it by whole days per market year so weekday phase "
        "matches that year's calendar. Prices/weather/carbon are therefore "
        "co-sampled per year while the workload is a phase-aligned proxy."
    ),
}

outage = _outage_hours(0.92, 8760)
for year in (2022, 2023, 2024):
    ts = load_time_series(project_root=ROOT, year=year, num_hours=8760)
    wb = ts.wet_bulb_C
    gate = wb + DT_CW > T_CRY
    out["gate_hours"][str(year)] = int(gate.sum())
    out["gate_hours_outside_outage"][str(year)] = int(
        sum(1 for t, g in enumerate(gate) if g and t not in outage)
    )
    out["wetbulb_peak_c"][str(year)] = float(wb.max())
    by_month = {}
    for t in wb.index[gate]:
        m = 1 + int(t // 730)  # coarse month bucket for reporting only
        by_month[m] = by_month.get(m, 0) + 1
    out["gate_hours_by_month"][str(year)] = by_month

audit_dir = ROOT / "submission_audit" / "audit"
audit_dir.mkdir(parents=True, exist_ok=True)
with (audit_dir / "C5_results.json").open("w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
