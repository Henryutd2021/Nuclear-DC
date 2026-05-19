"""Fetch ERCOT Real-Time Market Settlement Point Prices (15-min) 2022-2024.

Aggregates 15-min RT-SPP to hourly mean/min/max/std (captures intra-hour
volatility for paper SI / S2 sensitivity-regime physical-basis check).

Outputs:
  data/ercot/{year}_rtm_spp_all.csv.gz             — all hubs/zones 15-min
  data/ercot/{year}_rtm_lmp_houston_hourly.csv     — HB_HOUSTON hourly aggregate
  data/ercot/rtm_summary.csv                       — annual stats per hub

Source: ERCOT MIS Settlement Point Prices at Hubs and Load Zones (NP6-905-CD),
accessed via gridstatus Python package.
"""
from pathlib import Path
import gridstatus
import pandas as pd
import numpy as np
import time

DATA_DIR = Path(__file__).resolve().parents[1] / "ercot"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HUBS = ["HB_HOUSTON", "HB_NORTH", "HB_SOUTH", "HB_WEST", "HB_BUSAVG", "HB_HUBAVG"]

iso = gridstatus.Ercot()
all_year_summaries = []

for year in [2022, 2023, 2024]:
    print(f"\n[ERCOT-RTM] year {year}", flush=True)
    t0 = time.time()
    df = iso.get_rtm_spp(year=year)
    print(f"  pulled {len(df):,} 15-min rows in {time.time()-t0:.0f}s", flush=True)

    df = df.rename(columns={"SPP": "price_usd_per_mwh"})
    df["Interval Start"] = pd.to_datetime(df["Interval Start"])

    # Save full raw csv.gz
    out_path = DATA_DIR / f"{year}_rtm_spp_all.csv.gz"
    df.to_csv(out_path, index=False, compression="gzip")
    print(f"  saved {out_path.name}: {out_path.stat().st_size/1e6:.1f} MB", flush=True)

    # Aggregate HB_HOUSTON to hourly
    hou = df[df["Location"] == "HB_HOUSTON"].copy()
    hou = hou.set_index("Interval Start").sort_index()
    hourly = hou["price_usd_per_mwh"].resample("1h").agg(["mean", "min", "max", "std", "count"])
    hourly = hourly.reset_index().rename(columns={"Interval Start": "timestamp_utc",
                                                  "mean": "rt_lmp_mean", "min": "rt_lmp_min",
                                                  "max": "rt_lmp_max", "std": "rt_lmp_std",
                                                  "count": "intervals_in_hour"})
    hourly["hour"] = np.arange(len(hourly))
    hourly = hourly[["hour", "timestamp_utc", "rt_lmp_mean", "rt_lmp_min", "rt_lmp_max", "rt_lmp_std", "intervals_in_hour"]]
    hou_path = DATA_DIR / f"{year}_rtm_lmp_houston_hourly.csv"
    hourly.to_csv(hou_path, index=False)
    print(f"  saved {hou_path.name}: {len(hourly):,} hourly rows", flush=True)

    # Annual stats per major hub
    agg = df[df["Location"].isin(HUBS)].groupby("Location")["price_usd_per_mwh"].agg(
        ["count", "mean", "std", "min",
         lambda s: s.quantile(0.05),
         lambda s: s.quantile(0.50),
         lambda s: s.quantile(0.95),
         lambda s: s.quantile(0.99),
         "max"]
    )
    agg.columns = ["count", "mean", "std", "min", "p05", "p50", "p95", "p99", "max"]
    agg["year"] = year
    all_year_summaries.append(agg.reset_index())

summary = pd.concat(all_year_summaries, ignore_index=True)
summary.to_csv(DATA_DIR / "rtm_summary.csv", index=False)
print("\n=== RTM SUMMARY (HB_HOUSTON, hourly basis 15-min mean) ===", flush=True)
print(summary[summary["Location"] == "HB_HOUSTON"].to_string(index=False), flush=True)
print("\n[ERCOT-RTM] Done.", flush=True)
