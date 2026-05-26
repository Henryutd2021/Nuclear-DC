"""Generate every v2.7 paper figure into outputs/figures/.

Reads outputs/master_kpi_table.csv (73 rows from scripts/run_all_analyses.py)
and the Case 2 hourly dispatch from outputs/main_baseline/case2/dispatch.csv.gz,
then renders Fig 2–11 + the Graphical Abstract following the sci-figure skill
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

Fig 1 is the TikZ system schematic and stays in LaTeX — not produced here.

Run from project root:

    PYTHONPATH=. python notebooks/make_v27_figures.py
"""

# %% [markdown]
# # v2.7 paper figure pipeline
#
# Builds 10 main figures plus a Graphical Abstract for the plan-v2.7 Applied
# Energy manuscript. Each figure exports PDF + SVG + PNG via the sci-figure
# helper `save_triplet`.
#
# Inputs: `outputs/master_kpi_table.csv` (73 rows) and `outputs/main_baseline/case2/dispatch.csv.gz`.
# Outputs: `outputs/figures/fig{2..11}_*.{pdf,svg,png}` plus
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
    0: PALETTE["case0"],
    1: PALETTE["case1"],
    2: PALETTE["case2"],
    3: PALETTE["case4"],  # repurpose case4 hue for new Case 3 NGCC (warm/dirty)
}
CASE_MARKER = {0: "o", 1: "s", 2: "D", 3: "^"}

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

    fig, ax = plt.subplots(figsize=(3.8, 2.8))
    x = np.arange(len(cases))
    bw = 0.62

    # Stack positive components
    bot = np.zeros_like(capex)
    components = [
        ("Capital × CRF", capex, PALETTE["comp_capital"]),
        ("Fixed O&M", fom, PALETTE["comp_om"]),
        ("Variable O&M", vom, PALETTE["fill_gray"]),
        ("Fuel", fuel, PALETTE["comp_fuel"]),
        ("Grid import", grid_pos, PALETTE["comp_grid_buy"]),
    ]
    for lab, vals, color in components:
        if vals.sum() < 1e-3:
            continue
        ax.bar(x, vals, bottom=bot, width=bw, color=color, edgecolor="#000000",
               linewidth=0.6, label=lab)
        bot = bot + vals

    # Below-zero grid export bar (revenue offset)
    if (grid_neg < 0).any():
        ax.bar(x, grid_neg, width=bw,
               color=PALETTE["comp_grid_sell"], edgecolor="#000000", linewidth=0.6,
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
    ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3,
              frameon=False, columnspacing=1.0, handlelength=1.4)

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

    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    # Predefined offset directions for year tags so 3 years per case don't pile up
    year_offsets = {2022: (4, 6), 2023: (4, -8), 2024: (-12, -10)}
    for cid in (0, 1, 2, 3):
        sub = s2[s2.case_id == cid].sort_values("year")
        ax.plot(sub.tac_m, sub.co2_kt,
                color=CASE_COLOR[cid], linewidth=0.8, alpha=0.5, zorder=2)
        ax.scatter(sub.tac_m, sub.co2_kt,
                   marker=CASE_MARKER[cid], s=55,
                   facecolor=CASE_COLOR[cid], edgecolor="#000000", linewidth=0.6,
                   zorder=3, label=CASE_LABEL[cid])
        # Annotate only the 2022 endpoint per case so year clusters don't pile up
        head = sub[sub.year == 2022].iloc[0]
        ax.annotate(f"{int(head.year)}–{int(sub.year.max())}",
                    xy=(head.tac_m, head.co2_kt),
                    xytext=(6, 6),
                    textcoords="offset points",
                    fontsize=5.5, color="#444444")

    ax.set_xlabel(r"TAC (M\$/yr)")
    ax.set_ylabel(r"Annual CO$_2$ (kt CO$_2$/yr)")
    ax.set_axisbelow(True)
    ax.grid(axis="both", alpha=0.3, linestyle="--", linewidth=0.5)
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
        ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)

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

        ax.text(0.02, 0.92, name, transform=ax.transAxes, fontsize=7,
                fontweight="bold", color="#222222")

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

    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    for cid in (1, 2):
        sub = s1[s1.case_id == cid]
        ax.plot(sub.pue, sub.premium_pct,
                marker=CASE_MARKER[cid], markersize=6,
                color=CASE_COLOR[cid], linewidth=1.6,
                markerfacecolor=CASE_COLOR[cid],
                markeredgecolor="#000000", markeredgewidth=0.6,
                label=CASE_LABEL[cid])

    ax.axhline(0, color=PALETTE["accent_teal"], linestyle="--",
               linewidth=1.0, alpha=0.8, label="Premium = 0")
    ax.set_xlabel("PUE")
    ax.set_ylabel("Heat-Recovery Premium (%)")
    ax.set_xticks([1.10, 1.30, 1.50])
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", frameon=False, fontsize=6.5)
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

    fig, ax = plt.subplots(figsize=(4.0, 2.8))
    for i, cid in enumerate(cases):
        vals = [
            s2[(s2.year == y) & (s2.case_id == cid)].premium_pct.iloc[0]
            for y in years
        ]
        offset = (i - (len(cases) - 1) / 2) * bar_w
        ax.bar(x + offset, vals, width=bar_w,
               color=CASE_COLOR[cid], edgecolor="#000000", linewidth=0.6,
               label=CASE_LABEL[cid])

    ax.axhline(0, color="#000000", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlabel("ERCOT year")
    ax.set_ylabel("Heat-Recovery Premium (%)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
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
    colors = [CASE_COLOR[c] for c in cases]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 2.6))

    # Panel a — ΔTAC with BESS
    ax1.bar(labels, wide.delta_M.values, color=colors,
            edgecolor="#000000", linewidth=0.6)
    ax1.axhline(0, color="#000000", linewidth=0.7)
    ax1.set_ylabel(r"$\Delta$TAC with BESS (M\$/yr)")
    ax1.set_xlabel("Case")
    ax1.set_axisbelow(True)
    ax1.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    add_panel_label(ax1, "a")

    # Panel b — $/tCO2 abated
    ax2.bar(labels, wide.abate_usd_per_tco2.values, color=colors,
            edgecolor="#000000", linewidth=0.6)
    ax2.axhline(0, color="#000000", linewidth=0.7)
    ax2.set_ylabel(r"Carbon abatement (\$/tCO$_2$)")
    ax2.set_xlabel("Case")
    ax2.set_axisbelow(True)
    ax2.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    add_panel_label(ax2, "b")

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

    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for i, cid in enumerate((1, 2)):
        vals = [
            s4[(s4.reactor_scenario == s) & (s4.case_id == cid)].premium_pct.iloc[0]
            for s in scen_order
        ]
        offset = (i - 0.5) * bar_w
        ax.bar(x + offset, vals, width=bar_w,
               color=CASE_COLOR[cid], edgecolor="#000000", linewidth=0.6,
               label=CASE_LABEL[cid])
        for xi, v in zip(x + offset, vals):
            ax.text(xi, v - 8 if v < 0 else v + 4, f"{v:+.0f}%",
                    ha="center", va="top" if v < 0 else "bottom",
                    fontsize=5.5, color="#000000")

    ax.axhline(0, color="#000000", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(["FOAK\n$14,700", "ATB-Mid\n$7,615", "NOAK\n$2,250"], fontsize=6.5)
    ax.set_xlabel(r"BWRX-300 OCC (\$/kW$_\mathrm{e}$)")
    ax.set_ylabel("Heat-Recovery Premium (%)")
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    ax.legend(loc="lower right", frameon=False, fontsize=6)
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

    fig, ax = plt.subplots(figsize=(4.2, 3.6))
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
    for a in grid["anchors"]:
        i = smr_order.index(a["smr_tag"])
        j = abs_order.index(a["absorption_tag"])
        color, marker = anchor_style.get(a["marker"], ("#000000", "x"))
        ax.scatter(j, i, marker=marker, s=120,
                   facecolor=color, edgecolor="#000000", linewidth=1.0,
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

    fig, ax = plt.subplots(figsize=(4.4, 3.3))

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
                color=CASE_COLOR[cid], linewidth=1.3, zorder=2,
                label=CASE_LABEL[cid])
        ax.scatter(x, y, marker=CASE_MARKER[cid], s=42,
                   facecolor=CASE_COLOR[cid], edgecolor="#000000",
                   linewidth=0.6, zorder=4)

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
        ax.axvline(p_cross, color=CASE_COLOR[primary],
                   linestyle=":", linewidth=1.0, alpha=0.85, zorder=1)
        label = "/".join(f"C{c}" for c in cids) + f": \\${p_cross:.0f}"
        ax.annotate(
            label,
            xy=(p_cross, tac_cross),
            xytext=(7, 9 if 2 in cids else -14),
            textcoords="offset points",
            fontsize=6.5, color=CASE_COLOR[primary],
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

    ax.set_xlim(0, 250)
    ax.set_xlabel(r"Carbon price (\$/tCO$_2$)")
    ax.set_ylabel(r"TAC (M\$/yr)")
    ax.set_axisbelow(True)
    ax.grid(axis="both", alpha=0.25, linestyle="--", linewidth=0.5)

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
    colors = [CASE_COLOR[c] for c in cases]

    fig, axes = plt.subplots(2, 2, figsize=(5.6, 4.2))

    # (a) LCOE — $/MWh_e delivered
    lcoe = base.lcoe_usd_per_mwh_e.values
    axes[0, 0].bar(labels, lcoe, color=colors, edgecolor="#000000", linewidth=0.6)
    for x, v in zip(labels, lcoe):
        axes[0, 0].text(x, v + 5, f"{v:.0f}", ha="center", va="bottom",
                        fontsize=6, color="#000000")
    axes[0, 0].set_ylabel(r"LCOE (\$/MWh$_\mathrm{e}$)")
    axes[0, 0].set_axisbelow(True)
    axes[0, 0].grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    add_panel_label(axes[0, 0], "a")

    # (b) EPBT — years (Case 0 has no on-site plant → empty bar)
    epbt = base.epbt_years.fillna(0).values
    bars = axes[0, 1].bar(labels, epbt, color=colors, edgecolor="#000000", linewidth=0.6)
    for x, v, raw in zip(labels, epbt, base.epbt_years.values):
        if np.isnan(raw):
            axes[0, 1].text(x, 0.02, "n/a", ha="center", va="bottom",
                            fontsize=6, color="#666")
        else:
            axes[0, 1].text(x, v + 0.02, f"{v:.2f}", ha="center", va="bottom",
                            fontsize=6, color="#000000")
    axes[0, 1].set_ylabel(r"EPBT (years)")
    axes[0, 1].set_axisbelow(True)
    axes[0, 1].grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    add_panel_label(axes[0, 1], "b")

    # (c) Water footprint — L/MWh_e delivered (log scale: nuclear ~10× others)
    water = base.water_l_per_mwh_e.values
    axes[1, 0].bar(labels, water, color=colors, edgecolor="#000000", linewidth=0.6)
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
    axes[1, 1].bar(labels, abate, color=colors, edgecolor="#000000", linewidth=0.6)
    for x, v, raw in zip(labels, abate, raw_abate):
        if np.isnan(raw):
            axes[1, 1].text(x, 5, "n/a", ha="center", va="bottom",
                            fontsize=6, color="#666")
        else:
            axes[1, 1].text(x, v + 5, f"\\${v:.0f}", ha="center", va="bottom",
                            fontsize=6, color="#000000")
    axes[1, 1].set_ylabel(r"Abatement (\$/tCO$_2$)")
    axes[1, 1].set_axisbelow(True)
    axes[1, 1].grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
    add_panel_label(axes[1, 1], "d")

    for ax in axes.flat:
        ax.set_xlabel("")

    fig.tight_layout()
    save_triplet(fig, "fig11_kpi_panel", str(FIGURES))
    plt.close(fig)

fig11_kpi_panel()

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
                 color=CASE_COLOR[cid], linewidth=2.0, zorder=2,
                 label=f"C{cid}")
        axR.scatter(x_pts, y_pts, marker=CASE_MARKER[cid], s=80,
                    facecolor=CASE_COLOR[cid], edgecolor="#000000",
                    linewidth=0.8, zorder=4)
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
        axR.axvline(p_cross, color=CASE_COLOR[primary],
                    linestyle=":", linewidth=1.4, alpha=0.85, zorder=1)
        label = "/".join(f"C{c}" for c in cids) + f": \\${p_cross:.0f}"
        axR.annotate(
            label,
            xy=(p_cross, tac_cross),
            xytext=(10, 12 if 2 in cids else -22),
            textcoords="offset points",
            fontsize=11, color=CASE_COLOR[primary], ha="left",
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
    axR.grid(alpha=0.25, linestyle="--", linewidth=0.6)
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
