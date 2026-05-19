"""Build primary data/ambient.csv and data/price_grid.csv bridge files.

These two top-level files are what src/io_data.py expects to find directly.
They are bridges from the year-specific REAL data in data/weather/ and data/ercot/.

Default year: 2024 (current paper baseline). Switch with --year to use 2022 or 2023
for the S2 ERCOT price-regime sensitivity.

Inputs:
  data/weather/houston_ambient_{year}.csv   (REAL Open-Meteo ERA5 hourly)
  data/ercot/{year}_dam_lmp_houston.csv     (REAL ERCOT DAM SPP)

Outputs:
  data/ambient.csv       — (hour, wet_bulb_C)
  data/price_grid.csv    — (hour, price_import, price_export)

Both are simply slices of the REAL upstream files. No synthesis.
"""
from pathlib import Path
import pandas as pd
import argparse

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=2024,
                    help="Year to bridge for ambient + price_grid (2022/2023/2024)")
args = parser.parse_args()
YEAR = args.year

# ----------------------------------------------------------------------
# 1) ambient.csv from weather/houston_ambient_{year}.csv (REAL Open-Meteo)
# ----------------------------------------------------------------------
wx_path = ROOT / "weather" / f"houston_ambient_{YEAR}.csv"
if not wx_path.exists():
    raise FileNotFoundError(
        f"{wx_path} missing — run data/_raw/fetch_open_meteo_houston.py first.")
wx = pd.read_csv(wx_path)
wx = wx.iloc[:8760].reset_index(drop=True)
wx["hour"] = range(len(wx))
ambient_out = ROOT / "ambient.csv"
wx[["hour", "wet_bulb_C"]].assign(
    wet_bulb_C=lambda d: d["wet_bulb_C"].round(2)
).to_csv(ambient_out, index=False)
print(f"saved {ambient_out}: 8760 rows, REAL wet-bulb from Open-Meteo {YEAR}, "
      f"range [{wx['wet_bulb_C'].min():.1f}, {wx['wet_bulb_C'].max():.1f}] °C")

# ----------------------------------------------------------------------
# 2) price_grid.csv from ercot/{year}_dam_lmp_houston.csv (REAL ERCOT DAM)
# ----------------------------------------------------------------------
dam_file = ROOT / "ercot" / f"{YEAR}_dam_lmp_houston.csv"
if not dam_file.exists():
    raise FileNotFoundError(
        f"{dam_file} missing — run data/_raw/fetch_ercot_dam.py first.")
df = pd.read_csv(dam_file)
df = df.iloc[:8760].copy()
out = pd.DataFrame({
    "hour": range(8760),
    "price_import": df["price_usd_per_mwh"].values.round(2),
    "price_export": df["price_usd_per_mwh"].values.round(2),
})
# Convention for src/io_data.py validator (paper main run):
#   - Import: cannot be negative (we don't get paid to import). Clip ≥ 0.
#   - Export: cannot be negative either (validator requires ≥ 0).
# To analyze pure negative-price events as a sensitivity, use
# data/ercot/{year}_dam_lmp_houston.csv directly (preserves true ERCOT values).
n_neg = int((df["price_usd_per_mwh"] < 0).sum())
out["price_import"] = out["price_import"].clip(lower=0)
out["price_export"] = out["price_export"].clip(lower=0)
if n_neg > 0:
    print(f"   note: {n_neg} negative-price hour(s) clipped to 0 for validator compat.")
price_out = ROOT / "price_grid.csv"
out.to_csv(price_out, index=False)
print(f"saved {price_out}: 8760 rows from ERCOT {YEAR} HB_HOUSTON DAM SPP, "
      f"mean = ${out['price_import'].mean():.2f}/MWh")
