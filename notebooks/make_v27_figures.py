"""Generate every v2.7 paper figure into outputs/figures/.

Reads outputs/master_kpi_table.csv (76 rows from scripts/run_all_analyses.py)
and the Case 2 hourly dispatch from outputs/main_baseline/case2/dispatch.csv.gz,
then renders Fig 1–11 + the Graphical Abstract following the sci-figure skill
(palette, saturation rules, no titles, PDF+SVG+PNG triplet export).

v2.7 deltas vs v2.6:
  - Fig 10 — new: S6 carbon-price crossover (\$0/\$50/\$100/tCO2 across all 4
    cases) with Premium=0 vertical lines marking the policy break-even.
  - Fig 11 — new: 8-KPI compact panel (LCOE / EPBT / water / abatement cost),
    confirming the plan §0.5 D promise that all eight KPIs are populated.
  - Graphical Abstract — now a two-panel composition that pairs the S5 2D
    viability map (where) with the S6 carbon-price ladder (when).
  - Underlying data: BESS power capacity 25 → 50 MW (Plan §F.3 fix),
    Henry-Hub fuel cost now hourly (Plan §F.2), and the carbon-price
    sensitivity adds a new TAC term in Cases 1-2 via cfg.base.physics.

Fig 1 is generated here so its palette, line weights and typography match the
quantitative result figures.

Run from project root:

    PYTHONPATH=. python notebooks/make_v27_figures.py
"""

# %% [markdown]
# # v2.7 paper figure pipeline
#
# Builds 11 main figures plus a Graphical Abstract for the plan-v2.7 Applied
# Energy manuscript. Each figure exports PDF + SVG + PNG via the sci-figure
# helper `save_triplet`.
#
# Inputs: `outputs/master_kpi_table.csv` (76 rows) and `outputs/main_baseline/case2/dispatch.csv.gz`.
# Outputs: `outputs/figures/fig{1..11}_*.{pdf,svg,png}` plus
# `outputs/figures/graphical_abstract.{pdf,svg,png}`.

# %%
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D

# sci-figure helpers (palette + apply_sci_style + save_triplet)
SCI_FIGURE_SCRIPTS = "/home/honglin/.claude/skills/sci-figure/scripts"
if SCI_FIGURE_SCRIPTS not in sys.path:
    sys.path.insert(0, SCI_FIGURE_SCRIPTS)
from sci_figure_helpers import (  # noqa: E402
    PALETTE,
    apply_sci_style,
    save_triplet,
    add_panel_label,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = PROJECT_ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

apply_sci_style("ae_single")  # 7pt body for 89mm AE single column

SINGLE_W = 3.45
DOUBLE_W = 7.0
EDGE_LW = 0.75
GRID_KW = dict(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)

CASE_LINE = {
    0: "#555555",
    1: PALETTE["accent_teal"],
    2: PALETTE["stroke_teal"],
    3: PALETTE["stroke_clay"],
}
CASE_FILL = {
    0: PALETTE["fill_gray"],
    1: PALETTE["fill_blue"],
    2: PALETTE["case1"],
    3: PALETTE["fill_orange"],
}

# %% [markdown]
# ## Data loading

# %%
df = pd.read_csv(OUTPUTS / "master_kpi_table.csv")
print(f"Loaded {len(df)} rows from master_kpi_table.csv")
print(df.groupby("group").size())

# Convenience column for absolute Premium percentage
df["premium_pct"] = df["heat_recovery_premium"] * 100

# Case identity mapping for legends and colors
CASE_LABEL = {
    0: "Case 0 — Grid only",
    1: "Case 1 — Nuclear, no recovery",
    2: "Case 2 — Nuclear + cascade extraction",
    3: "Case 3 — NGCC on-site",
}
CASE_COLOR = {
    0: CASE_LINE[0],
    1: CASE_LINE[1],
    2: CASE_LINE[2],
    3: CASE_LINE[3],
}
CASE_MARKER = {0: "o", 1: "s", 2: "D", 3: "^"}

# %% [markdown]
# ## Fig 1 — Case 2 plant schematic

# %%
def _draw_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    label: str,
    facecolor: str,
    edgecolor: str,
    fontsize: float = 6.2,
) -> FancyBboxPatch:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.04,rounding_size=0.025",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0.75,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#111111",
        linespacing=1.08,
    )
    return box


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    *,
    style: str = "-|>",
    rad: float = 0.0,
    lw: float = 1.0,
    alpha: float = 1.0,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=8,
            connectionstyle=f"arc3,rad={rad}",
            linewidth=lw,
            color=color,
            alpha=alpha,
            shrinkA=3,
            shrinkB=3,
        )
    )


def fig1_system_schematic() -> None:
    heat = PALETTE["stroke_clay"]
    elec = PALETTE["stroke_navy"]
    cool = PALETTE["stroke_teal"]
    edge = "#323232"

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.38))
    ax.set_xlim(0, 10.0)
    ax.set_ylim(0.0, 5.45)
    ax.axis("off")

    boxes = {
        "rx": _draw_box(ax, (0.30, 4.35), 1.35, 0.64, "BWRX-300\nreactor\n$P_{rx}$",
                        PALETTE["fill_blue"], edge),
        "hp": _draw_box(ax, (2.05, 4.35), 1.12, 0.64, "HP turbine\n$P_{tg}$",
                        PALETTE["fill_blue"], edge),
        "lp": _draw_box(ax, (3.78, 4.35), 1.35, 0.64, "LP turbine\n+ condenser",
                        PALETTE["fill_blue"], edge),
        "abs": _draw_box(ax, (1.95, 2.30), 1.75, 0.78, "Double-effect\nLiBr-H$_2$O\nabsorber",
                         PALETTE["fill_orange"], edge, fontsize=5.8),
        "vcc": _draw_box(ax, (4.45, 2.08), 1.22, 0.70, "VCC\nbackup",
                         PALETTE["fill_salmon"], edge),
        "grid": _draw_box(ax, (4.25, 0.72), 1.42, 0.64, "ERCOT grid\nPCC 300 MW",
                          PALETTE["fill_gray"], edge, fontsize=5.9),
        "bess": _draw_box(ax, (6.55, 0.72), 1.40, 0.64, "BESS\n100 MWh\n50 MW",
                          "#F3E3A4", edge, fontsize=5.8),
        "dc": _draw_box(ax, (7.75, 2.58), 1.85, 0.95, "Data center\n200 MW$_e$",
                        "#E6E6E6", edge, fontsize=6.5),
    }

    # Heat / steam path.
    _arrow(ax, (1.65, 4.67), (2.05, 4.67), heat)
    _arrow(ax, (3.17, 4.67), (3.78, 4.67), heat)
    ax.text(1.86, 5.08, "steam", fontsize=5.3, color=heat, ha="center")
    _arrow(ax, (2.62, 4.35), (2.62, 3.08), heat, rad=0.0)
    ax.text(2.74, 3.74, "extraction", fontsize=5.5, color=heat,
            ha="left", va="center")

    # Electric path and bidirectional grid/storage exchanges.
    _arrow(ax, (5.13, 4.67), (7.75, 3.42), elec, rad=-0.18)
    ax.text(6.45, 4.20, "electricity", fontsize=5.6, color=elec,
            ha="center", va="center")
    _arrow(ax, (5.55, 1.36), (7.75, 2.77), elec, style="<|-|>", rad=-0.08)
    _arrow(ax, (7.25, 1.36), (8.35, 2.58), elec, style="<|-|>", rad=0.05)

    # Chilled-water delivery from absorption and backup VCC.
    _arrow(ax, (3.70, 2.84), (7.75, 3.05), cool, rad=-0.08)
    _arrow(ax, (5.67, 2.34), (7.75, 2.78), cool, rad=0.08)
    ax.text(5.95, 3.18, "chilled water", fontsize=5.6, color=cool,
            ha="center")

    # Compact legend.
    legend_handles = [
        Line2D([0], [0], color=heat, lw=1.2, label="heat / steam"),
        Line2D([0], [0], color=elec, lw=1.2, label="electricity"),
        Line2D([0], [0], color=cool, lw=1.2, label="chilled water"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", bbox_to_anchor=(0.0, -0.03),
              frameon=False, ncol=3, fontsize=5.8, handlelength=1.5,
              columnspacing=0.9)

    fig.tight_layout(pad=0.12)
    save_triplet(fig, "fig1_system_schematic", str(FIGURES))
    plt.close(fig)


fig1_system_schematic()

# %% [markdown]
# ## Fig 2 — TAC cost stack (4 cases, 2023 ATB-Mid baseline)
#
# Stacked bar of TAC for each case decomposed into CAPEX × CRF, FOM, VOM,
# Fuel, and net Grid (positive=import, negative=export shown below zero).
# Premium % annotation on top of each bar.

# %%
def fig2_tac_stack() -> None:
    base = df[df.group == "main_baseline"].sort_values("case_id").reset_index(drop=True)

    cases = base.case_id.astype(int).values
    labels = [f"C{c}" for c in cases]
    capex = base.capex_annual_usd.values / 1e6
    fom = base.fom_annual_usd.values / 1e6
    vom = base.vom_annual_usd.values / 1e6
    fuel = base.fuel_annual_usd.values / 1e6
    grid = base.grid_annual_usd.values / 1e6  # may be negative (export revenue)
    tac = base.tac_usd_per_yr.values / 1e6
    premium = base.premium_pct.values

    # Positive grid (imports) stacks above; negative grid (exports) shows below 0
    grid_pos = np.where(grid > 0, grid, 0.0)
    grid_neg = np.where(grid < 0, grid, 0.0)  # already negative

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.7))
    x = np.arange(len(cases))
    bw = 0.62

    # Stack positive components
    bot = np.zeros_like(capex)
    components = [
        ("Capital × CRF", capex, PALETTE["comp_capital"], 0.92),
        ("Fixed O&M", fom, PALETTE["comp_om"], 0.92),
        ("Variable O&M", vom, PALETTE["fill_gray"], 0.92),
        ("Fuel", fuel, PALETTE["comp_fuel"], 0.88),
        ("Grid import", grid_pos, PALETTE["stroke_clay"], 0.50),
    ]
    for lab, vals, color, alpha in components:
        if vals.sum() < 1e-3:
            continue
        ax.bar(x, vals, bottom=bot, width=bw, color=color, edgecolor="#000000",
               linewidth=EDGE_LW, alpha=alpha, label=lab)
        bot = bot + vals

    # Below-zero grid export bar (revenue offset)
    if (grid_neg < 0).any():
        ax.bar(x, grid_neg, width=bw,
               color=PALETTE["accent_teal"], edgecolor="#000000", linewidth=EDGE_LW,
               alpha=0.75,
               label="Grid export (revenue)")

    # Net TAC line marker on top of each bar
    stack_top = capex + fom + vom + fuel + grid_pos
    for xi, tac_i, prem_i, top in zip(x, tac, premium, stack_top):
        ax.scatter(xi, tac_i, marker="_", s=320, color="#000000", linewidth=1.6,
                   zorder=5, label="Net TAC" if xi == 0 else None)
        # Place the label ABOVE the visible stack top (not the net TAC) so it
        # never overlaps the bars themselves.
        ax.annotate(
            f"TAC ${tac_i:.0f} M\nP = {prem_i:+.0f}%",
            xy=(xi, top),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6,
            color="#000000",
        )

    ax.axhline(0, color="#000000", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"Annualised cost (M\$/yr)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2,
              frameon=False, columnspacing=0.8, handlelength=1.2)

    fig.tight_layout()
    save_triplet(fig, "fig2_tac_stack", str(FIGURES))
    plt.close(fig)

fig2_tac_stack()

# %% [markdown]
# ## Fig 3 — Cost vs CO₂ scatter (4 cases × 3 ERCOT years)
#
# Each case anchored by its 3-year (year × case) scatter cluster. Markers
# differentiate case; colors echo Fig 2. Arrow shows direction of preference
# (toward bottom-left = cheaper and cleaner).

# %%
def fig3_cost_carbon() -> None:
    s2 = df[df.group == "s2_price"].copy()
    s2["tac_m"] = s2.tac_usd_per_yr / 1e6
    s2["co2_kt"] = s2.co2_annual_tonnes / 1e3

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.65))
    for cid in (0, 1, 2, 3):
        sub = s2[s2.case_id == cid].sort_values("year")
        ax.plot(sub.tac_m, sub.co2_kt,
                color=CASE_LINE[cid], linewidth=0.9, alpha=0.65, zorder=2)
        ax.scatter(sub.tac_m, sub.co2_kt,
                   marker=CASE_MARKER[cid], s=55,
                   facecolor=CASE_FILL[cid], edgecolor=CASE_LINE[cid], linewidth=0.9,
                   zorder=3, label=CASE_LABEL[cid])

    ax.set_xlabel(r"TAC (M\$/yr)")
    ax.set_ylabel(r"Annual CO$_2$ (kt CO$_2$/yr)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2,
              frameon=False, fontsize=6, columnspacing=0.7, handlelength=1.0)

    # Pareto arrow
    ax.annotate("", xy=(0.05, 0.05), xytext=(0.30, 0.30),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=PALETTE["stroke_teal"],
                                lw=1.0, alpha=0.7))
    ax.text(0.32, 0.32, "preferred", transform=ax.transAxes,
            fontsize=6, color=PALETTE["stroke_teal"], style="italic")

    fig.tight_layout()
    save_triplet(fig, "fig3_cost_carbon", str(FIGURES))
    plt.close(fig)

fig3_cost_carbon()

# %% [markdown]
# ## Fig 4 — Case 2 typical-week dispatch (winter + summer)
#
# Two panels each covering 168 h: a January week (cool wet bulb, COP ~1.30)
# and a July week (warm wet bulb, COP dropping, crystallization gate may
# engage). Shows reactor thermal, turbine net electric, extraction to
# absorption, absorption cool, and VCC backup.

# %%
def fig4_case2_dispatch() -> None:
    disp = pd.read_csv(OUTPUTS / "main_baseline" / "case2" / "dispatch.csv.gz")
    winter_start = 24 * 14            # Jan 15 00:00 (hour 336)
    summer_start = 24 * (31 + 28 + 31 + 30 + 31 + 30 + 14)  # July 15 00:00 = hour 4680
    weeks = [
        ("Winter (Jan 15 – Jan 22)", winter_start),
        ("Summer (Jul 15 – Jul 22)", summer_start),
    ]

    fig, axes = plt.subplots(2, 1, figsize=(7.0, 4.4), sharex=False)

    handle_specs: list[tuple[str, str, str, str]] = []  # (label, kind, color, ls)
    for ax, (name, start) in zip(axes, weeks):
        sl = disp.iloc[start:start + 168].reset_index(drop=True)
        hours = np.arange(168)

        # Primary axis (left): reactor thermal + turbine net electric power.
        ax.fill_between(hours, 0, sl.P_turb_net_MW,
                        color=PALETTE["fill_blue"], alpha=0.85,
                        edgecolor="white", linewidth=0.4,
                        label=r"$P_\mathrm{turb,net}$ (MW$_\mathrm{e}$)")
        ax.plot(hours, sl.P_rx_MWth, color=PALETTE["stroke_navy"], linewidth=1.0,
                label=r"$P_\mathrm{rx}$ (MW$_\mathrm{th}$)")
        ax.set_xlim(0, 167)
        ax.set_xlabel("Hour of week")
        ax.set_ylabel(r"Power / heat (MW)")
        ax.set_axisbelow(True)
        ax.grid(**GRID_KW)

        # Secondary axis (right): cooling streams + extraction flow.
        ax_r = ax.twinx()
        ax_r.plot(hours, sl.Q_to_abs_MWth,
                  color=PALETTE["stroke_clay"], linewidth=1.2, linestyle="--",
                  label=r"$Q_\mathrm{extract}$ (MW$_\mathrm{th}$)")
        ax_r.plot(hours, sl.Q_abs_cool_MWth,
                  color=PALETTE["stroke_teal"], linewidth=1.2,
                  label=r"$Q_\mathrm{abs,cool}$ (MW$_\mathrm{c}$)")
        ax_r.fill_between(hours, 0, sl.Q_VCC_cool_MWth,
                          color=PALETTE["fill_salmon"], alpha=0.6,
                          edgecolor="white", linewidth=0.3,
                          label=r"$Q_\mathrm{VCC,backup}$ (MW$_\mathrm{c}$)")
        ax_r.set_ylabel(r"Cooling / extraction (MW)")
        ax_r.set_ylim(bottom=0)
        ax_r.spines["right"].set_visible(True)

        ax.text(0.02, 0.08, name, transform=ax.transAxes, fontsize=7,
                fontweight="bold", color="#222222",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=1.2))

        # Collect handles once (winter has all)
        if not handle_specs:
            handle_specs = [
                (r"$P_\mathrm{turb,net}$ (MW$_\mathrm{e}$)", "patch",
                 PALETTE["fill_blue"], None),
                (r"$P_\mathrm{rx}$ (MW$_\mathrm{th}$)", "line",
                 PALETTE["stroke_navy"], "-"),
                (r"$Q_\mathrm{extract}$ (MW$_\mathrm{th}$)", "line",
                 PALETTE["stroke_clay"], "--"),
                (r"$Q_\mathrm{abs,cool}$ (MW$_\mathrm{c}$)", "line",
                 PALETTE["stroke_teal"], "-"),
                (r"$Q_\mathrm{VCC,backup}$ (MW$_\mathrm{c}$)", "patch",
                 PALETTE["fill_salmon"], None),
            ]

    # Single combined legend drawn from synthetic handles
    legend_handles = []
    for label, kind, color, ls in handle_specs:
        if kind == "patch":
            from matplotlib.patches import Patch
            legend_handles.append(Patch(facecolor=color, edgecolor="white",
                                        label=label))
        else:
            legend_handles.append(Line2D([0], [0], color=color, linestyle=ls or "-",
                                         linewidth=1.4, label=label))
    fig.legend(handles=legend_handles, loc="lower center",
               bbox_to_anchor=(0.5, -0.02), ncol=5, frameon=False, fontsize=6.5,
               columnspacing=1.4, handlelength=1.8)
    add_panel_label(axes[0], "a", x=-0.06, y=1.02)
    add_panel_label(axes[1], "b", x=-0.06, y=1.02)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.14)
    save_triplet(fig, "fig4_case2_dispatch", str(FIGURES))
    plt.close(fig)

fig4_case2_dispatch()

# %% [markdown]
# ## Fig 5 — S1: PUE vs Heat-Recovery Premium for Cases 1 & 2
#
# Three PUE levels {1.10, 1.30, 1.50} on x; Premium (%) on y. Reference
# line at Premium = 0. Markers join via line. PUE narrative target: critical
# point where Premium crosses 0 for each case.

# %%
def fig5_s1_pue() -> None:
    s1 = df[df.group == "s1_pue"].sort_values(["case_id", "pue"]).copy()

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.45))
    for cid in (1, 2):
        sub = s1[s1.case_id == cid]
        ax.plot(sub.pue, sub.premium_pct,
                marker=CASE_MARKER[cid], markersize=6,
                color=CASE_LINE[cid], linewidth=1.5,
                markerfacecolor=CASE_FILL[cid],
                markeredgecolor=CASE_LINE[cid], markeredgewidth=0.9,
                label={1: "C1 nuclear, no recovery",
                       2: "C2 nuclear + absorption"}[cid])

    ax.axhline(0, color=PALETTE["accent_teal"], linestyle="--",
               linewidth=1.0, alpha=0.8, label="Premium = 0")
    ax.set_xlabel("PUE")
    ax.set_ylabel("Heat-Recovery Premium (%)")
    ax.set_xticks([1.10, 1.30, 1.50])
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    ax.legend(loc="center right", bbox_to_anchor=(0.98, 0.60),
              frameon=False, fontsize=5.8, handlelength=1.4,
              borderaxespad=0.0, labelspacing=0.35)
    fig.tight_layout()
    save_triplet(fig, "fig5_s1_pue", str(FIGURES))
    plt.close(fig)

fig5_s1_pue()

# %% [markdown]
# ## Fig 6 — S2: ERCOT 3-year regime grouped bars
#
# Years 2022 / 2023 / 2024 on x; 4 cases per cluster. Y = Heat-Recovery
# Premium (%). The 2024 cluster should show the largest negative Premium
# for nuclear cases (cheap grid year).

# %%
def fig6_s2_year_regime() -> None:
    s2 = df[df.group == "s2_price"].copy().sort_values(["year", "case_id"])

    years = sorted(s2.year.unique())
    cases = sorted(s2.case_id.unique())
    x = np.arange(len(years))
    bar_w = 0.18

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.75))
    for i, cid in enumerate(cases):
        vals = [
            s2[(s2.year == y) & (s2.case_id == cid)].premium_pct.iloc[0]
            for y in years
        ]
        offset = (i - (len(cases) - 1) / 2) * bar_w
        ax.bar(x + offset, vals, width=bar_w,
               color=CASE_FILL[cid], edgecolor=CASE_LINE[cid], linewidth=EDGE_LW,
               label=CASE_LABEL[cid])

    ax.axhline(0, color="#000000", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlabel("ERCOT year")
    ax.set_ylabel("Heat-Recovery Premium (%)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.35), ncol=2,
              frameon=False, fontsize=6, columnspacing=0.8, handlelength=1.1)
    fig.tight_layout()
    save_triplet(fig, "fig6_s2_year_regime", str(FIGURES))
    plt.close(fig)

fig6_s2_year_regime()

# %% [markdown]
# ## Fig 7 — S3: BESS on/off effect + $/tCO₂ avoided panel
#
# Two panels: (a) bar of ΔTAC (with BESS − without BESS) per case;
# (b) bar of carbon abatement cost ($/tCO₂ avoided) vs Case 0.

# %%
def fig7_s3_bess() -> None:
    s3 = df[df.group == "s3_battery"].copy()
    # Pivot to wide form: TAC_off, TAC_on per case
    wide = s3.pivot_table(index="case_id", columns="bess_applied",
                          values="tac_usd_per_yr")
    wide["delta_M"] = (wide.get(True, np.nan) - wide.get(False, np.nan)) / 1e6
    # CO2 same way
    co2_wide = s3.pivot_table(index="case_id", columns="bess_applied",
                              values="co2_annual_tonnes")

    # $/tCO2 avoided vs Case 0 baseline (BESS off)
    tac_off = wide.get(False, np.nan)
    co2_off = co2_wide.get(False, np.nan)
    tac_case0 = tac_off.loc[0]
    co2_case0 = co2_off.loc[0]
    abate = []
    for cid in tac_off.index:
        d_tac = tac_off.loc[cid] - tac_case0
        d_co2 = co2_case0 - co2_off.loc[cid]
        abate.append(d_tac / d_co2 if abs(d_co2) > 1e-3 else np.nan)
    wide["abate_usd_per_tco2"] = abate

    cases = wide.index.tolist()
    labels = [f"C{c}" for c in cases]
    fill_colors = [CASE_FILL[c] for c in cases]
    edge_colors = [CASE_LINE[c] for c in cases]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(SINGLE_W, 3.35))

    # Panel a — ΔTAC with BESS
    ax1.bar(labels, wide.delta_M.values, color=fill_colors,
            edgecolor=edge_colors, linewidth=EDGE_LW)
    ax1.axhline(0, color="#000000", linewidth=0.7)
    ax1.set_ylabel(r"$\Delta$TAC with BESS (M\$/yr)")
    ax1.set_xlabel("Case")
    ax1.set_axisbelow(True)
    ax1.grid(**GRID_KW)
    add_panel_label(ax1, "a", x=-0.10, y=1.02)

    # Panel b — $/tCO2 abated
    ax2.bar(labels, wide.abate_usd_per_tco2.values, color=fill_colors,
            edgecolor=edge_colors, linewidth=EDGE_LW)
    ax2.axhline(0, color="#000000", linewidth=0.7)
    ax2.set_ylabel(r"Carbon abatement (\$/tCO$_2$)")
    ax2.set_xlabel("Case")
    ax2.set_axisbelow(True)
    ax2.grid(**GRID_KW)
    add_panel_label(ax2, "b", x=-0.10, y=1.02)

    fig.tight_layout()
    save_triplet(fig, "fig7_s3_bess", str(FIGURES))
    plt.close(fig)

fig7_s3_bess()

# %% [markdown]
# ## Fig 8 — S4: SMR CAPEX FOAK / ATB-Mid / NOAK 1D scenarios
#
# Cases 1 & 2 across three deployment-maturity points. Designed to embed in
# Discussion at a smaller print size.

# %%
def fig8_s4_capex_1d() -> None:
    s4 = df[df.group == "s4_capex"].copy()
    scen_order = ["FOAK", "ATB_Mid", "NOAK"]
    x = np.arange(len(scen_order))
    bar_w = 0.36

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.45))
    for i, cid in enumerate((1, 2)):
        vals = [
            s4[(s4.reactor_scenario == s) & (s4.case_id == cid)].premium_pct.iloc[0]
            for s in scen_order
        ]
        offset = (i - 0.5) * bar_w
        ax.bar(x + offset, vals, width=bar_w,
               color=CASE_FILL[cid], edgecolor=CASE_LINE[cid], linewidth=EDGE_LW,
               label=CASE_LABEL[cid])
        for xi, v in zip(x + offset, vals):
            if v < -40:
                y_lab = v + 14
                va = "bottom"
            elif v < 0:
                y_lab = v - 7
                va = "top"
            else:
                y_lab = v + 4
                va = "bottom"
            ax.text(xi, y_lab, f"{v:+.0f}%",
                    ha="center", va=va, fontsize=5.5, color="#000000")

    ax.axhline(0, color="#000000", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(["FOAK\n$14,700", "ATB-Mid\n$7,615", "NOAK\n$2,250"], fontsize=6.5)
    ax.set_xlabel(r"BWRX-300 OCC (\$/kW$_\mathrm{e}$)")
    ax.set_ylabel("Heat-Recovery Premium (%)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    ax.legend(loc="lower right", frameon=False, fontsize=6)
    ax.set_ylim(-530, 25)
    fig.tight_layout()
    save_triplet(fig, "fig8_s4_capex_1d", str(FIGURES))
    plt.close(fig)

fig8_s4_capex_1d()

# %% [markdown]
# ## Fig 9 — S5: SMR × absorption CAPEX 2D feasibility heatmap (HEADLINE)
#
# 5 × 5 Premium grid with Premium = 0 contour overlay and five anchor
# markers (FOAK, NOAK, ATB-Mid, most-optimistic, most-pessimistic). The
# headline finding is that no cell in the grid reaches Premium ≥ 0 at the
# 200 MW DC scale.

# %%
def fig9_s5_feasibility_2d() -> None:
    s5 = df[df.group == "s5_feasibility_2d"].copy()
    smr_order = ["NOAK", "Low_Mid", "ATB_Mid", "High_Mid", "FOAK"]
    abs_order = ["Bare_Low", "Mid_Low", "Baseline", "Mid_High", "Turnkey_High"]
    smr_vals = [2250, 5000, 7615, 11000, 14700]
    abs_vals = [450, 600, 750, 900, 1200]

    piv = s5.pivot_table(index="smr_capex_tag", columns="absorption_capex_tag",
                         values="premium_pct")
    piv = piv.reindex(smr_order)[abs_order]
    data = piv.values  # shape (5, 5)

    # Custom diverging colormap centered on 0
    cmap = LinearSegmentedColormap.from_list(
        "sf_div",
        [PALETTE["fill_salmon"], "#FFFFFF", PALETTE["stroke_teal"]],
        N=256,
    )
    # All data are negative in this study; force symmetric centering so the
    # Premium=0 contour reads correctly if any future tweak pushes a cell
    # above zero.
    vmax = max(abs(data.min()), abs(data.max()), 30)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    fig, ax = plt.subplots(figsize=(4.8, 3.75))
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")

    # Cell value labels
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, f"{v:+.0f}%", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(v) > 0.6 * vmax else "#000000")

    # Premium = 0 contour
    cs = ax.contour(
        np.arange(data.shape[1]),
        np.arange(data.shape[0]),
        data,
        levels=[0.0],
        colors=[PALETTE["stroke_navy"]],
        linewidths=1.4,
        linestyles="--",
    )
    try:
        ax.clabel(cs, fmt={0.0: "Premium = 0"}, fontsize=6, inline=True)
    except (ValueError, IndexError):
        pass  # contour empty (no zero-crossing in grid)

    # Tick labels: combine tag + $ value
    smr_tick = [f"{t}\n${v:,}" for t, v in zip(smr_order, smr_vals)]
    abs_tick = [f"{t}\n${v}" for t, v in zip(abs_order, abs_vals)]
    ax.set_xticks(np.arange(len(abs_order)))
    ax.set_xticklabels(abs_tick, fontsize=6)
    ax.set_yticks(np.arange(len(smr_order)))
    ax.set_yticklabels(smr_tick, fontsize=6)
    ax.set_xlabel(r"Absorption CAPEX (\$/kW$_\mathrm{c}$)")
    ax.set_ylabel(r"SMR CAPEX (\$/kW$_\mathrm{e}$)")
    # Minor-grid separators between cells (NPPH2 P5)
    ax.set_xticks(np.arange(-0.5, len(abs_order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(smr_order), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", length=0)

    # Anchor markers — placed without inline labels (overlap with cell values).
    # Anchor identity carried by marker shape + color in the legend strip below.
    grid_path = PROJECT_ROOT / "config" / "capex_grid_s5.yaml"
    with grid_path.open() as f:
        grid = yaml.safe_load(f)
    anchor_style = {
        "red_circle":    ("#D43F3A",                "o"),
        "green_circle":  (PALETTE["accent_teal"],   "s"),
        "yellow_circle": ("#F1B842",                "D"),
        "blue_circle":   (PALETTE["accent_sky"],    "^"),
        "purple_circle": (PALETTE["accent_purple"], "v"),
    }
    legend_handles: list[Line2D] = []
    anchor_offsets = {
        "red_circle": (-0.24, 0.22),
        "green_circle": (0.24, -0.22),
        "yellow_circle": (0.24, 0.22),
        "blue_circle": (-0.24, -0.22),
        "purple_circle": (0.24, 0.22),
    }
    for a in grid["anchors"]:
        i = smr_order.index(a["smr_tag"])
        j = abs_order.index(a["absorption_tag"])
        color, marker = anchor_style.get(a["marker"], ("#000000", "x"))
        dx, dy = anchor_offsets.get(a["marker"], (0.24, 0.22))
        ax.scatter(j + dx, i + dy, marker=marker, s=82,
                   facecolor=color, edgecolor="#000000", linewidth=0.9,
                   zorder=5)
        # Short label for the legend strip (drop the parenthetical aside)
        short = a["label"].split("(")[0].strip()
        legend_handles.append(
            Line2D([0], [0], marker=marker, color="none",
                   markerfacecolor=color, markeredgecolor="#000000",
                   markersize=7, label=short)
        )

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Heat-Recovery Premium (%)", fontsize=6.5)
    cbar.ax.tick_params(labelsize=6)

    # Anchor legend below the heatmap
    ax.legend(handles=legend_handles, loc="upper center",
              bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False,
              fontsize=6, handlelength=1.0, columnspacing=1.0)

    fig.tight_layout()
    save_triplet(fig, "fig9_s5_feasibility_2d", str(FIGURES))
    plt.close(fig)

fig9_s5_feasibility_2d()

# %% [markdown]
# ## Fig 10 — S6: Carbon-price crossover (4 cases × \$0/\$50/\$100/tCO2)
#
# Headline v2.7 figure. Each case's TAC is plotted as a linear function of
# carbon price (the model is linear by construction: carbon cost = price ×
# net annual CO2). Lines that slope DOWN belong to net-negative carriers
# (Cases 1-2, nuclear export displaces ERCOT marginal mix); lines that
# slope UP belong to net-positive carriers (Cases 0, 3). The vertical
# dashes mark where Case 1/2/3 lines cross Case 0 — the carbon-price
# break-even with the grid-only baseline.

# %%
def fig10_s6_carbon_price() -> None:
    s6 = df[df.group == "s6_carbon_price"].copy()
    s6 = s6.sort_values(["case_id", "carbon_price_usd_per_tco2"])

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.85))

    # Plot the 3 actual data points per case, then extrapolate linearly to
    # carbon = $250 so the crossovers visualise on-canvas.
    x_extrap = np.linspace(0, 250, 256)
    crossings: dict[int, float] = {}
    case0_at_x = None

    for cid in (0, 1, 2, 3):
        sub = s6[s6.case_id == cid]
        x = sub.carbon_price_usd_per_tco2.values
        y = sub.tac_usd_per_yr.values / 1e6
        # Slope is exact because TAC is linear in carbon price by construction.
        slope = (y[-1] - y[0]) / (x[-1] - x[0])
        intercept = y[0]
        y_extrap = intercept + slope * x_extrap

        ax.plot(x_extrap, y_extrap,
                color=CASE_LINE[cid], linewidth=1.3, zorder=2,
                label=CASE_LABEL[cid])
        ax.scatter(x, y, marker=CASE_MARKER[cid], s=42,
                   facecolor=CASE_FILL[cid], edgecolor=CASE_LINE[cid],
                   linewidth=0.9, zorder=4)

        if cid == 0:
            case0_at_x = (intercept, slope)
        else:
            c0_int, c0_slope = case0_at_x
            denom = (slope - c0_slope)
            if abs(denom) > 1e-9:
                cross_price = (c0_int - intercept) / denom
                if 0 < cross_price < 260:
                    crossings[cid] = cross_price

    # Group near-identical Case 1 / Case 2 crossovers into one annotation
    # (they sit within ~$1/tCO2 because the cogen Premium ≈ pure-nuclear).
    cid_groups: list[tuple[list[int], float]] = []
    used: set[int] = set()
    for cid in (1, 2, 3):
        if cid not in crossings or cid in used:
            continue
        partners = [cid]
        used.add(cid)
        for other in (1, 2, 3):
            if other in crossings and other not in used and abs(
                crossings[other] - crossings[cid]
            ) < 3.0:
                partners.append(other)
                used.add(other)
        cid_groups.append(
            (sorted(partners), float(np.mean([crossings[c] for c in partners])))
        )

    for cids, p_cross in cid_groups:
        c0_int, c0_slope = case0_at_x
        tac_cross = c0_int + c0_slope * p_cross
        primary = cids[-1]  # darker hue if grouped (C2 > C1)
        ax.axvline(p_cross, color=CASE_LINE[primary],
                   linestyle=":", linewidth=1.0, alpha=0.85, zorder=1)
        label = "/".join(f"C{c}" for c in cids) + f": \\${p_cross:.0f}"
        ax.annotate(
            label,
            xy=(p_cross, tac_cross),
            xytext=(7, 9 if 2 in cids else -14),
            textcoords="offset points",
            fontsize=6.5, color=CASE_LINE[primary],
            ha="left", va="center",
        )

    # Shade the "nuclear cheaper than grid" region (right of last crossover).
    if crossings:
        p_max = max(crossings.values())
        ax.axvspan(p_max, 250, alpha=0.07,
                   color=PALETTE["stroke_teal"], zorder=0)
        # Tag anchored in axes coords so it never collides with data lines.
        x_norm = ((p_max + 250) / 2) / 250
        ax.text(x_norm, 0.965, "Nuclear $<$ grid",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=6, color=PALETTE["stroke_teal"], style="italic")

    ax.set_xlim(-5, 250)
    ax.set_xlabel(r"Carbon price (\$/tCO$_2$)")
    ax.set_ylabel(r"TAC (M\$/yr)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.25, linestyle="--", linewidth=0.5)

    # Legend below the data area — keeps the plot uncluttered.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2,
              frameon=False, fontsize=6, handlelength=1.6,
              columnspacing=1.2)

    fig.tight_layout()
    save_triplet(fig, "fig10_s6_carbon_price", str(FIGURES))
    plt.close(fig)

fig10_s6_carbon_price()

# %% [markdown]
# ## Fig 11 — 8-KPI compact panel (LCOE / EPBT / Water / Abatement)
#
# Compact 2 × 2 grid covering the four KPIs that v2.6 left empty (Plan §0.5
# D #6–#8 plus LCOE for context). Bars colored by case, ATB-Mid 2023 baseline.

# %%
def fig11_kpi_panel() -> None:
    base = df[df.group == "main_baseline"].sort_values("case_id").reset_index(drop=True)
    cases = base.case_id.astype(int).values
    labels = [f"C{c}" for c in cases]
    colors = [CASE_FILL[c] for c in cases]
    edge_colors = [CASE_LINE[c] for c in cases]

    fig, axes = plt.subplots(2, 2, figsize=(5.6, 4.2))

    # (a) LCOE — $/MWh_e delivered
    lcoe = base.lcoe_usd_per_mwh_e.values
    axes[0, 0].bar(labels, lcoe, color=colors, edgecolor=edge_colors, linewidth=EDGE_LW)
    for x, v in zip(labels, lcoe):
        axes[0, 0].text(x, v + 5, f"{v:.0f}", ha="center", va="bottom",
                        fontsize=6, color="#000000")
    axes[0, 0].set_ylabel(r"LCOE (\$/MWh$_\mathrm{e}$)")
    axes[0, 0].set_axisbelow(True)
    axes[0, 0].grid(**GRID_KW)
    add_panel_label(axes[0, 0], "a")

    # (b) EPBT — years (Case 0 has no on-site plant → empty bar)
    epbt = base.epbt_years.fillna(0).values
    bars = axes[0, 1].bar(labels, epbt, color=colors, edgecolor=edge_colors, linewidth=EDGE_LW)
    for x, v, raw in zip(labels, epbt, base.epbt_years.values):
        if np.isnan(raw):
            axes[0, 1].text(x, 0.02, "n/a", ha="center", va="bottom",
                            fontsize=6, color="#666")
        else:
            axes[0, 1].text(x, v + 0.02, f"{v:.2f}", ha="center", va="bottom",
                            fontsize=6, color="#000000")
    axes[0, 1].set_ylabel(r"EPBT (years)")
    axes[0, 1].set_axisbelow(True)
    axes[0, 1].grid(**GRID_KW)
    add_panel_label(axes[0, 1], "b")

    # (c) Water footprint — total L/MWh_e (v2.7 3-tier; subpanel uses total)
    water = base.water_total_l_per_mwh_e.values
    axes[1, 0].bar(labels, water, color=colors, edgecolor=edge_colors, linewidth=EDGE_LW)
    axes[1, 0].set_yscale("log")
    for x, v in zip(labels, water):
        axes[1, 0].text(x, v * 1.18, f"{v:,.0f}", ha="center", va="bottom",
                        fontsize=6, color="#000000")
    axes[1, 0].set_ylabel(r"Water (L/MWh$_\mathrm{e}$, log)")
    axes[1, 0].set_axisbelow(True)
    axes[1, 0].grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5, which="both")
    add_panel_label(axes[1, 0], "c")

    # (d) Carbon abatement cost — $/tCO2 avoided (Cases 0,3 → n/a)
    abate = base.carbon_abatement_cost_usd_per_tco2.fillna(0).values
    raw_abate = base.carbon_abatement_cost_usd_per_tco2.values
    axes[1, 1].bar(labels, abate, color=colors, edgecolor=edge_colors, linewidth=EDGE_LW)
    for x, v, raw in zip(labels, abate, raw_abate):
        if np.isnan(raw):
            axes[1, 1].text(x, 5, "n/a", ha="center", va="bottom",
                            fontsize=6, color="#666")
        else:
            axes[1, 1].text(x, v + 5, f"\\${v:.0f}", ha="center", va="bottom",
                            fontsize=6, color="#000000")
    axes[1, 1].set_ylabel(r"Abatement (\$/tCO$_2$)")
    axes[1, 1].set_axisbelow(True)
    axes[1, 1].grid(**GRID_KW)
    add_panel_label(axes[1, 1], "d")

    for ax in axes.flat:
        ax.set_xlabel("")

    fig.tight_layout()
    save_triplet(fig, "fig_si_kpi_panel", str(FIGURES))
    plt.close(fig)

fig11_kpi_panel()

# %% [markdown]
# ## Fig 4-bis (v2.7) — Absorption Chiller Value Decomposition (Plan §6 Patch 1)
#
# Waterfall decomposition of the marginal value of adding absorption to a
# nuclear-only Case 1 system. Components from src/results/value_decomposition.py
# (read via outputs/figures/value_decomp_case2.csv).

# %%
def fig4bis_value_decomp() -> None:
    decomp_path = OUTPUTS / "figures" / "value_decomp_case2.csv"
    if not decomp_path.exists():
        print(f"[fig4bis] missing {decomp_path}; skipping")
        return
    vd = pd.read_csv(decomp_path)
    base_row = vd[vd.matching_key == "main_baseline/base"].iloc[0]

    # Waterfall order: net = sum of these (positive adds, negative subtracts)
    components = [
        ("VCC\nsaved",
         base_row.vcc_elec_saved_usd_per_yr / 1e6),
        ("Power\nlost",
         base_row.turbine_gen_lost_usd_per_yr / 1e6),
        ("Abs.\nCAPEX",
         base_row.absorption_capex_fom_usd_per_yr / 1e6),
        ("Gate\nbackup",
         base_row.crystal_cutoff_backup_usd_per_yr / 1e6),
        ("Water\ncost",
         base_row.extra_water_cost_usd_per_yr / 1e6),
    ]
    net = base_row.net_value_of_absorption_usd_per_yr / 1e6
    residual = base_row.residual_usd_per_yr / 1e6

    fig, ax = plt.subplots(figsize=(SINGLE_W, 2.75))

    # Cumulative running total for the waterfall
    cum = 0.0
    x_pos = []
    heights = []
    bottoms = []
    colors = []
    for name, val in components:
        x_pos.append(name)
        heights.append(val)
        bottoms.append(cum)
        colors.append(
            PALETTE["accent_teal"] if val > 0 else PALETTE["fill_salmon"]
        )
        cum += val

    ax.bar(
        x_pos, heights, bottom=bottoms, color=colors,
        edgecolor="#000000", linewidth=EDGE_LW, width=0.58, alpha=0.88,
    )

    # Net result as a final summary bar
    x_pos.append("Net vs\nCase 1")
    heights.append(net)
    bottoms.append(0.0)
    net_color = (
        PALETTE["accent_teal"] if net > 0 else PALETTE["fill_salmon"]
    )
    ax.bar(
        ["Net vs\nCase 1"], [net], color=net_color,
        edgecolor="#000000", linewidth=EDGE_LW, width=0.58, alpha=0.88,
    )

    # Annotate only values large enough to read cleanly in print. Near-zero
    # components are visible as bars but left unlabeled to avoid a collision
    # cluster in the top margin.
    for x, h, b in zip(x_pos[:-1], heights[:-1], bottoms[:-1]):
        y = b + h
        if abs(h) > 0.5:
            # Inline label just past the bar end
            offset = 0.30 if h >= 0 else -0.30
            ax.text(
                x, y + offset, f"\\${h:+.1f}M",
                ha="center", va="center", fontsize=6.0, color="#000000",
            )

    # Final summary bar label
    net_color_label = "#000000"
    ax.text(
        x_pos[-1], net + (0.30 if net >= 0 else -0.30),
        f"\\${net:+.1f}M",
        ha="center", va="center", fontsize=6.5, color=net_color_label,
        fontweight="bold",
    )

    # Residual annotation (model-side leakage Δ for honesty), top-right corner
    if abs(residual) >= 1.0:
        ax.text(
            0.98, 0.94,
            f"Residual \\${residual:+.1f}M/yr",
            transform=ax.transAxes, fontsize=5.5, color="#666666",
            ha="right", va="top",
        )

    ax.axhline(0, color="#000000", linewidth=0.7)
    ax.set_ylabel("Δ vs Case 1 TAC (M\\$/yr)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    plt.setp(ax.get_xticklabels(), fontsize=6.0)
    # Give some headroom so the leader-line text has somewhere to live
    ymin = min(min(bottoms), -6.0)
    ymax = max(heights) + 1.2
    ax.set_ylim(ymin, ymax)

    fig.tight_layout()
    save_triplet(fig, "fig4bis_value_decomp", str(FIGURES))
    plt.close(fig)

fig4bis_value_decomp()

# %% [markdown]
# ## Fig 11 (v2.7) — S7 WACC vs CAPEX learning leverage (Plan §6 Patch 3)
#
# Side-by-side ΔPremium comparison: the WACC mini-scan (5% → 10%) vs the
# S4 CAPEX learning trajectory (FOAK → NOAK), both holding Case 0 at the
# ATB baseline so each bar isolates one lever.

# %%
def fig11_s7_wacc_leverage() -> None:
    # S7 rows
    s7 = df[df.group == "s7_wacc"].sort_values("wacc_effective")
    # S4 rows (Case 2 only — match the S7 Case 2 lens)
    s4 = (
        df[(df.group == "s4_capex") & (df.case_id == 2)]
        .copy()
        .sort_values(
            "reactor_scenario", key=lambda s: s.map({"FOAK": 0, "ATB_Mid": 1, "NOAK": 2})
        )
    )

    if s7.empty or s4.empty:
        print("[fig11] missing s7 or s4 rows; skipping")
        return

    # Premium points (percentage)
    wacc_pts = list(zip(s7.wacc_effective.values, s7.premium_pct.values))
    capex_pts = list(zip(s4.reactor_scenario.values, s4.premium_pct.values))

    # ΔPremium spans
    wacc_min = min(p for _, p in wacc_pts)
    wacc_max = max(p for _, p in wacc_pts)
    capex_min = min(p for _, p in capex_pts)
    capex_max = max(p for _, p in capex_pts)

    fig, axes = plt.subplots(2, 1, figsize=(SINGLE_W, 3.4), sharey=True)

    # Left: WACC sweep (5% / 6.7% / 10%)
    waccs = [w * 100 for w, _ in wacc_pts]
    prems_wacc = [p for _, p in wacc_pts]
    colors_wacc = [
        PALETTE["accent_teal"] if p > prems_wacc[1] else
        (PALETTE["fill_salmon"] if p < prems_wacc[1] else PALETTE["fill_gray"])
        for p in prems_wacc
    ]
    bars_l = axes[0].bar(
        [f"{w:.1f}%" for w in waccs], prems_wacc,
        color=colors_wacc, edgecolor="#000000", linewidth=EDGE_LW, width=0.6,
    )
    for b, v in zip(bars_l, prems_wacc):
        axes[0].text(
            b.get_x() + b.get_width() / 2,
            v + (8 if v < 0 else -8),
            f"{v:.0f}%",
            ha="center", va="center", fontsize=7, color="#000000",
        )
    span_w = wacc_max - wacc_min
    axes[0].text(0.00, 1.04, f"a  WACC sweep (span {span_w:+.0f} pp)",
                 transform=axes[0].transAxes, ha="left", va="bottom",
                 fontsize=7, fontweight="bold")
    axes[0].set_ylabel("Heat-Recovery Premium (%)")
    axes[0].set_xlabel("WACC")
    axes[0].axhline(0, color="#000000", linewidth=0.6, linestyle=":")
    axes[0].grid(**GRID_KW)
    axes[0].set_axisbelow(True)

    # Right: CAPEX sweep (FOAK / ATB_Mid / NOAK)
    labels_capex = [s.replace("ATB_Mid", "ATB-Mid") for s, _ in capex_pts]
    prems_capex = [p for _, p in capex_pts]
    colors_capex = [
        PALETTE["accent_teal"] if p > prems_capex[1] else
        (PALETTE["fill_salmon"] if p < prems_capex[1] else PALETTE["fill_gray"])
        for p in prems_capex
    ]
    bars_r = axes[1].bar(
        labels_capex, prems_capex,
        color=colors_capex, edgecolor="#000000", linewidth=EDGE_LW, width=0.6,
    )
    for b, v in zip(bars_r, prems_capex):
        axes[1].text(
            b.get_x() + b.get_width() / 2,
            v + (8 if v < 0 else -8),
            f"{v:.0f}%",
            ha="center", va="center", fontsize=7, color="#000000",
        )
    span_c = capex_max - capex_min
    axes[1].text(0.00, 1.04, f"b  CAPEX learning (span {span_c:+.0f} pp)",
                 transform=axes[1].transAxes, ha="left", va="bottom",
                 fontsize=7, fontweight="bold")
    axes[1].set_xlabel("SMR CAPEX scenario")
    axes[1].axhline(0, color="#000000", linewidth=0.6, linestyle=":")
    axes[1].grid(**GRID_KW)
    axes[1].set_axisbelow(True)

    # Sync y-limits so the comparison is fair
    ymin = min(min(prems_wacc), min(prems_capex))
    ymax = max(max(prems_wacc), max(prems_capex))
    pad = 0.06 * (ymax - ymin)
    for ax in axes:
        ax.set_ylim(ymin - pad, ymax + pad)

    # Caption hook: which lever wins?
    ratio = span_c / span_w if span_w != 0 else float("inf")
    note = (
        f"CAPEX learning provides {ratio:.1f}× the Premium leverage of WACC reduction"
        if ratio > 1.0 else
        f"WACC reduction provides {1.0 / ratio:.1f}× the Premium leverage of CAPEX learning"
    )
    fig.text(
        0.5, -0.01, note, ha="center", fontsize=6.5, color="#000000",
        style="italic",
    )

    fig.tight_layout(rect=(0.0, 0.06, 1.0, 0.98))
    save_triplet(fig, "fig11_s7_wacc_leverage", str(FIGURES))
    plt.close(fig)

fig11_s7_wacc_leverage()

# %% [markdown]
# ## SI Water — 4 cases × 3-tier water footprint stacked (Plan §6 Patch 2)
#
# Direct site (DC cooling-tower + absorption Q_reject) vs indirect generation
# (Macknick 2012 per-source factors) vs scarcity-weighted (Aqueduct ERCOT
# South 0.65 baseline). Surfaces the v2.7 counterintuitive finding that Case
# 2's absorption chiller raises *direct* site water even while it lowers
# indirect generation water.

# %%
def fig_si_water_3tier() -> None:
    base = df[df.group == "main_baseline"].sort_values("case_id").reset_index(drop=True)
    cases = base.case_id.astype(int).values
    labels = [f"C{c}" for c in cases]

    direct = base.water_direct_site_l_per_mwh_e.values
    indirect = base.water_indirect_generation_l_per_mwh_e.values
    total = base.water_total_l_per_mwh_e.values
    scarcity = base.water_scarcity_m3_world_eq_per_mwh_e.values

    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.0),
                              gridspec_kw={"width_ratios": [1.0, 1.0]})

    # Left: stacked direct + indirect (linear scale; uses two colors)
    axes[0].bar(labels, direct, color=PALETTE["fill_blue"],
                edgecolor="#000000", linewidth=EDGE_LW, width=0.62,
                label="Direct site (DC cooling tower)")
    axes[0].bar(labels, indirect, bottom=direct, color=PALETTE["fill_salmon"],
                edgecolor="#000000", linewidth=EDGE_LW, width=0.62,
                label="Indirect generation (Macknick)")
    for i, (d, t) in enumerate(zip(direct, total)):
        axes[0].text(i, t + max(total) * 0.025,
                     f"{t:,.0f}", ha="center", va="bottom",
                     fontsize=6, color="#000000")
        if d > 1.0:
            axes[0].text(i, d / 2, f"{d:.0f}", ha="center", va="center",
                         fontsize=5.5, color="#FFFFFF")
    axes[0].set_ylabel("Water (L/MWh$_\\mathrm{e\\,IT}$)")
    axes[0].set_axisbelow(True)
    axes[0].grid(**GRID_KW)
    axes[0].legend(loc="upper center", fontsize=5.5, frameon=False,
                    ncol=1, bbox_to_anchor=(0.5, -0.10))
    add_panel_label(axes[0], "a")

    # Right: scarcity-weighted (m3 world-eq / MWh_e_IT)
    bars = axes[1].bar(labels, scarcity, color=[CASE_FILL[c] for c in cases],
                        edgecolor=[CASE_LINE[c] for c in cases], linewidth=EDGE_LW, width=0.62)
    for b, v in zip(bars, scarcity):
        axes[1].text(b.get_x() + b.get_width() / 2,
                     v + max(scarcity) * 0.025,
                     f"{v:.2f}", ha="center", va="bottom",
                     fontsize=6, color="#000000")
    axes[1].set_ylabel("Scarcity-weighted\n(m$^3$ world-eq/MWh$_\\mathrm{e\\,IT}$)")
    axes[1].set_axisbelow(True)
    axes[1].grid(**GRID_KW)
    add_panel_label(axes[1], "b")

    # Below the figure, surface the absorption-vs-VCC reversal as caption hook
    delta_direct = direct[2] - direct[1]   # Case 2 - Case 1 (direct site)
    delta_indirect = indirect[2] - indirect[1]
    note = (
        f"Case 2 vs Case 1: direct site {delta_direct:+.1f}, "
        f"indirect generation {delta_indirect:+.0f} L/MWh$_\\mathrm{{e\\,IT}}$ — "
        f"absorption chiller trades indirect for direct water"
    )
    fig.text(0.5, -0.06, note, ha="center", fontsize=6.5, color="#000000",
             style="italic")

    fig.tight_layout()
    save_triplet(fig, "fig_si_water_3tier", str(FIGURES))
    plt.close(fig)

fig_si_water_3tier()

# %% [markdown]
# ## Graphical Abstract — 2-panel (S5 viability map + S6 carbon-price ladder)

# %%
def graphical_abstract() -> None:
    apply_sci_style("poster")

    # ---- Left panel data: S5 SMR×absorption viability heatmap ----------
    s5 = df[df.group == "s5_feasibility_2d"].copy()
    smr_order = ["NOAK", "Low_Mid", "ATB_Mid", "High_Mid", "FOAK"]
    abs_order = ["Bare_Low", "Mid_Low", "Baseline", "Mid_High", "Turnkey_High"]
    smr_vals = [2250, 5000, 7615, 11000, 14700]
    abs_vals = [450, 600, 750, 900, 1200]
    piv = s5.pivot_table(index="smr_capex_tag", columns="absorption_capex_tag",
                         values="premium_pct").reindex(smr_order)[abs_order]
    data = piv.values

    cmap = LinearSegmentedColormap.from_list(
        "sf_div",
        [PALETTE["fill_salmon"], "#FFFFFF", PALETTE["stroke_teal"]],
        N=256,
    )
    vmax = max(abs(data.min()), abs(data.max()), 30)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    # ---- Right panel data: S6 carbon-price crossover -------------------
    s6 = df[df.group == "s6_carbon_price"].copy().sort_values(
        ["case_id", "carbon_price_usd_per_tco2"]
    )
    x_extrap = np.linspace(0, 250, 256)
    case_lines: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    case0_at_x: tuple[float, float] | None = None
    crossings: dict[int, float] = {}
    for cid in (0, 1, 2, 3):
        sub = s6[s6.case_id == cid]
        x = sub.carbon_price_usd_per_tco2.values
        y = sub.tac_usd_per_yr.values / 1e6
        slope = (y[-1] - y[0]) / (x[-1] - x[0])
        intercept = y[0]
        case_lines[cid] = (x_extrap, intercept + slope * x_extrap, x, y)
        if cid == 0:
            case0_at_x = (intercept, slope)
        else:
            c0_int, c0_slope = case0_at_x
            denom = (slope - c0_slope)
            if abs(denom) > 1e-9:
                p_cross = (c0_int - intercept) / denom
                if 0 < p_cross < 260:
                    crossings[cid] = p_cross

    # ---- Compose -----------------------------------------------------------
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.0, 5.6),
                                    gridspec_kw={"width_ratios": [1.0, 1.0]})

    # Left: S5 heatmap
    im = axL.imshow(data, cmap=cmap, norm=norm, aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            axL.text(j, i, f"{v:+.0f}%", ha="center", va="center", fontsize=12,
                     color="white" if abs(v) > 0.6 * vmax else "#000000")
    axL.contour(
        np.arange(data.shape[1]),
        np.arange(data.shape[0]),
        data,
        levels=[0.0],
        colors=[PALETTE["stroke_navy"]],
        linewidths=2.0,
        linestyles="--",
    )
    axL.set_xticks(np.arange(len(abs_order)))
    axL.set_xticklabels([f"${v}" for v in abs_vals], fontsize=11)
    axL.set_yticks(np.arange(len(smr_order)))
    axL.set_yticklabels([f"${v:,}" for v in smr_vals], fontsize=11)
    axL.set_xlabel(r"Absorption CAPEX (\$/kW$_\mathrm{c}$)", fontsize=13)
    axL.set_ylabel(r"SMR CAPEX (\$/kW$_\mathrm{e}$)", fontsize=13)
    axL.set_xticks(np.arange(-0.5, len(abs_order), 1), minor=True)
    axL.set_yticks(np.arange(-0.5, len(smr_order), 1), minor=True)
    axL.grid(which="minor", color="white", linewidth=2.0)
    axL.tick_params(which="minor", length=0)
    add_panel_label(axL, "a", x=-0.16, y=1.04, fontsize=15)
    cbar = fig.colorbar(im, ax=axL, fraction=0.046, pad=0.04)
    cbar.set_label("Heat-Recovery Premium (%)", fontsize=12)

    # Right: S6 carbon-price crossover
    for cid in (0, 1, 2, 3):
        x_e, y_e, x_pts, y_pts = case_lines[cid]
        axR.plot(x_e, y_e,
                 color=CASE_LINE[cid], linewidth=2.0, zorder=2,
                 label=f"C{cid}")
        axR.scatter(x_pts, y_pts, marker=CASE_MARKER[cid], s=80,
                    facecolor=CASE_FILL[cid], edgecolor=CASE_LINE[cid],
                    linewidth=1.0, zorder=4)
    # Group near-identical Case 1 / Case 2 crossovers — same rule as Fig 10.
    cid_groups: list[tuple[list[int], float]] = []
    used: set[int] = set()
    for cid in (1, 2, 3):
        if cid not in crossings or cid in used:
            continue
        partners = [cid]
        used.add(cid)
        for other in (1, 2, 3):
            if other in crossings and other not in used and abs(
                crossings[other] - crossings[cid]
            ) < 3.0:
                partners.append(other)
                used.add(other)
        cid_groups.append(
            (sorted(partners), float(np.mean([crossings[c] for c in partners])))
        )

    for cids, p_cross in cid_groups:
        c0_int, c0_slope = case0_at_x
        tac_cross = c0_int + c0_slope * p_cross
        primary = cids[-1]
        axR.axvline(p_cross, color=CASE_LINE[primary],
                    linestyle=":", linewidth=1.4, alpha=0.85, zorder=1)
        label = "/".join(f"C{c}" for c in cids) + f": \\${p_cross:.0f}"
        axR.annotate(
            label,
            xy=(p_cross, tac_cross),
            xytext=(10, 12 if 2 in cids else -22),
            textcoords="offset points",
            fontsize=11, color=CASE_LINE[primary], ha="left",
        )
    if crossings:
        p_max = max(crossings.values())
        axR.axvspan(p_max, 250, alpha=0.07,
                    color=PALETTE["stroke_teal"], zorder=0)
        x_norm = ((p_max + 250) / 2) / 250
        axR.text(x_norm, 0.965, "Nuclear $<$ grid",
                 transform=axR.transAxes, ha="center", va="top",
                 fontsize=11, color=PALETTE["stroke_teal"], style="italic")

    axR.set_xlim(0, 250)
    axR.set_xlabel(r"Carbon price (\$/tCO$_2$)", fontsize=13)
    axR.set_ylabel(r"TAC (M\$/yr)", fontsize=13)
    axR.set_axisbelow(True)
    axR.grid(axis="y", alpha=0.25, linestyle="--", linewidth=0.6)
    axR.legend(loc="upper left", frameon=False, fontsize=11,
               handlelength=1.4, ncol=2)
    add_panel_label(axR, "b", x=-0.16, y=1.04, fontsize=15)

    fig.tight_layout()
    save_triplet(fig, "graphical_abstract", str(FIGURES))
    plt.close(fig)
    apply_sci_style("ae_single")  # restore single-column for any later figs

graphical_abstract()

# %% [markdown]
# ## Done — list the outputs

# %%
generated = sorted(FIGURES.glob("*.pdf"))
print(f"\n{'Wrote ' + str(len(generated)) + ' figures (PDF + SVG + PNG triplet each) to ' + str(FIGURES):s}")
for p in generated:
    print(f"  {p.name}")
