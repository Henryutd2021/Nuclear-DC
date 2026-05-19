"""Fetch ERCOT Day-Ahead Settlement Point Prices for 2022-2024 via gridstatus.

Outputs:
  data/ercot/{year}_dam_spp_all.csv.gz    — all hubs/zones, full year hourly
  data/ercot/{year}_dam_lmp_houston.csv   — HB_HOUSTON only, simplified for optimizer
  data/ercot/dam_summary.csv              — annual mean/std/percentiles per hub

Provenance: ERCOT Market Information System (MIS), public reports NP4-183-CD
(DAM Settlement Point Prices), accessed via gridstatus Python package.

Citation: gridstatus 0.30.1 — https://github.com/gridstatus/gridstatus
ERCOT MIS: https://www.ercot.com/mp/data-products/data-product-details?id=NP4-183-CD
"""
from pathlib import Path
import gridstatus
import pandas as pd
import numpy as np
import sys

DATA_DIR = Path(__file__).resolve().parents[1] / "ercot"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HUBS = ["HB_HOUSTON", "HB_NORTH", "HB_SOUTH", "HB_WEST", "HB_BUSAVG", "HB_HUBAVG"]

iso = gridstatus.Ercot()
all_years = []

for year in [2022, 2023, 2024]:
    print(f"[ERCOT] Fetching DAM SPP for {year}...", flush=True)
    df = iso.get_dam_spp(year=year)
    df = df.rename(columns={"SPP": "price_usd_per_mwh"})
    out_path = DATA_DIR / f"{year}_dam_spp_all.csv.gz"
    df.to_csv(out_path, index=False, compression="gzip")
    print(f"  saved {out_path.name}: {len(df):,} rows, {out_path.stat().st_size/1e6:.1f} MB on disk", flush=True)

    # Extract HB_HOUSTON hourly (primary anchor for paper)
    hou = df[df["Location"] == "HB_HOUSTON"].copy()
    hou = hou.sort_values("Interval Start").reset_index(drop=True)
    hou["hour"] = np.arange(len(hou))
    hou["datetime_utc"] = pd.to_datetime(hou["Interval Start"]).dt.tz_convert("UTC")
    hou_out = hou[["hour", "datetime_utc", "price_usd_per_mwh"]]
    hou_csv = DATA_DIR / f"{year}_dam_lmp_houston.csv"
    hou_out.to_csv(hou_csv, index=False)
    print(f"  saved {hou_csv.name}: {len(hou_out):,} hours", flush=True)

    # Annual summary per hub
    agg = df.groupby("Location")["price_usd_per_mwh"].agg(
        ["count", "mean", "std", "min",
         lambda s: s.quantile(0.05),
         lambda s: s.quantile(0.50),
         lambda s: s.quantile(0.95),
         lambda s: s.quantile(0.99),
         "max"]
    )
    agg.columns = ["count", "mean", "std", "min", "p05", "p50", "p95", "p99", "max"]
    agg["year"] = year
    agg = agg.reset_index()
    all_years.append(agg)

summary = pd.concat(all_years, ignore_index=True)
summary = summary[summary["Location"].isin(HUBS)]
summary.to_csv(DATA_DIR / "dam_summary.csv", index=False)
print("\n=== DAM SUMMARY (HB_HOUSTON) ===", flush=True)
print(summary[summary["Location"] == "HB_HOUSTON"].to_string(index=False), flush=True)
print("[ERCOT] Done.", flush=True)
