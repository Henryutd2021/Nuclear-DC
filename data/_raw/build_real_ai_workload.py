"""Build REAL AI data-center IT load by scaling + aggregating NLR whole-facility
profiles (arxiv 2604.07345 / DOI 10.7799/3025227).

Source dataset: Vercellino et al. 2026, "Measurement of Generative AI Workload
Power Profiles for Whole-Facility Data Center Infrastructure Planning".
Raw zip: data/_raw/ai_workload_dataset.zip (1.07 GB)
Extracted: data/_raw/nlr_extract/03_whole-facility_profiles/

Source profile characteristics (NLR/Kestrel HPC + DIPLOEE simulation):
  - Time span: 2018-01-01 to 2019-01-01 (one full year)
  - Resolution: 1 minute (525,601 timestamps × four utilization variants)
  - Profile: 10 MW colocation facility with 2840 nodes (HPC + GenAI mixed)
  - Utilization variants: 20%, 40%, 60%, 80%

Transformation:
  1. Take colocation_10MW @ 60u variant as paper baseline (matches hyperscale AI)
  2. Scale by 20× to map 10 MW → 200 MW nameplate IT capacity
  3. Aggregate 1-min → 1-hour by mean (525,600 → 8760 rows)

Outputs:
  data/workload/dc_200mw_real_60u_2018.csv             — baseline IT load profile
  data/workload/dc_200mw_real_{u}u_2018.csv            — for each utilization (20/40/60/80)
  data/workload/cooling_load_pue{110,130,150}.csv     — legacy derived PUE-load files
  data/it_load.csv                                      — primary, copied from 60u

This REPLACES the previous synthetic archetype with REAL measurement-derived data.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

OUT = Path(__file__).resolve().parents[1] / "workload"
OUT.mkdir(parents=True, exist_ok=True)
DATA_ROOT = OUT.parent

NLR_DIR = Path(__file__).resolve().parents[1] / "workload/raw_nlr_colocation"
NAMEPLATE_TARGET_MW = 200    # paper target (10 MW × 20 = 200 MW)
ETA_CHAIN = 0.9

results = {}
for u in ["20u", "40u", "60u", "80u"]:
    src = NLR_DIR / f"colocation_10MW_2840nodes_{u}_power.csv"
    df = pd.read_csv(src, parse_dates=["timestamp"])
    # Scale 10 MW → 200 MW by ×20
    df["IT_load_MW"] = (df["power_W"] / 1e6) * 20
    # Aggregate to hourly
    df = df.set_index("timestamp")
    hourly = df["IT_load_MW"].resample("1h").mean()
    hourly = hourly.iloc[:8760]   # ensure 8760
    out_df = pd.DataFrame({
        "hour": range(len(hourly)),
        "timestamp_local": hourly.index,
        "IT_load_MW": hourly.values.round(2),
    })
    out_path = OUT / f"dc_200mw_real_{u}_2018.csv"
    out_df.to_csv(out_path, index=False)
    results[u] = {
        "mean_MW": float(hourly.mean()),
        "min_MW": float(hourly.min()),
        "max_MW": float(hourly.max()),
        "std_MW": float(hourly.std()),
        "rows": int(len(hourly)),
        "csv": out_path.name,
    }
    print(f"  {u}: rows={len(hourly)}, mean={hourly.mean():.1f} MW, max={hourly.max():.1f} MW")

# Choose 60u as paper baseline (matches typical hyperscale AI DC utilization)
baseline_csv = OUT / "dc_200mw_real_60u_2018.csv"
baseline = pd.read_csv(baseline_csv)
baseline[["hour", "IT_load_MW"]].to_csv(DATA_ROOT / "it_load.csv", index=False)
print(f"\nPrimary data/it_load.csv updated from REAL 60u profile.")

# Cooling load variants (3 PUE)
it_mw = baseline["IT_load_MW"].values
for pue, label in [(1.10, "pue110"), (1.30, "pue130"), (1.50, "pue150")]:
    q_cool = ((pue - 1.0) * it_mw / ETA_CHAIN).round(2)
    out_df = pd.DataFrame({
        "hour": range(8760),
        "timestamp_local": baseline["timestamp_local"],
        "cooling_load_MWth": q_cool,
    })
    p = OUT / f"cooling_load_{label}.csv"
    out_df.to_csv(p, index=False)
    print(f"  {p.name}: PUE={pue}, mean={q_cool.mean():.1f}, max={q_cool.max():.1f}")

# Updated stats YAML
stats = {
    "profile": {
        "nameplate_it_capacity_MW": NAMEPLATE_TARGET_MW,
        "workload_archetype": "10 MW NLR colocation facility (HPC + GenAI mixed) × 20 scale",
        "data_origin": "REAL — NLR/Kestrel HPC measurements + DIPLOEE simulation",
        "scaling_method": "Multiply 10 MW profile by 20× to reach 200 MW IT nameplate",
        "aggregation": "1-min → 1-hour by mean",
        "year_of_measurement": 2018,
        "paper_baseline_utilization": "60u (60% — matches hyperscale AI DC)",
        "alternative_utilizations_available": ["20u", "40u", "60u", "80u"],
    },
    "statistics_per_utilization": results,
        "pue_variants_legacy": {
        "pue_110": {
            "description": "Hyperscale direct-liquid-cooling (Google fleet 2024, Meta tier-1)",
            "cooling_load_mean_MWth": round((0.10 / 0.9) * results["60u"]["mean_MW"], 1),
            "cooling_load_max_MWth": round((0.10 / 0.9) * results["60u"]["max_MW"], 1),
        },
        "pue_130": {
            "description": "Modern enterprise air+liquid hybrid",
            "cooling_load_mean_MWth": round((0.30 / 0.9) * results["60u"]["mean_MW"], 1),
            "cooling_load_max_MWth": round((0.30 / 0.9) * results["60u"]["max_MW"], 1),
        },
        "pue_150": {
            "description": "Traditional air-cooled DC (pre-AI legacy)",
            "cooling_load_mean_MWth": round((0.50 / 0.9) * results["60u"]["mean_MW"], 1),
            "cooling_load_max_MWth": round((0.50 / 0.9) * results["60u"]["max_MW"], 1),
        },
    },
    "sources": [
        {
            "id": "Vercellino-2026-arxiv",
            "title": "Measurement of Generative AI Workload Power Profiles for Whole-Facility Data Center Infrastructure Planning",
            "authors": "Vercellino, Willard, Campos, da Silva Pereira, Hull, Selensky, Mueller",
            "publisher": "arXiv preprint, National Laboratory of the Rockies",
            "year": 2026,
            "arxiv_id": "2604.07345",
            "url": "https://arxiv.org/abs/2604.07345",
            "used_for": "Real GenAI workload power profiles methodology",
        },
        {
            "id": "NLR-DataCatalog-3025227",
            "title": "Dataset of Generative AI Workload Power Profiles",
            "publisher": "National Laboratory of the Rockies, NLR Data Catalog",
            "year": 2026,
            "doi": "10.7799/3025227",
            "url": "https://data.nlr.gov/submissions/312",
            "license": "Public dataset (see landing page)",
            "used_for": "Whole-facility 1-min power profile for 10 MW colocation × 4 utilization levels",
        },
    ],
}

with open(OUT / "profile_stats.yaml", "w") as f:
    yaml.dump(stats, f, sort_keys=False, default_flow_style=False)
print("\nWrote workload/profile_stats.yaml (REAL data version)")

# Remove the old archetype synthetic file
old = OUT / "dc_200mw_h100_archetype.csv"
if old.exists():
    old.unlink()
    print(f"Deleted obsolete synthetic file: {old.name}")
