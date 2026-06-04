#!/usr/bin/env python3
"""Build the two consolidated (multi-panel) manuscript figures from the same
data and styling helpers used by paper_figures.ipynb, without modifying that
notebook. Panel plotting code is reused verbatim from the notebook cells, only
adapted to draw onto provided axes instead of creating a standalone figure.

Outputs:
  fig_operation_value.pdf       (dispatch winter/summer + absorption value waterfall)
  fig_baseline_economics.pdf    (TAC stack + cost-carbon scatter + nuclear CO2 accounting)

Run from the repository root:  python3 notebooks/make_composite_figures.py
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")

PROJECT_ROOT = Path("/home/honglin/Nuclear-DC")
NB = PROJECT_ROOT / "notebooks" / "paper_figures.ipynb"
NAT_FIGS = PROJECT_ROOT / "MANUSCRIPT" / "Nature Energy" / "figures"

# --- load notebook setup cells (palette, helpers, df) into this namespace ----
nb = json.load(open(NB))
_g = {}
for i in (2, 3, 4):
    exec(compile("".join(nb["cells"][i]["source"]), f"cell{i}", "exec"), _g)
_g.pop("__name__", None)
globals().update(_g)  # PALETTE, df, save_triplet, add_panel_label, BODY_W, MAIN_FILLS, ...

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial"],
        "font.size": 8.0,
        "axes.labelsize": 8.0,
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.0,
        "legend.fontsize": 8.0,
        "legend.title_fontsize": 8.0,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
    }
)

COMPOSITE_HSPACE = 0.28
FIG2_WSPACE = 0.30
FIG2_HSPACE = 0.48
FIG2_LEFT = 0.12
FIG2_RIGHT = 0.98


# =====================================================================
# Panel builders (verbatim plotting logic from the notebook, ax-driven)
# =====================================================================

def panel_tac_stack(ax):
    """Cell 7 logic -> draws TAC stack onto ax, returns legend handles."""
    base = df[df.group == "main_baseline"].sort_values("case_id").reset_index(drop=True)
    cases = base.case_id.astype(int).values
    labels = [f"C{c}" for c in cases]
    capex = base.capex_annual_usd.values / 1e6
    fom = base.fom_annual_usd.values / 1e6
    vom = base.vom_annual_usd.values / 1e6
    fuel = base.fuel_annual_usd.values / 1e6
    grid = base.grid_annual_usd.values / 1e6
    tac = base.tac_usd_per_yr.values / 1e6
    premium = base.premium_pct.values
    grid_pos = np.where(grid > 0, grid, 0.0)
    grid_neg = np.where(grid < 0, grid, 0.0)

    x = np.arange(len(cases))
    bw = 0.62
    bot = np.zeros_like(capex)
    for lab, vals, color, alpha, hatch in [
        ("Capital", capex, MAIN_FILLS[0], 0.92, None),
        ("Fixed O&M", fom, MAIN_FILLS[1], 0.92, None),
        ("Variable O&M", vom, TAC_STACK_VOM_FILL, 0.92, None),
        ("Fuel", fuel, TAC_STACK_FUEL_FILL, 0.88, None),
    ]:
        if vals.sum() < 1e-3:
            continue
        ax.bar(x, vals, bottom=bot, width=bw, color=color, edgecolor=BLOCK_EDGE,
               linewidth=EDGE_LW, alpha=alpha, hatch=hatch, label=lab)
        bot = bot + vals
    c0_import = np.where(cases == 0, grid_pos, 0.0)
    other_import = np.where(cases != 0, grid_pos, 0.0)
    if other_import.sum() >= 1e-3:
        ax.bar(x, other_import, bottom=bot, width=bw, color=MAIN_FILLS[0],
               edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, alpha=0.52, hatch="////")
    if c0_import.sum() >= 1e-3:
        ax.bar(x, c0_import, bottom=bot, width=bw, color=TAC_STACK_C0_IMPORT_FILL,
               edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, alpha=1.0)
    bot = bot + grid_pos
    if (grid_neg < 0).any():
        ax.bar(x, grid_neg, width=bw, color=GRID_EXPORT_FILL, edgecolor=BLOCK_EDGE,
               linewidth=EDGE_LW, alpha=GRID_EXPORT_ALPHA)
    ptc = np.nan_to_num(base["ptc_annual_usd"].to_numpy(dtype=float)) / 1e6
    if (ptc < 0).any():
        ax.bar(x, ptc, bottom=grid_neg, width=bw, color="#7FB7A6",
               edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, alpha=0.85)
    stack_top = capex + fom + vom + fuel + grid_pos
    for xi, tac_i, prem_i, top in zip(x, tac, premium, stack_top):
        ax.scatter(xi, tac_i, marker="_", s=320, color=MAIN_STROKES[3], linewidth=1.6, zorder=5)
        ax.annotate(f"TAC {tac_i:.0f}\nM = {prem_i:+.0f}%", xy=(xi, top),
                    xytext=(0, VALUE_LABEL_OFFSET_PT), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color="#000000")
    ax.axhline(0, **ZERO_LINE_KW)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"Annualized cost (M\$ yr$^{-1}$)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    return [
        Patch(facecolor=MAIN_FILLS[0], edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, label="Capital"),
        Patch(facecolor=MAIN_FILLS[1], edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, label="Fixed O&M"),
        Patch(facecolor=TAC_STACK_VOM_FILL, edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, label="Variable O&M"),
        Patch(facecolor=TAC_STACK_FUEL_FILL, edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, alpha=0.88, label="Fuel"),
        Patch(facecolor=TAC_STACK_C0_IMPORT_FILL, edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, label="Import"),
        Patch(facecolor=GRID_EXPORT_FILL, edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, alpha=GRID_EXPORT_ALPHA, label="Export"),
        Patch(facecolor="#7FB7A6", edgecolor=BLOCK_EDGE, linewidth=EDGE_LW, alpha=0.85, label="PTC"),
        Line2D([0], [0], color=MAIN_STROKES[3], lw=1.6, label="Net TAC"),
    ]


def _cc_data():
    s2 = df[df.group == "s2_price"].copy().sort_values(["case_id", "year"])
    s2["tac_m"] = s2.tac_usd_per_yr / 1e6
    s2["co2_kt"] = s2.co2_annual_tonnes / 1e3
    return s2


def _finish_local_axes(ax, grid_axis="y"):
    ax.set_axisbelow(True)
    ax.grid(axis=grid_axis, alpha=0.30, linestyle="--", linewidth=0.5)
    ax.tick_params(direction="out", length=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def panel_cc_scatter(ax):
    """Cell 9 axes[0]: cost-carbon plane (self-contained legends)."""
    s2 = _cc_data()
    years = [2022, 2023, 2024]
    cases = [0, 1, 2, 3]
    local_case_label = {0: "C0 grid", 1: "C1 SMR", 2: "C2 SMR + cool", 3: "C3 NGCC"}
    local_case_marker = {0: "o", 1: "s", 2: "P", 3: "^"}
    year_color = {2022: PALETTE["fill_blue"], 2023: PALETTE["fill_salmon"], 2024: PALETTE["fill_orange"]}
    for cid in cases:
        sub = s2[s2.case_id == cid].sort_values("year")
        ax.plot(sub.tac_m, sub.co2_kt, color="#B6B6B6", linewidth=THIN_LINE_PLOT_LW, alpha=0.68, zorder=1.5)
        for _, row in sub.iterrows():
            ax.scatter(row.tac_m, row.co2_kt, marker=local_case_marker[cid], s=LINE_MARKER_AREA,
                       facecolor=year_color[int(row.year)], edgecolor=BLOCK_EDGE,
                       linewidth=LINE_MARKER_EDGE_WIDTH, zorder=3)
    ax.set_xlabel(r"TAC (M\$ yr$^{-1}$)")
    ax.set_ylabel(r"Annual CO$_2$ (kt CO$_2$ yr$^{-1}$)")
    ax.set_xlim(20, 260)
    ax.set_ylim(-525, 520)
    _finish_local_axes(ax)
    case_handles = [Line2D([0], [0], marker=local_case_marker[cid], linestyle="none", color="none",
                           markerfacecolor="#777777", markeredgecolor=BLOCK_EDGE,
                           markeredgewidth=LINE_MARKER_EDGE_WIDTH, markersize=LINE_MARKER_SIZE,
                           label=local_case_label[cid]) for cid in cases]
    year_handles = [Line2D([0], [0], marker="o", linestyle="none", color="none",
                           markerfacecolor=year_color[y], markeredgecolor=BLOCK_EDGE,
                           markeredgewidth=LINE_MARKER_EDGE_WIDTH, markersize=LINE_MARKER_SIZE,
                           label=str(y)) for y in years]
    leg_case = ax.legend(handles=case_handles, loc="center", bbox_to_anchor=(0.52, 0.54),
                         ncol=2, frameon=True, facecolor="white", edgecolor="none", framealpha=0.88,
                         fontsize=TEXT_SIZE, handlelength=1.05, handletextpad=0.55, borderpad=0.32,
                         labelspacing=0.36, columnspacing=0.65, borderaxespad=0.0)
    ax.add_artist(leg_case)
    ax.legend(handles=year_handles, loc="upper right", bbox_to_anchor=(0.985, 0.985), ncol=1,
              frameon=True, facecolor="white", edgecolor="none", framealpha=0.88,
              fontsize=TEXT_SIZE, handlelength=0.8, handletextpad=0.35, borderpad=0.28,
              labelspacing=0.30, columnspacing=0.75, borderaxespad=0.0)
    ax.annotate("", xy=(0.135, 0.105), xytext=(0.235, 0.155), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=PALETTE["stroke_teal"], lw=0.9, alpha=0.72))
    ax.text(0.245, 0.165, "preferred", transform=ax.transAxes, fontsize=TEXT_SIZE,
            color=PALETTE["stroke_teal"], ha="left", va="center")


def panel_cc_accounting(ax):
    """Cell 9 axes[1]: nuclear CO2 accounting (self-contained legend, top of panel)."""
    s2 = _cc_data()
    years = [2022, 2023, 2024]
    local_case_short = {0: "C0", 1: "C1", 2: "C2", 3: "C3"}
    x_pos, x_labels, grid_import, reactor_lca, export_credit, net_co2 = [], [], [], [], [], []
    xpos = 0.0
    for year in years:
        for cid in (1, 2):
            row = s2[(s2.year == year) & (s2.case_id == cid)].iloc[0]
            x_pos.append(xpos)
            x_labels.append(f"{str(year)[-2:]}\n{local_case_short[cid]}")
            grid_import.append(row.co2_grid_import_tonnes / 1e3)
            reactor_lca.append(row.co2_rx_lifecycle_tonnes / 1e3)
            export_credit.append(-row.co2_export_credit_tonnes / 1e3)
            net_co2.append(row.co2_kt)
            xpos += 1.0
        xpos += 0.45
    x_pos = np.array(x_pos)
    grid_import = np.array(grid_import)
    reactor_lca = np.array(reactor_lca)
    export_credit = np.array(export_credit)
    net_co2 = np.array(net_co2)
    positive_total = grid_import + reactor_lca
    bars_grid = ax.bar(x_pos, grid_import, color=PALETTE["fill_blue"], edgecolor=BLOCK_EDGE,
                       linewidth=BLOCK_EDGE_LW, width=0.70)
    apply_vertical_bar_gradients(ax, bars_grid, PALETTE["fill_blue"])
    bars_lca = ax.bar(x_pos, reactor_lca, bottom=grid_import, color=PALETTE["fill_orange"],
                      edgecolor=BLOCK_EDGE, linewidth=BLOCK_EDGE_LW, width=0.70)
    apply_vertical_bar_gradients(ax, bars_lca, PALETTE["fill_orange"])
    bars_export = ax.bar(x_pos, export_credit, color=PALETTE["fill_salmon"], edgecolor=BLOCK_EDGE,
                         linewidth=BLOCK_EDGE_LW, width=0.70)
    apply_vertical_bar_gradients(ax, bars_export, PALETTE["fill_salmon"], white_at_zero=True, gamma=3.0)
    ax.scatter(x_pos, net_co2, marker="_", s=170, color="#222222", linewidth=1.0, zorder=5)
    for xi, top, net in zip(x_pos, positive_total, net_co2):
        annotate_vertical_value(ax, xi, top, f"+{top:.0f}", color="#111111")
        annotate_vertical_value(ax, xi, net, f"{net:.0f}", color="#111111", offset_pt=POINT_LABEL_OFFSET_PT)
    ax.axhline(0, **ZERO_LINE_KW)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel(r"Nuclear CO$_2$ accounting (kt CO$_2$ yr$^{-1}$)")
    ax.set_ylim(-835, 560)
    _finish_local_axes(ax)
    handles = [
        Patch(facecolor=PALETTE["fill_blue"], edgecolor=BLOCK_EDGE, label="Grid import"),
        Patch(facecolor=PALETTE["fill_orange"], edgecolor=BLOCK_EDGE, label="Reactor lifecycle"),
        Patch(facecolor=PALETTE["fill_salmon"], edgecolor=BLOCK_EDGE, label="Export credit"),
        Line2D([0], [0], color="#222222", linewidth=1.2, label="Net"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.965), ncol=2, frameon=True,
              facecolor="white", edgecolor="none", framealpha=0.88, fontsize=TEXT_SIZE,
              handlelength=0.9, columnspacing=0.8, handletextpad=0.4, borderpad=0.3,
              labelspacing=0.30, borderaxespad=0.0)


def panel_dispatch(ax, week):
    """Cell 10 logic for one week onto ax; returns the 5 legend specs."""
    disp = pd.read_csv(OUTPUTS / "main_baseline" / "case2" / "dispatch.csv.gz")
    starts = {"winter": 24 * 14, "summer": 24 * (31 + 28 + 31 + 30 + 31 + 30 + 14)}
    names = {"winter": "Winter (Jan 15 - Jan 22)", "summer": "Summer (Jul 15 - Jul 22)"}
    start = starts[week]
    sl = disp.iloc[start:start + 168].reset_index(drop=True)
    hours = np.arange(168)
    ax.fill_between(hours, 0, sl.P_turb_net_MW, color=PALETTE["fill_blue"], alpha=0.85,
                    edgecolor="white", linewidth=0.4)
    ax.plot(hours, sl.P_rx_MWth, color=FIGURE6_LINE_COLORS[0], linewidth=THIN_LINE_PLOT_LW)
    ax.set_xlim(0, 167)
    ax.set_xlabel("Hour of week")
    ax.set_ylabel(r"Power and heat (MW)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    ax_r = ax.twinx()
    ax_r.plot(hours, sl.Q_to_abs_MWth, color=FIGURE6_LINE_COLORS[1], linewidth=THIN_LINE_PLOT_LW, linestyle="--")
    ax_r.plot(hours, sl.Q_abs_cool_MWth, color=FIGURE6_LINE_COLORS[2], linewidth=THIN_LINE_PLOT_LW)
    ax_r.fill_between(hours, 0, sl.Q_VCC_cool_MWth, color=PALETTE["fill_salmon"], alpha=0.6,
                      edgecolor="white", linewidth=0.3)
    ax_r.set_ylabel(r"Cooling and extraction (MW)")
    ax_r.set_ylim(bottom=0)
    ax_r.spines["right"].set_visible(True)
    ax_r.text(0.02, 0.08, names[week], transform=ax.transAxes, fontsize=8,
              color="#222222", zorder=30, clip_on=False,
              bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=1.2))
    return [
        (r"$P_{\mathrm{tn}}$ (MW$_\mathrm{e}$)", "patch", PALETTE["fill_blue"], None),
        (r"$P_{\mathrm{rx}}$ (MW$_\mathrm{th}$)", "line", FIGURE6_LINE_COLORS[0], "-"),
        (r"$Q_{\mathrm{ext}}$ (MW$_\mathrm{th}$)", "line", FIGURE6_LINE_COLORS[1], "--"),
        (r"$Q_{\mathrm{a}}$ (MW$_\mathrm{c}$)", "line", FIGURE6_LINE_COLORS[2], "-"),
        (r"$Q_{\mathrm{v}}$ (MW$_\mathrm{c}$)", "patch", PALETTE["fill_salmon"], None),
    ]


def panel_value_decomp(ax):
    """Cell 11 waterfall onto ax."""
    vd = pd.read_csv(OUTPUTS / "figures" / "value_decomp_case2.csv")
    base_row = vd[vd.matching_key == "main_baseline/base"].iloc[0]
    components = [
        ("VCC\nsaved", base_row.vcc_elec_saved_usd_per_yr / 1e6),
        ("Power\nlost", base_row.turbine_gen_lost_usd_per_yr / 1e6),
        ("Absorber\ncapital", base_row.absorption_capex_fom_usd_per_yr / 1e6),
        ("VCC\nbackup", base_row.crystal_cutoff_backup_usd_per_yr / 1e6),
        ("PTC\nforgone", base_row.ptc_forgone_usd_per_yr / 1e6),
        ("Water\ncost", base_row.extra_water_cost_usd_per_yr / 1e6),
    ]
    net = base_row.net_value_of_absorption_usd_per_yr / 1e6
    residual = base_row.residual_usd_per_yr / 1e6
    components.append(("Residual", residual))
    bar_width = 0.58
    cum = 0.0
    x_pos, heights, bottoms, colors = [], [], [], []
    for name, val in components:
        x_pos.append(name)
        heights.append(val)
        bottoms.append(cum)
        colors.append(MAIN_FILLS[3] if name == "Residual" else (MAIN_FILLS[0] if val > 0 else MAIN_FILLS[1]))
        cum += val
    ax.bar(x_pos, heights, bottom=bottoms, color=colors, edgecolor=BLOCK_EDGE,
           linewidth=EDGE_LW, width=bar_width, alpha=0.88)
    x_pos.append("Net vs\nCase 1")
    heights.append(net)
    bottoms.append(0.0)
    net_color = MAIN_FILLS[0] if net > 0 else MAIN_FILLS[1]
    ax.bar(["Net vs\nCase 1"], [net], color=net_color, edgecolor=BLOCK_EDGE,
           linewidth=EDGE_LW, width=bar_width, alpha=0.88)
    for i in range(len(x_pos) - 1):
        level = bottoms[i] + heights[i]
        ax.plot([i + bar_width / 2, i + 1 - bar_width / 2], [level, level], color="#BDBDBD",
                linewidth=0.55, alpha=0.85, solid_capstyle="butt", zorder=2.2)
    small_label_offsets = {"VCC\nbackup": (-3, 3), "PTC\nforgone": (-3, 10), "Water\ncost": (3, 8)}
    vfs = 8.0
    for i, (x, h, b) in enumerate(zip(x_pos[:-1], heights[:-1], bottoms[:-1])):
        y = b + h
        if abs(h) >= 0.5:
            if x == "Residual":
                ax.text(i, b + h / 2, f"{h:+.1f}", ha="center", va="center", fontsize=vfs, color="#000000")
            else:
                fps = h >= 0
                if x == "Absorber\ncapital" and y > 0:
                    fps = True
                annotate_vertical_value(ax, i, y, f"{h:+.1f}", fontsize=vfs, force_positive_side=fps)
        else:
            dx, dy = small_label_offsets.get(x, (10, 10))
            ax.annotate(f"{h:+.2f}", xy=(i, y), xycoords="data", xytext=(dx, dy),
                        textcoords="offset points", ha="center", va="bottom", fontsize=vfs,
                        color="#000000", zorder=10,
                        arrowprops=dict(arrowstyle="-", color="#666666", linewidth=0.55, shrinkA=0, shrinkB=0))
    annotate_vertical_value(ax, len(x_pos) - 1, net, f"{net:+.1f}", fontsize=vfs, color="#000000")
    ax.axhline(0, **ZERO_LINE_KW)
    ax.set_ylabel(r"Δ vs Case 1 TAC (M\$ yr$^{-1}$)")
    ax.set_axisbelow(True)
    ax.grid(**GRID_KW)
    plt.setp(ax.get_xticklabels(), fontsize=8)
    ax.set_ylim(min(min(bottoms), -6.0), max(heights) + 1.2)


def _dispatch_legend(ax_leg, specs):
    handles = []
    for label, kind, color, ls in specs:
        if kind == "patch":
            handles.append(Patch(facecolor=color, edgecolor="white", label=label))
        else:
            handles.append(Line2D([0], [0], color=color, linestyle=ls or "-",
                                  linewidth=THIN_LINE_PLOT_LW, label=label))
    ax_leg.axis("off")
    ax_leg.legend(handles=handles, loc="upper center", ncol=5, frameon=True, facecolor="white",
                  edgecolor="none", framealpha=0.86, fontsize=8, columnspacing=1.2,
                  handlelength=1.5, borderpad=0.22, borderaxespad=0.0)


# =====================================================================
# Composite 1: Operation and absorption value (Nature Energy)
# =====================================================================
def build_operation_value(dirs):
    fig = plt.figure(figsize=(BODY_W, 7.05))
    gs = fig.add_gridspec(
        4, 1,
        height_ratios=[1.0, 1.0, 0.055, 1.18],
        left=0.11, right=0.96, top=0.985, bottom=0.080,
        hspace=COMPOSITE_HSPACE,
    )
    ax_w = fig.add_subplot(gs[0])
    ax_s = fig.add_subplot(gs[1])
    ax_leg = fig.add_subplot(gs[2])
    ax_v = fig.add_subplot(gs[3])
    specs = panel_dispatch(ax_w, "winter")
    panel_dispatch(ax_s, "summer")
    _dispatch_legend(ax_leg, specs)
    panel_value_decomp(ax_v)
    add_panel_label(ax_w, "a", x=-0.07, y=1.04)
    add_panel_label(ax_s, "b", x=-0.07, y=1.04)
    add_panel_label(ax_v, "c", x=-0.07, y=1.04)
    for d in dirs:
        save_triplet(fig, "fig_operation_value", str(d))
    plt.close(fig)


# =====================================================================
# Composite 2: Baseline economics (NATURE only)
# =====================================================================
def build_baseline_economics(dirs):
    fig = plt.figure(figsize=(BODY_W, 5.75))
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[1.0, 1.15],
        left=FIG2_LEFT, right=FIG2_RIGHT, top=0.965, bottom=0.095,
        hspace=FIG2_HSPACE, wspace=FIG2_WSPACE,
    )
    ax_tac = fig.add_subplot(gs[0, :])
    ax_sc = fig.add_subplot(gs[1, 0])
    ax_ac = fig.add_subplot(gs[1, 1])
    handles = panel_tac_stack(ax_tac)
    ax_tac.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.145),
                  ncol=8, frameon=False, fontsize=8,
                  columnspacing=0.6, handlelength=0.9, handletextpad=0.3, borderaxespad=0.0)
    panel_cc_scatter(ax_sc)
    panel_cc_accounting(ax_ac)
    add_panel_label(ax_tac, "a", x=-0.065, y=1.04)
    add_panel_label(ax_sc, "b", x=-0.14, y=1.045)
    add_panel_label(ax_ac, "c", x=-0.14, y=1.045)
    for d in dirs:
        save_triplet(fig, "fig_baseline_economics", str(d))
    plt.close(fig)


import traceback
try:
    build_operation_value([NAT_FIGS])
    build_baseline_economics([NAT_FIGS])
    print("OK: wrote fig_operation_value and fig_baseline_economics (Nature Energy)")
except Exception:
    traceback.print_exc()
    raise
