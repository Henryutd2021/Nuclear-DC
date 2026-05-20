"""Build make_paper_figures.ipynb — one cell per main figure.

Run with:  .venv/bin/python notebooks/build_notebook.py

Produces a notebook with 8 main figures totalling ~20 subpanels:
  Fig 1   = TikZ schematic (hand-drawn, not in this notebook)
  Fig 2   = 3 panels — TAC stack / Premium waterfall / driver tornado
  Fig 3   = 2 panels — cost-carbon scatter / carbon decomposition
  Fig 4   = 4 panels — winter week / summer week / diurnal heatmap / LMP duration
  Fig 5   = 2 panels — PUE line / PUE×Case 2D heatmap
  Fig 6   = 3 panels — Premium by Year×Case / LMP violin / LMP summary stats
  Fig 7   = 2 panels — BESS Premium delta / $/tCO2 avoided
  Fig 8   = 3 panels — CAPEX bar / CAPEX×Case 2D heatmap / sensitivity radar (hero)

Palette + style + helpers all sourced from the personal sci-figure skill
(``~/.claude/skills/sci-figure``).  Per Nature-portfolio convention and the
user's memory ``feedback_no-figure-titles``, NO ``set_title`` / ``suptitle``
calls anywhere; captions own that text.
"""
from __future__ import annotations

from pathlib import Path
import nbformat as nbf


HERE = Path(__file__).resolve().parent
OUT = HERE / "make_paper_figures.ipynb"


def md(src: str):
    return nbf.v4.new_markdown_cell(src)


def code(src: str):
    return nbf.v4.new_code_cell(src)


CELLS = []

# ---- Title ----
CELLS.append(md("""# Nuclear-DC paper figures

One *figure* per cell (each figure may contain 2–4 subpanels).  Driven by:

- `outputs/master_kpi_table.csv` (51 MILP runs)
- `outputs/<group>/<run_id>/dispatch.csv.gz` (8760-hour dispatch)
- `data/ercot/{2022,2023,2024}_rtm_lmp_houston_hourly.csv` (ERCOT LMP)
- `notebooks/figure_helpers.py` → personal **sci-figure** skill at `~/.claude/skills/sci-figure/`

Outputs are written to `outputs/figures/figN_*.{pdf,svg,png}` via the sci-figure `save_triplet` exporter.

**Figure map:**

| # | Panels | Plot types | Role |
|---|---|---|---|
| 2 | a/b/c | stacked bar · waterfall · tornado | Headline |
| 3 | a/b   | Pareto scatter · stacked carbon | Trade-off |
| 4 | a–d   | multi-stream line ×2 · diurnal heatmap · LMP duration | Mechanism |
| 5 | a/b   | line · 2D heatmap | S1 PUE |
| 6 | a/b/c | grouped bar · violin · small stats bar | S2 year |
| 7 | a/b   | paired bar · paired bar | S3 BESS |
| 8 | a/b/c | bar · 2D heatmap · radar | S4 CAPEX (hero) |

**Per sci-figure skill workflow:** every figure uses the NPPH2 palette via `PALETTE`, applies `apply_nature_style()` once at the top of the notebook, and exports via `save_fig`.  Run `colorblind_check.py` and `qa_check.py` on each PNG before declaring final."""))

# ---- Setup cell ----
CELLS.append(code("""# Setup: shared style, palette, master KPI, dispatch loader, LMP loader.
%matplotlib inline
import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

sys.path.insert(0, str(Path.cwd() / "notebooks"))
from figure_helpers import (
    PALETTE, CASE_LABELS, SHORT_LABELS,
    OUTPUTS_DIR, MASTER_CSV, DATA_DIR,
    apply_nature_style, mm, save_fig, premium_color, case_color, panel_label,
    SINGLE_COL_MM, ONE_HALF_COL_MM, DOUBLE_COL_MM,
    tornado, radar, duration_curve, bivariate_heatmap, violin_grouped,
)

apply_nature_style()

def load_dispatch(group: str, run_id: str) -> pd.DataFrame:
    p = OUTPUTS_DIR / group / run_id / "dispatch.csv.gz"
    with gzip.open(p, "rt") as f:
        return pd.read_csv(f)

def load_lmp(year: int) -> np.ndarray:
    p = DATA_DIR / "ercot" / f"{year}_rtm_lmp_houston_hourly.csv"
    return pd.read_csv(p)["rt_lmp_mean"].to_numpy()

df = pd.read_csv(MASTER_CSV)
print(f"Loaded {len(df)} runs across groups: {sorted(df.group.unique())}")
df.head(3)"""))

# ---- Fig 2 (3 panels) ----
CELLS.append(md("""## Fig 2 — TAC stack · Premium waterfall · driver tornado

Three views of the headline economics:

- **a.** TAC stacked by cost component (CAPEX / FOM / VOM / Fuel / Grid net) across the 5 cases.
- **b.** Premium derivation as a waterfall, showing how each cost layer moves the bar from C0 baseline to C2 cogen.
- **c.** Sensitivity tornado: which dimension changes Premium the most?  Computed as `max - baseline` and `min - baseline` along each sensitivity sweep for C2."""))

CELLS.append(code("""# Fig 2 -- TAC stack (a) + Premium waterfall (b) + driver tornado (c)
base = df[df.group == "main_baseline"].sort_values("case_id").reset_index(drop=True)
cases = base["case_id"].to_numpy()
n = len(cases)

layers = {
    "CAPEX":      base["capex_annual_usd"].to_numpy() / 1e6,
    "FOM":        base["fom_annual_usd"].to_numpy() / 1e6,
    "VOM":        base["vom_annual_usd"].to_numpy() / 1e6,
    "Fuel":       base["fuel_annual_usd"].fillna(0.0).to_numpy() / 1e6,
    "Grid (net)": base["grid_annual_usd"].to_numpy() / 1e6,
}
layer_colors = {
    "CAPEX":      PALETTE["capex"],
    "FOM":        PALETTE["fom"],
    "VOM":        PALETTE["vom"],
    "Fuel":       PALETTE["fuel"],
    "Grid (net)": PALETTE["grid_sell"],
}
tac     = base["tac_usd_per_yr"].to_numpy() / 1e6
premium = base["heat_recovery_premium"].to_numpy()

fig = plt.figure(figsize=mm(DOUBLE_COL_MM, 78))
gs = fig.add_gridspec(1, 3, width_ratios=[1.40, 1.05, 1.05],
                      wspace=0.42, left=0.06, right=0.98,
                      top=0.92, bottom=0.18)
axA = fig.add_subplot(gs[0]); axB = fig.add_subplot(gs[1]); axC = fig.add_subplot(gs[2])

# ----- Panel a -- TAC stack ----------------------------------------------
x = np.arange(n); width = 0.62
pos_b = np.zeros(n); neg_b = np.zeros(n)
for name, vals in layers.items():
    pos = np.where(vals > 0, vals, 0)
    neg = np.where(vals < 0, vals, 0)
    axA.bar(x, pos, width, bottom=pos_b, color=layer_colors[name],
            edgecolor="black", linewidth=0.4, label=name)
    axA.bar(x, neg, width, bottom=neg_b, color=layer_colors[name],
            edgecolor="black", linewidth=0.4)
    pos_b += pos; neg_b += neg
axA.scatter(x, tac, marker="D", s=18, color="#222222", zorder=5, label="Net TAC")
for xi, ti in zip(x, tac):
    axA.annotate(f"{ti:.0f}", (xi, ti), xytext=(0, 5), textcoords="offset points",
                 ha="center", fontsize=5.5, color="#222222")
axA.axhline(0, color="#000000", linewidth=0.5)
axA.set_xticks(x); axA.set_xticklabels([SHORT_LABELS[c] for c in cases])
# Extra headroom for legend that sits ABOVE the panel-label band
axA.set_ylim(neg_b.min() * 1.15, pos_b.max() * 1.40)
axA.set_ylabel(r"Annualised cost (M\\$ yr$^{-1}$)")
axA.set_axisbelow(True); axA.grid(axis="y", alpha=0.3, linestyle="--")
# Legend INSIDE the panel (top, single row) so it doesn't collide with "a" label
axA.legend(loc="upper right", ncol=2, fontsize=5.6, handlelength=1.0,
           columnspacing=0.8, handletextpad=0.4, frameon=False)
panel_label(axA, "a", y=1.04)

# ----- Panel b -- Premium waterfall C0 -> C2 (cost-layer decomposition) -
# Build the bridge: starting from C0 TAC, subtract/add each layer's delta
# C2 - C0 to land at C2 TAC.  Then Premium = (C0_TAC - C2_TAC) / C0_TAC.
c0_idx = list(cases).index(0); c2_idx = list(cases).index(2)
c0_tac = tac[c0_idx]; c2_tac = tac[c2_idx]
deltas = {name: vals[c2_idx] - vals[c0_idx] for name, vals in layers.items()}
labels_b  = ["C0 TAC"] + list(deltas.keys()) + ["C2 TAC"]
vals_b    = [c0_tac] + list(deltas.values()) + [c2_tac]
bottoms_b = [0]
running = c0_tac
for v in vals_b[1:-1]:
    bottoms_b.append(running)
    running += v
bottoms_b.append(0)
# Color delta bars by sign (positive cost = salmon; negative = teal)
colors_b = [PALETTE["fill_gray"]]
for v in vals_b[1:-1]:
    colors_b.append(PALETTE["fill_salmon"] if v > 0 else PALETTE["accent_teal"])
colors_b.append(PALETTE["fill_gray"])
xb = np.arange(len(labels_b))
for i, (v, b, c) in enumerate(zip(vals_b, bottoms_b, colors_b)):
    if i == 0 or i == len(labels_b) - 1:
        axB.bar(xb[i], v, color=c, edgecolor="black", linewidth=0.4, alpha=0.85)
    else:
        axB.bar(xb[i], v, bottom=b, color=c, edgecolor="black", linewidth=0.4, alpha=0.85)
# Dashed step connectors between bar tops
for i in range(len(vals_b) - 1):
    if i == 0:
        y_top = vals_b[0]
    elif i == len(vals_b) - 2:
        y_top = bottoms_b[i] + vals_b[i] if vals_b[i] > 0 else bottoms_b[i]
    else:
        y_top = bottoms_b[i] + vals_b[i] if vals_b[i] > 0 else bottoms_b[i]
    axB.plot([xb[i] + 0.4, xb[i+1] - 0.4], [y_top, y_top],
             "k--", alpha=0.4, linewidth=0.6)
axB.set_xticks(xb)
axB.set_xticklabels(labels_b, rotation=30, ha="right", fontsize=6)
axB.set_ylabel(r"TAC (M\\$ yr$^{-1}$)")
axB.set_axisbelow(True); axB.grid(axis="y", alpha=0.3, linestyle="--")
axB.text(0.02, 0.96,
         f"Premium = {(c0_tac - c2_tac) / c0_tac:+.2f}",
         transform=axB.transAxes, fontsize=6.5, fontweight="bold",
         va="top", color=premium_color((c0_tac - c2_tac) / c0_tac),
         bbox=dict(boxstyle="round,pad=0.25", fc="white",
                   ec="#cccccc", linewidth=0.5))
panel_label(axB, "b", y=1.10)

# ----- Panel c -- Driver tornado (sensitivity of Premium for C2) --------
# Compute (min, max) of Premium across each sensitivity sweep, evaluated at
# baseline (year=2023, ATB-Mid, PUE=1.30, BESS=off, eq=baseline) for case 2.
def prem_range(group_name, sweep_col, case=2):
    sub = df[(df.group == group_name) & (df.case_id == case)]
    if len(sub) == 0:
        return (np.nan, np.nan)
    vals = sub["heat_recovery_premium"].dropna().to_numpy()
    return (vals.min(), vals.max())

base_prem = base.loc[base.case_id == 2, "heat_recovery_premium"].iloc[0]

drivers = [
    ("CAPEX (FOAK to NOAK)",  *prem_range("s4_capex",    "reactor_scenario")),
    ("Year (2022 to 2024)",   *prem_range("s2_price",    "year")),
    ("PUE (1.50 to 1.10)",    *prem_range("s1_pue",      "pue")),
    ("BESS (off to on)",      *prem_range("s3_battery",  "bess_applied")),
    ("Equipment (-40% / +40%)", *prem_range("s5_equipment", "equipment_capex_factor")),
]
# Convert to (label, lo, hi) deltas relative to baseline
factors = [(name, lo - base_prem, hi - base_prem) for name, lo, hi in drivers]
factors.sort(key=lambda x: max(abs(x[1]), abs(x[2])), reverse=True)

tornado(axC, factors)
axC.set_xlabel(r"$\\Delta$ Premium vs baseline (C2)", fontsize=6.5)
axC.tick_params(axis="y", labelsize=5.5)
panel_label(axC, "c", y=1.10)

save_fig(fig, "fig2_economics_overview")
fig"""))

# ---- Fig 3 (2 panels) ----
CELLS.append(md("""## Fig 3 — Cost-carbon trade-off + carbon decomposition

- **a.** TAC vs annual CO2 scatter across the 5 cases × 3 ERCOT years (15 points), connected within-case to show the year-driven trajectory.
- **b.** Direct vs lifecycle CO2 emissions decomposition — shows how much of each case's footprint is operational vs. upstream."""))

CELLS.append(code("""# Fig 3 -- Pareto scatter (a) + carbon decomposition (b)
sp = df[df.group == "s2_price"].copy()
sp["tac_M"]  = sp["tac_usd_per_yr"] / 1e6
sp["co2_kt"] = sp["co2_annual_tonnes"] / 1e3

fig, (axA, axB) = plt.subplots(1, 2, figsize=mm(DOUBLE_COL_MM, 78),
                                gridspec_kw={"width_ratios": [1.2, 1.0],
                                             "wspace": 0.32,
                                             "left": 0.06, "right": 0.98,
                                             "top": 0.94, "bottom": 0.15})

# ----- Panel a -- Pareto scatter -----------------------------------------
markers = {2022: "o", 2023: "s", 2024: "^"}
for case_id, sub in sp.groupby("case_id"):
    sub_s = sub.sort_values("year")
    axA.plot(sub_s["co2_kt"], sub_s["tac_M"],
             color=case_color(int(case_id)), linewidth=0.8, alpha=0.6, zorder=2)
    for _, row in sub_s.iterrows():
        axA.scatter(row["co2_kt"], row["tac_M"],
                    marker=markers[int(row["year"])], s=42,
                    color=case_color(int(case_id)),
                    edgecolor="black", linewidth=0.5, zorder=3)
# Direct case labels — anchor table fans out the 3 nuclear cases vertically so
# they don't stack on top of each other at the left cluster.  C0 + C4 sit at
# the right cluster and need horizontal separation only.
label_offsets = {
    0: (40,   8, "left"),   # C0: right cluster, label to its upper-right
    1: (-55, -22, "right"),  # C1: left cluster, label below-left
    2: (-55,   0, "right"),  # C2: left cluster, label at level
    3: (-55, +22, "right"),  # C3: left cluster, label above-left
    4: (40, -10, "left"),   # C4: right cluster, label to its lower-right
}
for case_id, sub in sp.groupby("case_id"):
    sub_s = sub.sort_values("year")
    r23 = sub_s[sub_s.year == 2023].iloc[0]
    dx, dy, ha = label_offsets[int(case_id)]
    axA.annotate(SHORT_LABELS[int(case_id)],
                 xy=(r23["co2_kt"], r23["tac_M"]),
                 xytext=(dx, dy), textcoords="offset points",
                 fontsize=7, fontweight="bold",
                 color=case_color(int(case_id)),
                 ha=ha, va="center",
                 arrowprops=dict(arrowstyle="-", color=case_color(int(case_id)),
                                 linewidth=0.4, alpha=0.7))
axA.axvline(0, color=PALETTE["zero_line"], linewidth=0.4, linestyle="--", alpha=0.7)
axA.set_xlabel(r"Annual CO$_2$ (kt yr$^{-1}$)")
axA.set_ylabel(r"TAC (M\\$ yr$^{-1}$)")
axA.set_axisbelow(True); axA.grid(alpha=0.3, linestyle="--")
year_legend = [plt.Line2D([], [], marker=m, linestyle="", color="#444",
                          markersize=5, label=str(y))
               for y, m in markers.items()]
axA.legend(handles=year_legend, title="ERCOT year",
           loc="lower right", ncol=3, fontsize=5.8, title_fontsize=6,
           handletextpad=0.4, columnspacing=1.0,
           frameon=True, framealpha=0.85, edgecolor="#cccccc")
panel_label(axA, "a", y=1.04)

# ----- Panel b -- CO2 intensity (per MWh-IT) by case --------------------
# Underlying data lacks direct/lifecycle separation for most rows, so we
# show per-unit-IT-energy carbon intensity instead -- a single signed bar
# whose color encodes whether the case emits (salmon) or avoids (teal).
base_b = df[df.group == "main_baseline"].sort_values("case_id").reset_index(drop=True)
co2_kg_per_mwh = base_b["co2_per_mwh_kg"].to_numpy()    # signed
co2_kt_total   = base_b["co2_annual_tonnes"].to_numpy() / 1e3
x = np.arange(len(base_b))
colors_b = [PALETTE["fill_salmon"] if v > 0 else PALETTE["accent_teal"] for v in co2_kg_per_mwh]
axB.bar(x, co2_kg_per_mwh, 0.55, color=colors_b, edgecolor="black", linewidth=0.4)
axB.axhline(0, color="#000000", linewidth=0.5)
# Reference line at ERCOT 2023 mean grid intensity (~370 kg/MWh, set by C0)
axB.axhline(co2_kg_per_mwh[list(base_b.case_id).index(0)],
            color=PALETTE["stroke_clay"], linewidth=0.6, linestyle=":",
            alpha=0.7, label="C0 grid baseline")
axB.set_xticks(x); axB.set_xticklabels([SHORT_LABELS[c] for c in base_b["case_id"]])
axB.set_ylabel(r"CO$_2$ intensity (kg / MWh$_\\mathrm{IT}$)")
axB.set_axisbelow(True); axB.grid(axis="y", alpha=0.3, linestyle="--")
# Each bar: primary intensity label on the OUTER edge; italicised total
# kt-CO2 placed INSIDE the bar near the outer edge so it never collides with
# the x-axis tick labels (which previously happened for the negative-bar cases).
for xi, v, kt in zip(x, co2_kg_per_mwh, co2_kt_total):
    if v >= 0:
        axB.annotate(f"{v:+.0f}", (xi, v), xytext=(0, 5),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=6, fontweight="bold", color="#444")
        axB.annotate(f"({kt:+.0f} kt)", (xi, v), xytext=(0, -10),
                     textcoords="offset points", ha="center", va="top",
                     fontsize=5, style="italic", color="white")
    else:
        axB.annotate(f"{v:+.0f}", (xi, v), xytext=(0, -5),
                     textcoords="offset points", ha="center", va="top",
                     fontsize=6, fontweight="bold", color="#444")
        axB.annotate(f"({kt:+.0f} kt)", (xi, v), xytext=(0, 10),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=5, style="italic", color="white")
axB.legend(loc="upper right", fontsize=5.8, frameon=False, handlelength=1.4)
panel_label(axB, "b", y=1.04)

save_fig(fig, "fig3_cost_carbon")
fig"""))

# ---- Fig 4 (4 panels) ----
CELLS.append(md("""## Fig 4 — Case 2 operational deep dive

Four panels covering the operational mechanism behind Case 2's cogeneration economics:

- **a.** Mid-January week: power streams (IT load + net grid + ORC) and cooling streams (demand + absorption).
- **b.** Mid-July week: same streams, summer regime.
- **c.** 24×365 diurnal heatmap of net grid purchase, revealing the day-of-year × hour-of-day arbitrage signature.
- **d.** ERCOT LMP duration curves for 2022 / 2023 / 2024, showing why the year matters."""))

CELLS.append(code("""# Fig 4 -- 4-panel C2 operational deep dive
disp = load_dispatch("main_baseline", "case2")
week_len = 24 * 7
winter = disp.iloc[24*14 : 24*14 + week_len].reset_index(drop=True)
summer = disp.iloc[24*195: 24*195 + week_len].reset_index(drop=True)

fig = plt.figure(figsize=mm(DOUBLE_COL_MM, 145))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.15], hspace=0.45,
                       wspace=0.22, left=0.07, right=0.98,
                       top=0.96, bottom=0.07)
axA = fig.add_subplot(gs[0, 0]); axB = fig.add_subplot(gs[0, 1])
axC = fig.add_subplot(gs[1, 0]); axD = fig.add_subplot(gs[1, 1])

def draw_week(ax, d):
    h = np.arange(len(d))
    P_net = d["P_grid_buy_MW"] - d["P_grid_sell_MW"]
    ax.plot(h, d["P_IT_MW"], color=PALETTE["P_IT"], linewidth=1.0, label="IT load")
    ax.fill_between(h, 0, P_net, where=(P_net >= 0),
                    color=PALETTE["P_grid_buy"], alpha=0.55, linewidth=0,
                    label="Grid import")
    ax.fill_between(h, 0, P_net, where=(P_net < 0),
                    color=PALETTE["P_grid_sell"], alpha=0.55, linewidth=0,
                    label="Grid export")
    ax.plot(h, d["P_orc_MW"], color=PALETTE["P_orc"], linewidth=0.9,
            linestyle="--", label="ORC")
    ax.axhline(0, color="#666666", linewidth=0.4)
    ax.set_xlim(0, len(d) - 1)
    ax.set_xticks([0, 24, 48, 72, 96, 120, 144, 168])
    ax.set_ylabel("Power (MW)")
    ax.set_axisbelow(True); ax.grid(axis="y", alpha=0.3, linestyle="--")
    for day in range(1, 7):
        ax.axvline(day * 24, color="#dddddd", linewidth=0.3, zorder=0)

draw_week(axA, winter)
draw_week(axB, summer)
axA.set_xlabel("Hour of week (mid-January)")
axB.set_xlabel("Hour of week (mid-July)")
axA.legend(loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=4,
           fontsize=5.8, handlelength=1.2, handletextpad=0.4,
           columnspacing=1.0, frameon=False)
panel_label(axA, "a", y=1.10); panel_label(axB, "b", y=1.10)

# ----- Panel c -- 24x365 diurnal heatmap of net grid (C2, full year) ----
P_net_full = (disp["P_grid_buy_MW"] - disp["P_grid_sell_MW"]).to_numpy()
# Reshape 8760 -> 365 days x 24 hours.
n_days = len(P_net_full) // 24
grid_dh = P_net_full[:n_days * 24].reshape(n_days, 24)
# Saturate at the 5th/95th percentile so the typical-hour variation reads
# clearly instead of being compressed by tail extremes.
cmap_dh = LinearSegmentedColormap.from_list(
    "dh_div", [PALETTE["accent_teal"], "#FFFFFF", PALETTE["fill_salmon"]], N=256)
vlow  = float(np.nanpercentile(grid_dh, 5))
vhigh = float(np.nanpercentile(grid_dh, 95))
vbound = max(abs(vlow), abs(vhigh))
norm_dh = TwoSlopeNorm(vmin=-vbound, vcenter=0, vmax=vbound)
im = axC.imshow(grid_dh.T, aspect="auto", origin="lower", cmap=cmap_dh, norm=norm_dh,
                extent=[0, n_days, 0, 24])
axC.set_xlabel("Day of year")
axC.set_ylabel("Hour of day")
axC.set_xticks([0, 60, 120, 180, 240, 300, 365])
axC.set_yticks([0, 6, 12, 18, 24])
cbar = plt.colorbar(im, ax=axC, label=r"Net grid (MW); $\\leftarrow$ export | import $\\rightarrow$",
                    pad=0.02, shrink=0.85, extend="both")
cbar.ax.tick_params(labelsize=5.5)
panel_label(axC, "c", y=1.04)

# ----- Panel d -- LMP duration curves (2022/2023/2024) -------------------
lmp_series = {
    "2022 (extreme)": (load_lmp(2022), PALETTE["stroke_clay"]),
    "2023 (normal)":  (load_lmp(2023), PALETTE["stroke_teal"]),
    "2024 (cheap)":   (load_lmp(2024), PALETTE["stroke_navy"]),
}
duration_curve(axD, lmp_series, log_y=True)
axD.set_ylabel(r"ERCOT LMP (\\$/MWh)")
axD.legend(loc="upper right", fontsize=6, frameon=False)
panel_label(axD, "d", y=1.04)

save_fig(fig, "fig4_case2_operational")
fig"""))

# ---- Fig 5 (2 panels) ----
CELLS.append(md("""## Fig 5 — S1: PUE sensitivity

- **a.** Premium vs PUE line plot for Cases 1–3, marking the Premium=0 threshold.
- **b.** Joint Premium response across PUE × Case as a 2D heatmap — shows whether PUE_critical depends on case."""))

CELLS.append(code("""# Fig 5 -- PUE line (a) + PUE x Case 2D heatmap (b)
s1 = df[df.group == "s1_pue"].sort_values(["case_id", "pue"])

fig, (axA, axB) = plt.subplots(1, 2, figsize=mm(DOUBLE_COL_MM, 78),
                                gridspec_kw={"width_ratios": [1.1, 1.0],
                                             "wspace": 0.32,
                                             "left": 0.07, "right": 0.97,
                                             "top": 0.92, "bottom": 0.16})

# ----- Panel a -- Premium vs PUE -----------------------------------------
for case_id, sub in s1.groupby("case_id"):
    axA.plot(sub["pue"], sub["heat_recovery_premium"],
             marker="o", markersize=4.5, linewidth=1.2,
             color=case_color(int(case_id)),
             label=SHORT_LABELS[int(case_id)])
# Fan the right-edge labels vertically by Premium-rank so C2 and C3 do not stack.
last_vals = (s1[s1.pue == s1.pue.max()]
             .set_index("case_id")["heat_recovery_premium"]
             .sort_values(ascending=False))
slot = {cid: dy for cid, dy in zip(last_vals.index, [8, 0, -8])}
for case_id, sub in s1.groupby("case_id"):
    last = sub.iloc[-1]
    axA.annotate(f"{SHORT_LABELS[int(case_id)]}",
                 (last["pue"], last["heat_recovery_premium"]),
                 xytext=(8, slot.get(int(case_id), 0)),
                 textcoords="offset points",
                 fontsize=6.5, fontweight="bold",
                 color=case_color(int(case_id)), va="center")
axA.axhline(0, color=PALETTE["zero_line"], linewidth=0.6, linestyle="--",
            label="Premium = 0")
axA.set_xticks([1.10, 1.30, 1.50])
axA.set_xticklabels(["1.10\\nHyperscale", "1.30\\nModern", "1.50\\nLegacy"])
axA.set_xlim(1.05, 1.60)
# Extra bottom padding so the fanned label slots (slot[case] = +-8 px) stay
# inside the data area rather than getting clipped at the x-axis.
ymin = float(s1["heat_recovery_premium"].min())
axA.set_ylim(ymin - 0.18, 0.25)
axA.set_xlabel("Data-centre PUE (annual)")
axA.set_ylabel("Heat-Recovery Premium")
axA.set_axisbelow(True); axA.grid(alpha=0.3, linestyle="--")
axA.legend(loc="upper right", fontsize=6, frameon=False, handlelength=1.2)
panel_label(axA, "a", y=1.06)

# ----- Panel b -- PUE x Case 2D heatmap ---------------------------------
pivot = s1.pivot(index="pue", columns="case_id", values="heat_recovery_premium")
pivot = pivot.reindex(index=[1.50, 1.30, 1.10])
data_b = pivot.to_numpy()
row_labels = [f"PUE {p:.2f}" for p in pivot.index]
col_labels = [SHORT_LABELS[int(c)] for c in pivot.columns]
v = max(abs(np.nanmin(data_b)), abs(np.nanmax(data_b)))
im = bivariate_heatmap(axB, data_b, row_labels, col_labels,
                       vlow=-v, vhigh=v, vcenter=0, fmt="+.2f")
cbar = plt.colorbar(im, ax=axB, label="Premium", pad=0.02, shrink=0.85)
cbar.ax.tick_params(labelsize=5.5)
panel_label(axB, "b", y=1.06)

save_fig(fig, "fig5_s1_pue")
fig"""))

# ---- Fig 6 (3 panels) ----
CELLS.append(md("""## Fig 6 — S2: ERCOT year regime

- **a.** Grouped bar of Premium across (year × case) — the result.
- **b.** Violin plot of raw ERCOT LMP per year — the cause (2022 volatility, 2024 collapse).
- **c.** Summary statistics for each year (mean / std / 95th percentile) — the numbers."""))

CELLS.append(code("""# Fig 6 -- year x case Premium (a) + LMP violin (b) + LMP stats (c)
s2 = df[df.group == "s2_price"].copy()
years = [2022, 2023, 2024]
cases = [1, 2, 3, 4]

fig = plt.figure(figsize=mm(DOUBLE_COL_MM, 78))
gs = fig.add_gridspec(1, 3, width_ratios=[1.4, 1.0, 0.65],
                      wspace=0.40, left=0.06, right=0.98,
                      top=0.92, bottom=0.16)
axA = fig.add_subplot(gs[0]); axB = fig.add_subplot(gs[1]); axC = fig.add_subplot(gs[2])

# ----- Panel a -- grouped bar -------------------------------------------
x = np.arange(len(years)); width = 0.18
for i, case_id in enumerate(cases):
    sub = s2[s2.case_id == case_id].set_index("year").reindex(years)
    vals = sub["heat_recovery_premium"].to_numpy()
    offset = (i - (len(cases) - 1) / 2) * width
    axA.bar(x + offset, vals, width,
            color=case_color(case_id), edgecolor="black", linewidth=0.4,
            label=SHORT_LABELS[case_id])
    # Place each label at the bar's free edge (top for >=0, bottom for <0) so
    # negative-bar labels can't collide at y=0.
    for xi, v in zip(x + offset, vals):
        if np.isnan(v):
            continue
        va = "bottom" if v >= 0 else "top"
        dy = 3 if v >= 0 else -3
        axA.annotate(f"{v:+.2f}", (xi, v), xytext=(0, dy),
                     textcoords="offset points", ha="center", va=va,
                     fontsize=5.2, color=case_color(case_id), rotation=90)
axA.axhline(0, color=PALETTE["zero_line"], linewidth=0.6)
axA.set_xticks(x)
axA.set_xticklabels([f"{y}\\n{txt}" for y, txt in zip(years, ["extreme", "normal", "low"])])
axA.set_xlabel("ERCOT year")
axA.set_ylabel("Heat-Recovery Premium")
axA.set_axisbelow(True); axA.grid(axis="y", alpha=0.3, linestyle="--")
axA.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.04),
           fontsize=6, handlelength=1.0, columnspacing=1.0, frameon=False)
panel_label(axA, "a", y=1.10)

# ----- Panel b -- LMP violin per year -----------------------------------
lmp_by_year = {str(y): load_lmp(y) for y in years}
# Filter out negative-LMP outliers below 0.1 so log-scale violin works
lmp_clipped = {k: np.clip(v, 0.1, None) for k, v in lmp_by_year.items()}
violin_grouped(axB, lmp_clipped, log_y=True,
               colors=[PALETTE["stroke_clay"], PALETTE["stroke_teal"], PALETTE["stroke_navy"]])
axB.set_xlabel("ERCOT year")
axB.set_ylabel(r"LMP (\\$/MWh)")
panel_label(axB, "b", y=1.10)

# ----- Panel c -- LMP summary stats -------------------------------------
stats = {
    "mean": [lmp_by_year[str(y)].mean() for y in years],
    "std":  [lmp_by_year[str(y)].std()  for y in years],
    "p95":  [np.percentile(lmp_by_year[str(y)], 95) for y in years],
}
stat_colors = {"mean": PALETTE["fill_blue"],
               "std":  PALETTE["fill_orange"],
               "p95":  PALETTE["fill_salmon"]}
xs = np.arange(3); barw = 0.25
for i, (name, vals) in enumerate(stats.items()):
    off = (i - 1) * barw
    axC.bar(xs + off, vals, barw, color=stat_colors[name],
            edgecolor="black", linewidth=0.4, label=name)
axC.set_xticks(xs); axC.set_xticklabels([str(y) for y in years])
axC.set_ylabel(r"LMP (\\$/MWh)")
axC.set_axisbelow(True); axC.grid(axis="y", alpha=0.3, linestyle="--")
axC.legend(loc="upper right", fontsize=5.8, handlelength=1.0, frameon=False)
panel_label(axC, "c", y=1.10)

save_fig(fig, "fig6_s2_year_regime")
fig"""))

# ---- Fig 7 (2 panels) ----
CELLS.append(md("""## Fig 7 — S3: 100 MWh BESS perturbation

- **a.** Premium with vs without BESS for Cases 1–3 (paired bars).
- **b.** $/tCO2 avoided when the BESS is added — translates the small Premium impact into the carbon framing."""))

CELLS.append(code("""# Fig 7 -- BESS Premium delta (a) + $/tCO2 avoided (b)
s3 = df[(df.group == "s3_battery") & (df.case_id.isin([1, 2, 3]))].copy()
pivot_p   = s3.pivot(index="case_id", columns="bess_applied", values="heat_recovery_premium")
pivot_tac = s3.pivot(index="case_id", columns="bess_applied", values="tac_usd_per_yr")
pivot_co2 = s3.pivot(index="case_id", columns="bess_applied", values="co2_annual_tonnes")

cases = [1, 2, 3]
x = np.arange(len(cases)); width = 0.36

fig, (axA, axB) = plt.subplots(1, 2, figsize=mm(ONE_HALF_COL_MM + 30, 72),
                                gridspec_kw={"width_ratios": [1.0, 0.85],
                                             "wspace": 0.36,
                                             "left": 0.08, "right": 0.97,
                                             "top": 0.92, "bottom": 0.16})

# ----- Panel a -- Premium paired bar ------------------------------------
off_v = pivot_p[False].reindex(cases).to_numpy()
on_v  = pivot_p[True].reindex(cases).to_numpy()
axA.bar(x - width/2, off_v, width, color=PALETTE["fill_gray"],
        edgecolor="black", linewidth=0.4, label="No BESS")
axA.bar(x + width/2, on_v,  width, color=PALETTE["case2"],
        edgecolor="black", linewidth=0.4, label="100 MWh BESS")
axA.axhline(0, color=PALETTE["zero_line"], linewidth=0.6)
for xi, voff, von in zip(x, off_v, on_v):
    axA.annotate(f"{voff:+.2f}", (xi - width/2, voff), xytext=(0, -3),
                 textcoords="offset points", ha="center", va="top", fontsize=5.5)
    axA.annotate(f"{von:+.2f}", (xi + width/2, von), xytext=(0, -3),
                 textcoords="offset points", ha="center", va="top", fontsize=5.5)
axA.set_xticks(x); axA.set_xticklabels([SHORT_LABELS[c] for c in cases])
axA.set_ylabel("Heat-Recovery Premium")
# Headroom below the bars (negative direction) for the value labels, plus
# above for the panel label.  Legend sits at top-right INSIDE the axes so it
# does not collide with the panel "a" label or the bars.
ymin = float(min(off_v.min(), on_v.min()))
axA.set_ylim(ymin * 1.15, 0.25)
axA.set_axisbelow(True); axA.grid(axis="y", alpha=0.3, linestyle="--")
axA.legend(loc="upper right", ncol=1, fontsize=5.8, handlelength=1.2, frameon=False)
panel_label(axA, "a", y=1.04)

# ----- Panel b -- $/tCO2 avoided ----------------------------------------
dtac = (pivot_tac[True] - pivot_tac[False]).reindex(cases).to_numpy()
dco2 = (pivot_co2[False] - pivot_co2[True]).reindex(cases).to_numpy()
# $/tCO2 avoided = additional cost per tonne removed.  Negative dtac (savings)
# with positive dco2 (less CO2) = a "free" reduction.
with np.errstate(divide="ignore", invalid="ignore"):
    cost_per_t = np.where(dco2 != 0, dtac / dco2, np.nan)
colors_b = [PALETTE["pos"] if c < 0 else PALETTE["neg"] for c in cost_per_t]
axB.bar(x, cost_per_t, 0.5, color=colors_b, edgecolor="black", linewidth=0.4)
axB.axhline(0, color=PALETTE["zero_line"], linewidth=0.6)
for xi, c, col in zip(x, cost_per_t, colors_b):
    if np.isfinite(c):
        axB.annotate(f"{c:+.0f}", (xi, c), xytext=(0, 4 if c >= 0 else -7),
                     textcoords="offset points", ha="center",
                     va="bottom" if c >= 0 else "top", fontsize=6, color=col)
axB.set_xticks(x); axB.set_xticklabels([SHORT_LABELS[c] for c in cases])
axB.set_ylabel(r"\\$/tCO$_2$ avoided")
axB.set_axisbelow(True); axB.grid(axis="y", alpha=0.3, linestyle="--")
panel_label(axB, "b", y=1.10)

save_fig(fig, "fig7_s3_bess")
fig"""))

# ---- Fig 8 (3 panels) -- hero ----
CELLS.append(md("""## Fig 8 — S4: BWRX-300 CAPEX deployment maturity *(hero)*

- **a.** Premium vs CAPEX scenario for Cases 1–3 — the headline bar.
- **b.** 2D heatmap of Premium across CAPEX (FOAK/ATB-Mid/NOAK) × Case — visualizes that NOAK-Case2/3 is the only positive-Premium region.
- **c.** 5-dimensional sensitivity radar showing how each case rides each lever's full range."""))

CELLS.append(code("""# Fig 8 -- CAPEX bar (a) + CAPEX x Case heatmap (b) + sensitivity radar (c)
s4 = df[df.group == "s4_capex"].copy()
order  = ["FOAK", "ATB_Mid", "NOAK"]
pretty = {"FOAK":    "FOAK\\n\\$14.7k/kWe",
          "ATB_Mid": "ATB-Mid\\n\\$7.6k/kWe",
          "NOAK":    "NOAK\\n\\$2.25k/kWe"}
s4["reactor_scenario"] = pd.Categorical(s4["reactor_scenario"], categories=order, ordered=True)
pivot = s4.pivot(index="reactor_scenario", columns="case_id",
                 values="heat_recovery_premium").reindex(order)
cases = [1, 2, 3]
x = np.arange(len(order)); width = 0.24

fig = plt.figure(figsize=mm(DOUBLE_COL_MM, 90))
gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 0.85, 0.85],
                      wspace=0.40, left=0.07, right=0.97,
                      top=0.92, bottom=0.20)
axA = fig.add_subplot(gs[0])
axB = fig.add_subplot(gs[1])
axC = fig.add_subplot(gs[2], projection="polar")

# ----- Panel a -- Premium vs CAPEX scenario (grouped bar) ----------------
for i, case_id in enumerate(cases):
    vals = pivot[case_id].to_numpy()
    offset = (i - 1) * width
    axA.bar(x + offset, vals, width,
            color=case_color(case_id), edgecolor="black", linewidth=0.4,
            label=SHORT_LABELS[case_id])
    # Label at the free edge of each bar (top of positive, bottom of negative)
    # and rotated 90 deg in tight clusters to avoid horizontal pileup.
    for xi, v in zip(x + offset, vals):
        va = "bottom" if v >= 0 else "top"
        dy = 3 if v >= 0 else -3
        axA.annotate(f"{v:+.2f}", (xi, v), xytext=(0, dy),
                     textcoords="offset points", ha="center", va=va,
                     fontsize=5.4, color=case_color(case_id), rotation=90)
axA.axhline(0, color=PALETTE["zero_line"], linewidth=0.8, linestyle="--")
axA.set_xticks(x); axA.set_xticklabels([pretty[s] for s in order])
axA.set_xlabel("BWRX-300 CAPEX scenario")
axA.set_ylabel("Heat-Recovery Premium")
axA.set_axisbelow(True); axA.grid(axis="y", alpha=0.3, linestyle="--")
ymin = float(np.nanmin(pivot.to_numpy()))
axA.set_ylim(ymin - 0.3, max(np.nanmax(pivot.to_numpy()) + 0.5, 1.5))
axA.legend(title="Case", ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.04),
           fontsize=6, title_fontsize=6, handlelength=1.0, columnspacing=1.2,
           frameon=False)
panel_label(axA, "a", y=1.10)

# ----- Panel b -- CAPEX x Case 2D heatmap ------------------------------
data_b = pivot[cases].to_numpy()  # rows=CAPEX, cols=case
row_labels = ["FOAK", "ATB-Mid", "NOAK"]
col_labels = [SHORT_LABELS[c] for c in cases]
v = max(abs(np.nanmin(data_b)), abs(np.nanmax(data_b)))
im = bivariate_heatmap(axB, data_b, row_labels, col_labels,
                       vlow=-v, vhigh=v, vcenter=0, fmt="+.2f")
axB.set_xlabel("Case")
cbar = plt.colorbar(im, ax=axB, label="Premium", pad=0.02, shrink=0.85)
cbar.ax.tick_params(labelsize=5.5)
panel_label(axB, "b", y=1.10)

# ----- Panel c -- Sensitivity radar -------------------------------------
# For each case, score each sensitivity dimension as:
#   (max Premium achievable across that dim - baseline Premium for that case)
# Then normalize to [0, 1] across all (case, dim) entries so the most
# favorable case-dim combination = 1.
sweeps = {
    "PUE":      "s1_pue",
    "Year":     "s2_price",
    "BESS":     "s3_battery",
    "CAPEX":    "s4_capex",
    "Equip.":   "s5_equipment",
}
case_list = [2, 3]   # only C2 and C3 have full sweep coverage
radar_data = {}
for cid in case_list:
    base_p = df[(df.group == "main_baseline") & (df.case_id == cid)]["heat_recovery_premium"].iloc[0]
    case_scores = []
    for axis_name, group_name in sweeps.items():
        sub = df[(df.group == group_name) & (df.case_id == cid)]
        if len(sub) == 0:
            case_scores.append(0.0)
        else:
            case_scores.append(sub["heat_recovery_premium"].max() - base_p)
    radar_data[SHORT_LABELS[cid]] = case_scores

# Normalize so the max across all cases on the same axis = 1
data_arr = np.array(list(radar_data.values()))
max_per_axis = np.maximum(np.abs(data_arr).max(axis=0), 1e-9)
norm = data_arr / max_per_axis
radar_norm = {k: norm[i].tolist() for i, k in enumerate(radar_data.keys())}

radar(axC, list(sweeps.keys()), radar_norm,
      colors=[PALETTE["case2"], PALETTE["case3"]], ylim=(0, 1))
axC.set_yticks([0.25, 0.50, 0.75])
axC.set_yticklabels(["0.25", "0.50", "0.75"], fontsize=5.5)
axC.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10), fontsize=6,
           frameon=False)
panel_label(axC, "c", y=1.10)

save_fig(fig, "fig8_s4_capex_hero")
fig"""))

# ============================================================
# Methods / Data figures (M1 / M2 / M3)
# ============================================================

# ---- M1 ----
CELLS.append(md("""## Methods Fig M1 — ERCOT LMP 3-year overview

Input-data figure (Methods section, not Results).

- **a.** Monthly-mean LMP envelope for 2022 / 2023 / 2024 (band = monthly mean ± 1 std).
- **b.** Full-resolution 8760×3 duration curve, log y-axis."""))

CELLS.append(code("""# Fig M1 -- monthly LMP envelope (a) + full duration curve (b)
years = [2022, 2023, 2024]
year_colors = {
    2022: PALETTE["stroke_clay"],   # extreme volatility
    2023: PALETTE["stroke_teal"],   # normal
    2024: PALETTE["stroke_navy"],   # cheap
}
year_labels = {2022: "2022 (extreme)", 2023: "2023 (normal)", 2024: "2024 (cheap)"}

# Re-load with timestamp so we can compute monthly statistics.
# Use pd.to_datetime(..., utc=True) explicitly because the CSV has
# tz-aware strings ("-06:00") which pandas 2.x leaves as object dtype if
# parsed via parse_dates= alone.
def load_lmp_full(year: int) -> pd.DataFrame:
    p = DATA_DIR / "ercot" / f"{year}_rtm_lmp_houston_hourly.csv"
    d = pd.read_csv(p)
    d["timestamp_utc"] = pd.to_datetime(d["timestamp_utc"], utc=True)
    d["month"] = d["timestamp_utc"].dt.month
    return d

fig, (axA, axB) = plt.subplots(1, 2, figsize=mm(DOUBLE_COL_MM, 72),
                                gridspec_kw={"wspace": 0.30,
                                             "left": 0.07, "right": 0.98,
                                             "top": 0.92, "bottom": 0.16})

# ----- Panel a -- Monthly mean +/- 1 std band per year ------------------
for year in years:
    d = load_lmp_full(year)
    monthly = d.groupby("month")["rt_lmp_mean"].agg(["mean", "std"])
    mo = monthly.index.to_numpy()
    mu = monthly["mean"].to_numpy()
    sigma = monthly["std"].to_numpy()
    axA.plot(mo, mu, color=year_colors[year], linewidth=1.4, marker="o",
             markersize=3.5, label=year_labels[year])
    axA.fill_between(mo, mu - sigma, mu + sigma, color=year_colors[year],
                     alpha=0.18, linewidth=0)
axA.set_xticks(range(1, 13))
axA.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
axA.set_xlabel("Month")
axA.set_ylabel(r"ERCOT LMP (\\$/MWh)  (mean $\\pm$ 1 std)")
axA.set_axisbelow(True); axA.grid(alpha=0.3, linestyle="--")
axA.legend(loc="upper right", fontsize=6, frameon=False, handlelength=1.4)
panel_label(axA, "a", y=1.04)

# ----- Panel b -- Duration curves (full 8760 per year) ------------------
series = {year_labels[y]: (load_lmp(y), year_colors[y]) for y in years}
duration_curve(axB, series, log_y=True)
axB.set_ylabel(r"ERCOT LMP (\\$/MWh)")
axB.legend(loc="upper right", fontsize=6, frameon=False)
panel_label(axB, "b", y=1.04)

save_fig(fig, "figM1_ercot_lmp_overview")
fig"""))

# ---- M2 ----
CELLS.append(md("""## Methods Fig M2 — Houston climate inputs (wet-bulb + cooling)

- **a.** Daily mean wet-bulb temperature with month-band shading (2023, the baseline year).
- **b.** Monthly box-plot of cooling demand for Case 2 (driven by IT load × climate)."""))

CELLS.append(code("""# Fig M2 -- Houston wet-bulb (a) + monthly cooling demand box (b)
wb = pd.read_csv(DATA_DIR / "weather" / "houston_hourly_2023.csv", parse_dates=["time"])
wb["dayofyear"] = wb["time"].dt.dayofyear
wb["month"]     = wb["time"].dt.month
daily = wb.groupby("dayofyear")["wet_bulb_C"].mean()

# Cooling demand from Case 2 dispatch (Q_cool varies with IT load and temperature)
disp_c2 = load_dispatch("main_baseline", "case2")
hours = np.arange(len(disp_c2))
months_per_hour = ((hours // 24) // 30.5 % 12).astype(int) + 1  # rough month bucket
cool_by_month = {m: disp_c2.loc[months_per_hour == m, "Q_cool_MWth"].to_numpy()
                  for m in range(1, 13)}

fig, (axA, axB) = plt.subplots(1, 2, figsize=mm(DOUBLE_COL_MM, 72),
                                gridspec_kw={"wspace": 0.30,
                                             "left": 0.07, "right": 0.98,
                                             "top": 0.92, "bottom": 0.16})

# ----- Panel a -- Daily wet-bulb + month bands --------------------------
axA.plot(daily.index, daily.values, color=PALETTE["stroke_teal"], linewidth=1.0)
month_starts = [pd.Timestamp(f"2023-{m:02d}-01").dayofyear for m in range(1, 13)]
month_starts.append(366)
# Alternate light-gray bands so seasonal structure reads at a glance
for i in range(len(month_starts) - 1):
    if i % 2 == 0:
        axA.axvspan(month_starts[i], month_starts[i + 1],
                    color=PALETTE["fill_gray"], alpha=0.18, zorder=0)
axA.set_xlim(1, 365)
axA.set_xticks([month_starts[m] for m in range(12)])
axA.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
axA.set_xlabel("Day of year (2023)")
axA.set_ylabel(r"Wet-bulb temperature ($^\\circ$C)")
axA.set_axisbelow(True); axA.grid(axis="y", alpha=0.3, linestyle="--")
panel_label(axA, "a", y=1.04)

# ----- Panel b -- Monthly box-plot of cooling demand --------------------
months = list(range(1, 13))
data_b = [cool_by_month[m] for m in months]
bp = axB.boxplot(data_b, positions=months, widths=0.55,
                  patch_artist=True, showfliers=False,
                  medianprops=dict(color="#000000", linewidth=0.8),
                  whiskerprops=dict(linewidth=0.6),
                  capprops=dict(linewidth=0.6),
                  boxprops=dict(linewidth=0.6))
for patch in bp["boxes"]:
    patch.set_facecolor(PALETTE["fill_orange"])
    patch.set_edgecolor("#000000")
    patch.set_alpha(0.85)
axB.set_xticks(months)
axB.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
axB.set_xlabel("Month")
axB.set_ylabel(r"Cooling demand $Q_\\mathrm{cool}$ (MW$_\\mathrm{th}$)")
axB.set_axisbelow(True); axB.grid(axis="y", alpha=0.3, linestyle="--")
panel_label(axB, "b", y=1.04)

save_fig(fig, "figM2_houston_climate")
fig"""))

# ---- M3 ----
CELLS.append(md("""## Methods Fig M3 — BWRX-300 CAPEX trajectory

Single-panel comparison of the three CAPEX scenarios used in S4 against three independent literature benchmarks.  Bars = scenario values used in this work; markers = literature values."""))

CELLS.append(code("""# Fig M3 -- BWRX-300 CAPEX scenarios vs literature benchmarks
scenarios = ["FOAK", "ATB-Mid", "NOAK"]
capex_kwe = {
    "FOAK":    14700,    # MIT ANP-201, per BWRX-300 first-of-a-kind estimate
    "ATB-Mid": 7600,     # NREL ATB 2024 mid-line SMR projection
    "NOAK":    2250,     # ATB 2024 long-term Nth-of-a-kind
}
benchmarks = {
    "UNECE 2022 mean SMR":    (7000, "o"),
    "MIT ANP-201 (BWRX-300)": (12700, "s"),
    "NREL ATB-Low 2024":      (3800, "^"),
}

fig, ax = plt.subplots(figsize=mm(SINGLE_COL_MM + 25, 75),
                        gridspec_kw={"left": 0.15, "right": 0.97,
                                     "top": 0.92, "bottom": 0.20})

# Bars in case-block fills (low-sat) so markers (high-sat) read on top
bar_colors = [PALETTE["fill_orange"], PALETTE["fill_blue"], PALETTE["accent_teal"]]
x = np.arange(len(scenarios))
ax.bar(x, [capex_kwe[s] for s in scenarios], 0.55,
       color=bar_colors, edgecolor="black", linewidth=0.6, alpha=0.85)
for xi, s in zip(x, scenarios):
    ax.annotate(f"\\${capex_kwe[s]:,}", (xi, capex_kwe[s]),
                xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", fontsize=6, fontweight="bold")

# Literature benchmark markers, plotted at a y-coordinate to indicate the value
benchmark_colors = [PALETTE["stroke_teal"], PALETTE["stroke_navy"], PALETTE["stroke_clay"]]
for (bname, (bval, bmarker)), bc in zip(benchmarks.items(), benchmark_colors):
    # Plot the benchmark as a horizontal dashed line + a single marker at x=1.5
    ax.axhline(bval, color=bc, linestyle=":", linewidth=0.6, alpha=0.7)
    ax.scatter(len(scenarios) + 0.4, bval, marker=bmarker, s=60,
               color=bc, edgecolor="black", linewidth=0.6, zorder=3,
               clip_on=False, label=f"{bname} (\\${bval:,})")

ax.set_xticks(x)
ax.set_xticklabels(scenarios)
ax.set_xlim(-0.5, len(scenarios) + 0.9)
ax.set_xlabel("CAPEX scenario (BWRX-300, overnight)")
ax.set_ylabel(r"Overnight CAPEX (\\$/kW$_\\mathrm{e}$)")
ax.set_axisbelow(True); ax.grid(axis="y", alpha=0.3, linestyle="--")
# Legend BELOW the axes so the literature-benchmark markers (plotted at x=3.4
# inside the data area) don't sit inside the legend box.
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=3,
          fontsize=5.8, handlelength=1.0, frameon=False,
          title="Literature benchmarks (markers + dotted reference lines)",
          title_fontsize=6)
fig.subplots_adjust(bottom=0.32)

save_fig(fig, "figM3_capex_trajectory")
fig"""))

# ---- Summary ----
CELLS.append(md("""## Summary

All figures written to `outputs/figures/`.  Each is exported as **PDF + SVG + PNG (600 dpi)** via `save_fig` / `save_triplet`.

| File | Figure | Panels |
|---|---|---|
| `fig2_economics_overview.*`   | Fig 2 — TAC + Premium waterfall + tornado     | 3 |
| `fig3_cost_carbon.*`          | Fig 3 — Pareto + carbon decomposition         | 2 |
| `fig4_case2_operational.*`    | Fig 4 — winter + summer + diurnal + LMP dur.  | 4 |
| `fig5_s1_pue.*`               | Fig 5 — PUE line + PUE×Case heatmap           | 2 |
| `fig6_s2_year_regime.*`       | Fig 6 — grouped bar + LMP violin + stats      | 3 |
| `fig7_s3_bess.*`              | Fig 7 — BESS Premium + \\$/tCO2 avoided        | 2 |
| `fig8_s4_capex_hero.*`        | Fig 8 — CAPEX bar + CAPEX×Case + radar *(hero)* | 3 |
| `figM1_ercot_lmp_overview.*`  | Fig M1 — Monthly LMP envelope + duration curve | 2 |
| `figM2_houston_climate.*`     | Fig M2 — Wet-bulb daily + cooling demand box   | 2 |
| `figM3_capex_trajectory.*`    | Fig M3 — BWRX-300 CAPEX scenarios + benchmarks | 1 |

**Total: 19 results subpanels + 5 Methods/Data subpanels + Fig 1 schematic (separate .tex) = 25 paper subpanels.**

After running this notebook, invoke the sci-figure QA loop:

```bash
for f in outputs/figures/fig*.png; do
    python ~/.claude/skills/sci-figure/scripts/qa_check.py "$f"
    python ~/.claude/skills/sci-figure/scripts/colorblind_check.py "$f"
done
```

Then walk through `~/.claude/skills/sci-figure/references/qa-checklist.md` and fix any flagged items before declaring final."""))

# ---- Assemble notebook ----
nb = nbf.v4.new_notebook()
nb["cells"] = CELLS
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
nbf.write(nb, OUT)
print(f"Wrote {OUT} with {len(CELLS)} cells.")
