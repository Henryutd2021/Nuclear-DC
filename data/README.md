# Nuclear-DC Data Inventory

Project data folder for the Nuclear-DC Heat-Recovery Premium paper
(Applied Energy target, BWRX-300 + ERCOT Houston anchor case).

## How to get the data

The data folder uses a **three-tier strategy** to keep the git repo clean
while preserving full reproducibility:

| Tier | What | Where | How to obtain |
|---|---|---|---|
| **1** | Tracked in git (~550 KB) | YAMLs, scripts, perf curves, 3 bridge CSVs, docs | Already in repo — `git clone` is enough for main case |
| **2** | Regenerable from public sources (~36 MB) | ERCOT historical, weather, hourly carbon, workload aggregates, Henry Hub daily | `make data` (~10 min) |
| **3** | Third-party manual download (1 GB) | NLR AI workload raw 1-minute profiles | `make data-tier3` for instructions |

### Fresh clone workflow

```bash
git clone https://github.com/[author]/Nuclear-DC.git
cd Nuclear-DC

# Optional but recommended — regenerate Tier 2 data (ERCOT, EIA, weather, etc.)
make data

# Optional — instructions for the NLR AI workload dataset (Tier 3)
make data-tier3

# Run a smoke test (from the repo root)
python3 -c "from pathlib import Path; from src.data import load_time_series; \
            ts = load_time_series(Path('.'), year=2023, num_hours=8760); \
            print('OK', ts.num_hours)"
```

**Without `make data`:** everything runs. The eleven 8760-h CSVs that
`src/data.py` reads (workload 60u aggregate, per-year DAM LMP / ambient /
carbon intensity, Henry Hub daily) are tracked in git alongside all YAMLs;
`make data` only regenerates them from the raw sources, and the workload
aggregate additionally needs the Tier 3 NLR download.

## Folder layout

```
data/
├── README.md                  ← you are here
├── SOURCES.md                 ← authoritative provenance / citation registry
├── MANUAL_COLLECTION.md       ← optional manual replacements (WattTime, NSRDB, etc.)
│
├── it_load.csv                ← Tier 1: 200 MW DC IT load, 8760 h, REAL (NLR scaled)
├── ambient.csv                ← Tier 1: Houston wet-bulb, 8760 h, REAL (Open-Meteo 2024)
├── price_grid.csv             ← Tier 1: ERCOT HB_HOUSTON DAM 2024, 8760 h, REAL
│
├── reactor/                   ← Tier 1: BWRX-300 YAMLs (technical + 3-tier economic)
├── equipment/                 ← Tier 1: ORC, absorption, NGCC, BESS YAMLs
├── perf/                      ← Tier 1: Performance curves (derived from public formulas)
├── environmental/             ← Tier 1 YAMLs + summary CSVs; Tier 2 hourly CSVs
├── economics/                 ← Tier 1 YAMLs + summaries; Tier 2 Henry Hub daily
├── workload/
│   ├── profile_stats.yaml     ← Tier 1
│   ├── dc_200mw_real_*u.csv   ← Tier 2 (regen from NLR raw)
│   ├── cooling_load_*.csv     ← Tier 2 (regen from IT load × PUE)
│   └── raw_nlr_colocation/    ← Tier 3 manual download (NLR DOI 10.7799/3025227)
├── ercot/                     ← Tier 1 summary CSVs; Tier 2 full 3-year LMP + EIA-930
├── weather/                   ← Tier 1 SOURCES.yaml; Tier 2 Open-Meteo hourly CSVs
└── _raw/                      ← Tier 1: All fetch/build scripts
```

## Quick-start: load a paper case

```python
from pathlib import Path
import pandas as pd

DATA = Path("data")

# Primary 8760-h time series (Tier 1, always present)
it_load    = pd.read_csv(DATA / "it_load.csv")
ambient    = pd.read_csv(DATA / "ambient.csv")
price_grid = pd.read_csv(DATA / "price_grid.csv")

# After `make data` — switch ERCOT year for S2 sensitivity
year = 2023   # 2022 / 2023 / 2024
da_lmp = pd.read_csv(DATA / f"ercot/{year}_dam_lmp_houston.csv")
rt_lmp = pd.read_csv(DATA / f"ercot/{year}_rtm_lmp_houston_hourly.csv")

# Switch PUE for S1 sensitivity — pass to load_time_series, or use:
pue = "pue110"   # pue110 / pue130 / pue150  (Tier 2; or io_data.py derives from PUE param)
cooling = pd.read_csv(DATA / f"workload/cooling_load_{pue}.csv")

# Hourly grid carbon intensity (Tier 2 after `make data`)
ci = pd.read_csv(DATA / f"environmental/ercot_carbon_intensity_hourly_{year}.csv")
```

## Switching the paper-baseline year

```bash
python3 data/_raw/build_ambient_and_price_bridge.py --year 2022   # or 2023 / 2024
```

This regenerates `data/ambient.csv` and `data/price_grid.csv` from the
specified year's Tier-2 data.

## Sensitivity dimensions (5 mapped to data)

| Dim | Variable | Data files / config |
|---|---|---|
| **S1** | Effective full-load PUE {1.10, 1.30, 1.50} | VCC COP override via `with_cooling_cop()`; legacy `workload/cooling_load_pue{110,130,150}.csv` files are retained only for audit history |
| **S2** | ERCOT regime {2022/2023/2024} | `ercot/{year}_dam_lmp_houston.csv` (Tier 2) + `build_ambient_and_price_bridge.py --year` |
| **S3** | BESS on/off | `equipment/bess_liion.yaml` + flag in `config/plant_case*.yaml` |
| **S4** | CAPEX {FOAK/Mid/NOAK} | `reactor/bwrx300_economic.yaml.scenarios.*` |
| **S5** | SMR × absorption CAPEX 5×5 grid | `config/capex_grid_s5.yaml` (SMR $2,250–14,700/kWe × absorption $450–1,200/kWth) |

## Disk usage by tier

| Tier | Size | What |
|---|---|---|
| 1 (tracked in git) | ~560 KB | YAMLs + scripts + 3 bridge CSVs + perf + summaries + docs |
| 2 (regen via `make data`) | ~36 MB | ERCOT historical, weather, hourly carbon, workload aggregates, Henry Hub daily |
| 3 (manual NLR download) | ~226 MB | NLR 1-minute raw profiles (audit trail; aggregates in Tier 2 are sufficient for paper) |

## Citing this dataset

Every numerical value traces:

```
paper.tex citation → SOURCES.md entry → original publisher URL
```

The reference list in [SOURCES.md §11](SOURCES.md#11-citation-bundle--paper-ready-reference-list)
is organized for direct BibTeX export. License & attribution per upstream
source is in [../LICENSES.md](../LICENSES.md).

## Maintainer notes

- Last update: 2026-05-19 (full real-data refresh + three-tier reorganization)
- All build/fetch scripts under `data/_raw/` are idempotent and safe to re-run
- `make data-clean` removes Tier 2 + Tier 3 but preserves Tier 1
- For paper submission: archive a full Tier 1+2+3 snapshot on Zenodo and cite
  the DOI in the manuscript's Data Availability statement (template in
  [../LICENSES.md](../LICENSES.md))
- Maintainer: lihonglin998@gmail.com
