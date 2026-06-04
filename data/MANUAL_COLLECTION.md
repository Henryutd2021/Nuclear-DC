# Manual Data Collection — Optional Replacements

**As of 2026-05-19:** All mandatory data is **REAL** and traced to authoritative
sources (see [SOURCES.md](SOURCES.md)). This document lists **optional**
replacements that could marginally improve fidelity for the paper. None are
blocking for the AE submission.

---

## 1. WattTime Marginal Operating Emissions Rate (MOER) — Optional

**What it adds:** Replaces the AEF (average emission factor) hour-of-day shape
derived from EIA-930 with MEF (marginal emission factor) at 5-minute resolution.
MEF is more accurate for "displacement" accounting (the headline KPI
"carbon abatement cost").

**Current fallback:** AEF computed from real EIA-930 generation mix × UNECE LCA
factors. AEF slightly underestimates abatement vs MEF (by ~5-15% typically).

**Steps to obtain:**

1. Apply for WattTime academic API access:
   - URL: https://www.watttime.org/api-documentation/
   - Click "Apply for Academic Access"
   - Approval typically 1-2 business days
   - Free for research use
2. Download data for BAs `ERCOTC` (Central) and `ERCOTH` (Houston) for
   2022-2024 hourly MOER.
3. Save to `data/environmental/watttime_moer_houston_{year}.csv`.
4. Update `data/environmental/grid_carbon_avert.yaml`:
   - Replace `hour_of_day_shape.ercot_aef_3yr_mean.multiplier_by_hour` with
     the MOER-derived hourly multipliers.
   - Update `sources:` to include the WattTime citation.
5. Re-run the paper's carbon accounting.

**Expected impact:** Heat-Recovery Premium might shift by ±5-10% on the carbon
component of TAC; will not change the qualitative finding.

---

## 2. NLR ATB 2024 Raw CSV Files — Optional

**What it adds:** The complete cost and performance CSV tables that NLR ATB
publishes for the manuscript SI appendix's "input data audit trail". The
specific values used in the paper are already in our YAMLs (`reactor/`,
`equipment/`), so this is purely for the SI completeness section.

**Steps to obtain:**

1. Visit NLR ATB 2024 download page: https://atb.nlr.gov/electricity/2024/data
2. Download CSV files for:
   - **Nuclear (SMR):** https://atb.nrel.gov/electricity/2024/nuclear
   - **Natural Gas:** https://atb.nrel.gov/electricity/2024/natural_gas
   - **Battery Storage:** https://atb.nrel.gov/electricity/2024/utility-scale_battery_storage
   - **Geothermal (Binary):** https://atb.nrel.gov/electricity/2024/geothermal
3. Save raw CSVs to `data/economics/nrel_atb_2024_raw/`.
4. The specific values used in our YAMLs are already cited and traceable,
   so the raw CSVs are SI-only (manuscript appendix Table SI-1).

---

## 3. Alternative AI Workload Datasets — Optional

The paper baseline uses the **NLR/Vercellino 2026 dataset** (arxiv 2604.07345)
which is the source explicitly cited in the project plan. No replacement
needed. However, if a Discussion §5.X comparison is desired, these are
publicly available alternatives:

### 3a. Google Cluster Data v3 (Borg traces)
- URL: https://github.com/google/cluster-data
- Resolution: 5-minute, ~58 power domains × 8 cells
- 2019 May (1-month trace), gigantic but representative for hyperscale CPU+GPU mix
- License: CC-BY 4.0

### 3b. Azure Public Dataset (VM traces)
- URL: https://github.com/Azure/AzurePublicDataset
- Resolution: 5-minute, multiple workload types
- 2017 and 2019 traces available

### 3c. LBNL Shehabi 2024 Aggregate
- URL: https://datacenters.lbl.gov/sites/default/files/2024-12/lbnl-2024-united-states-data-center-energy-usage-report.pdf
- This is a national aggregate report, not a hourly time series, but it's
  the authoritative source for the "200 MW hyperscale AI DC" framing
  context.

These are listed only for the Discussion comparison; the primary anchor case
already uses NLR real data.

---

## 4. NREL NSRDB Houston Hourly Observations — Optional Cross-Check

The Open-Meteo Houston weather we use is ERA5 reanalysis (high-quality but
not station-level observations). NSRDB provides station-level hourly data
which can be used as a sanity check or higher-fidelity alternative.

**Steps to obtain:**

1. Get free NREL API key: https://developer.nrel.gov/signup/
   (instant approval)
2. NSRDB Viewer: https://maps.nrel.gov/nsrdb-viewer/
3. Pull hourly TMY3 or 2022-2024 actual for Houston (lat 29.76, lon -95.37).
4. Save to `data/weather/nsrdb_houston_{year}.csv`.
5. Compare to Open-Meteo wet-bulb to confirm match (expected within 1-2 K).

**Expected impact:** Negligible; ERA5 reanalysis matches station observations
within ~1.5 K RMSE for Houston temperature variables. We use Open-Meteo as
the primary because it is easier to access and well-cited in research.

---

## 5. ERCOT Long-Term Load Forecast (35 GW DC by 2035) — Optional

For Discussion §5.X (deployment context, ERCOT growth narrative).

**Where to find:**
- ERCOT Long-Term Reliability Reports: https://www.ercot.com/gridmktinfo/planning
- ERCOT 2024 Long-Term Load Forecast (December 2024 published version)
- EIA Annual Energy Outlook 2025 (state-level Texas projections)

**Use:** Cited in §5.X as deployment context; no numerical data needed in
optimization. Reference URL in Discussion is sufficient.

---

## Priority Summary

| Item | Replaces | Priority | Time required |
|---|---|---|---|
| 1. WattTime MOER | EIA-930 AEF hour-of-day shape | Low | 1-2 days application + 1 hour processing |
| 2. NLR ATB raw CSVs | (nothing — adds SI completeness) | Low | 30 min |
| 3. Alt AI workloads | (already have NLR real) | Optional | 1 day each |
| 4. NSRDB observations | Open-Meteo ERA5 | Optional | 30 min + API key |
| 5. ERCOT load forecast | (Discussion narrative only) | Optional | 1 hour |

**None are blocking.** The paper can be submitted with the current data; all
optional replacements would marginally tighten specific results or add
manuscript SI completeness.

---

*Last updated: 2026-05-19.*
