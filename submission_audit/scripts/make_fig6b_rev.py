"""Task B3 — redraw manuscript Figure 6 with a dual-scale panel (b).

Panel (a) reproduces the PUBLISHED figure's semantics (solid lines inside
the solved $0-100/tCO2 range, dashed extrapolation beyond, "solved range"
rule, short crossover labels, unit-style axis labels) — the checked-in
notebook cell 15 predates the shipped figure, so the shipped PNG is the
style reference here.

Panel (b) keeps the published ranked margin-span (pp) bars and axis order,
and pairs every axis with a light mint-teal |dTAC| bar read on a secondary
top axis (M$/yr), so the pp ranking and the absolute-dollar ranking are
visible side by side.  The data-center-size bar is hatched and
dagger-flagged: that axis rescales the system itself, so its absolute span
is not comparable with the fixed-system axes.

Outputs go to submission_audit/figures/ (fig_policy_sensitivity_summary_rev)
and submission_audit/audit/B3_results.json; the manuscript's own figures/
folder is not touched.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

SCI_FIGURE_SCRIPTS = "/home/honglin/.claude/skills/sci-figure/scripts"
if SCI_FIGURE_SCRIPTS not in sys.path:
    sys.path.insert(0, SCI_FIGURE_SCRIPTS)
from sci_figure_helpers import (  # noqa: E402
    PALETTE,
    add_panel_label,
    apply_sci_style,
    save_pdf,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = PROJECT_ROOT / "outputs"
FIGURES = PROJECT_ROOT / "submission_audit" / "figures"
AUDIT = PROJECT_ROOT / "submission_audit" / "audit"
FIGURES.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)

# ---- shared style, identical to make_figures.ipynb cell 3 ------------------
MANUSCRIPT_RC = {
    "font.size": 8.0,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
    "legend.fontsize": 8.0,
}
apply_sci_style("ae_single")
plt.rcParams.update(MANUSCRIPT_RC)

BODY_W = 7.0
MAIN_FILLS = [
    PALETTE["fill_blue"],
    PALETTE["fill_salmon"],
    PALETTE["fill_orange"],
    PALETTE["fill_gray"],
]
MAIN_STROKES = [
    PALETTE["stroke_navy"],
    PALETTE["stroke_clay"],
    PALETTE["stroke_teal"],
    "#555555",
]
BLOCK_EDGE = "#FFFFFF"
TEXT_SIZE = MANUSCRIPT_RC["font.size"]
GRID_KW = dict(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
LINE_PLOT_LW = 1.85
LINE_MARKER_AREA = 6.2 ** 2
LINE_MARKER_EDGE_WIDTH = 1.0
POINT_LABEL_OFFSET_PT = 5
FIGURE2_LINE_COLORS = [MAIN_FILLS[1], MAIN_FILLS[0], MAIN_FILLS[3], MAIN_FILLS[2]]
CASE_MARKER = {0: "o", 1: "s", 2: "D", 3: "^"}
BAR_GRADIENT_STEPS = 256
MONEY_FILL = "#86DED4"          # low-sat mint teal — money-scale fill
MONEY_STROKE = PALETTE["stroke_teal"]


def _bar_gradient_cmap(color: str, steps: int = BAR_GRADIENT_STEPS):
    return LinearSegmentedColormap.from_list(
        "white_to_bar_color", ["#FFFFFF", color], N=steps
    )


def draw_horizontal_gradient_bar(ax, y, x_start, x_end, height, color, *,
                                 white_at="left", steps=BAR_GRADIENT_STEPS,
                                 gamma=1.0):
    if x_end <= x_start:
        return
    ramp = np.linspace(0.0, 1.0, steps) ** gamma
    if white_at == "right":
        ramp = ramp[::-1]
    gradient = np.tile(ramp[None, :], (2, 1))
    ax.imshow(
        gradient,
        extent=(x_start, x_end, y - height / 2, y + height / 2),
        origin="lower",
        aspect="auto",
        cmap=_bar_gradient_cmap(color, steps),
        interpolation="nearest",
        resample=False,
        zorder=2,
    )


def annotate_horizontal_endpoint(ax, x, y, label, *, side, fontsize=TEXT_SIZE,
                                 offset_pt=POINT_LABEL_OFFSET_PT,
                                 color="#000000", zorder=10):
    dx = -offset_pt if side == "left" else offset_pt
    ha = "right" if side == "left" else "left"
    ax.annotate(label, xy=(x, y), xycoords="data", xytext=(dx, 0),
                textcoords="offset points", ha=ha, va="center",
                fontsize=fontsize, color=color, zorder=zorder,
                annotation_clip=False)


df = pd.read_csv(OUTPUTS / "master_kpi_table.csv")


def run_row(run_id: str) -> pd.Series:
    m = df[df.run_id == run_id]
    assert len(m) == 1, run_id
    return m.iloc[0]


def hrp_percent(run_id: str) -> float:
    return float(run_row(run_id)["heat_recovery_premium"] * 100.0)


def tac_musd(run_id: str) -> float:
    return float(run_row(run_id)["tac_usd_per_yr"] / 1e6)


# ---------------------------------------------------------------------------
# Axis table: (published label, endpoint runs) as in the shipped figure
# ---------------------------------------------------------------------------
AXES_DEF = [
    ("Reactor capital", "case2_FOAK", "case2_NOAK", False),
    ("Market year", "case2_year2024", "case2_year2022", False),
    ("WACC", "case2_wacc_100", "case2_wacc_50", False),
    ("Carbon price", "case2_co2_0", "case2_co2_100", False),
    ("Data-center size", "case2_load_x050", "case2_load_x300", True),
    ("Absorber capital", "case2_smr_ATB_Mid_abs_Turnkey_High",
     "case2_smr_ATB_Mid_abs_Bare_Low", False),
    ("PUE", "case2_pue150", "case2_pue110", False),
    ("BESS on/off", "case2_bess_off", "case2_bess_on", False),
]

axis_rows = []
for label, run_a, run_b, size_flag in AXES_DEF:
    va, vb = hrp_percent(run_a), hrp_percent(run_b)
    ta, tb = tac_musd(run_a), tac_musd(run_b)
    lo, hi = min(va, vb), max(va, vb)
    axis_rows.append(
        {
            "axis": label,
            "run_low_margin": run_a if va <= vb else run_b,
            "run_high_margin": run_b if va <= vb else run_a,
            "margin_low_pct": lo,
            "margin_high_pct": hi,
            "margin_span_pp": hi - lo,
            "case2_tac_low_musd_yr": min(ta, tb),
            "case2_tac_high_musd_yr": max(ta, tb),
            "delta_tac_musd_yr": abs(ta - tb),
            "system_rescaling_axis": size_flag,
        }
    )
axis_rows.sort(key=lambda r: r["margin_span_pp"], reverse=True)

SOLVED_MAX = 100.0


def figure_policy_sensitivity_summary_rev() -> None:
    fig = plt.figure(figsize=(BODY_W, 6.35))
    gs = fig.add_gridspec(
        2, 1,
        height_ratios=[1.02, 1.40],
        left=0.15, right=0.98, top=0.955, bottom=0.075,
        hspace=0.30,
    )
    ax_c = fig.add_subplot(gs[0, 0])
    ax_t = fig.add_subplot(gs[1, 0])

    # ---- a) Carbon-price crossover: solid inside solved range, dashed out --
    s6 = df[df.group == "s6_carbon_price"].copy().sort_values(
        ["case_id", "carbon_price_usd_per_tco2"]
    )
    crossings: dict[int, float] = {}
    fits: dict[int, tuple[float, float]] = {}
    panel_a_line_colors = FIGURE2_LINE_COLORS.copy()
    panel_a_line_colors[1] = PALETTE["accent_sky"]
    case0_at_x = None
    for cid in (0, 1, 2, 3):
        sub = s6[s6.case_id == cid]
        x = sub.carbon_price_usd_per_tco2.values
        y = sub.tac_usd_per_yr.values / 1e6
        slope = (y[-1] - y[0]) / (x[-1] - x[0])
        intercept = y[0]
        fits[cid] = (intercept, slope)
        line_color = panel_a_line_colors[cid]
        x_solid = np.linspace(0.0, SOLVED_MAX, 64)
        x_dash = np.linspace(SOLVED_MAX, 250.0, 96)
        ax_c.plot(x_solid, intercept + slope * x_solid, color=line_color,
                  linewidth=LINE_PLOT_LW, zorder=2)
        ax_c.plot(x_dash, intercept + slope * x_dash, color=line_color,
                  linewidth=LINE_PLOT_LW, linestyle=(0, (4.2, 2.6)), zorder=2)
        ax_c.scatter(x, y, marker=CASE_MARKER[cid], s=LINE_MARKER_AREA,
                     facecolor=MAIN_FILLS[3], edgecolor=BLOCK_EDGE,
                     linewidth=LINE_MARKER_EDGE_WIDTH, zorder=4)
        if cid == 0:
            case0_at_x = (intercept, slope)
        else:
            c0_int, c0_slope = case0_at_x
            denom = slope - c0_slope
            if abs(denom) > 1e-9:
                cross_price = (c0_int - intercept) / denom
                if 0 < cross_price < 260:
                    crossings[cid] = cross_price

    nuclear_cross = np.mean([crossings[c] for c in (1, 2) if c in crossings])
    ngcc_cross = crossings.get(3, 250)
    ax_c.axvspan(nuclear_cross, ngcc_cross, color=PALETTE["fill_blue"],
                 alpha=0.16, lw=0)
    ax_c.axvspan(ngcc_cross, 250, color=PALETTE["fill_salmon"], alpha=0.13, lw=0)
    # Solved-range boundary rule.
    ax_c.axvline(SOLVED_MAX, color="#999999", lw=1.0, zorder=3)
    ax_c.text(SOLVED_MAX - 3, 232, "solved range", rotation=90, ha="right",
              va="top", fontsize=TEXT_SIZE, color="#888888")
    ax_c.axvline(nuclear_cross, color=PALETTE["stroke_navy"], ls=":", lw=1.0)
    ax_c.text(nuclear_cross - 4, 232, f"Nuclear\n~{nuclear_cross:.0f}",
              fontsize=TEXT_SIZE, ha="right", va="top",
              color=PALETTE["stroke_navy"], linespacing=0.95)
    if 3 in crossings:
        ax_c.axvline(crossings[3], color="#555555", ls=":", lw=0.9)
        ax_c.text(crossings[3] + 4, 232, f"NGCC\n~{crossings[3]:.0f}",
                  fontsize=TEXT_SIZE, ha="left", va="top", color="#555555",
                  linespacing=0.95)
    ax_c.text((nuclear_cross + ngcc_cross) / 2, 198, "Nuclear\nless than\ngrid",
              fontsize=TEXT_SIZE, ha="center", va="center",
              color=PALETTE["stroke_navy"], linespacing=1.18)
    ax_c.text((ngcc_cross + 250) / 2, 198, "Nuclear\nless than\ngrid and NGCC",
              fontsize=TEXT_SIZE, ha="center", va="center",
              color=PALETTE["stroke_clay"], linespacing=1.20)

    # Direct line labels: ascending pair at the right edge, descending pair
    # placed above their dashed tails inside the axes.
    for cid, text, dy in ((3, "C3 NGCC", 8.0), (0, "C0 grid", -7.5)):
        intercept, slope = fits[cid]
        ax_c.text(253.5, intercept + slope * 250 + dy, text, ha="left",
                  va="center", fontsize=TEXT_SIZE,
                  color=panel_a_line_colors[cid])
    i2, s2 = fits[2]
    ax_c.text(233.0, i2 + s2 * 233.0 + 17.0, "C2 absorption", ha="center",
              va="center", fontsize=TEXT_SIZE, color=panel_a_line_colors[2])
    i1, s1 = fits[1]
    ax_c.text(205.0, i1 + s1 * 205.0 - 14.0, "C1 nuclear", ha="center",
              va="center", fontsize=TEXT_SIZE, color=panel_a_line_colors[1])

    ax_c.set_xlabel(r"Carbon price (\$ tCO$_2^{-1}$)")
    ax_c.set_ylabel(r"TAC (M\$ yr$^{-1}$)")
    ax_c.set_xlim(0, 272)
    ax_c.set_ylim(22, 237)
    ax_c.set_axisbelow(True)
    ax_c.grid(**GRID_KW)
    add_panel_label(ax_c, "a", x=-0.12, y=1.05)

    # ---- b) Ranked tornado, dual scale ------------------------------------
    baseline = hrp_percent("case2_ATB_Mid")
    labels = [r["axis"] for r in axis_rows]
    lows = [r["margin_low_pct"] for r in axis_rows]
    highs = [r["margin_high_pct"] for r in axis_rows]
    spans = [r["margin_span_pp"] for r in axis_rows]
    dtacs = [r["delta_tac_musd_yr"] for r in axis_rows]
    size_flags = [r["system_rescaling_axis"] for r in axis_rows]
    ypos = np.arange(len(axis_rows))[::-1]

    segment_lengths = []
    for lo, hi in zip(lows, highs):
        if min(lo, baseline) < baseline:
            segment_lengths.append(baseline - min(lo, baseline))
        if max(hi, baseline) > baseline:
            segment_lengths.append(max(hi, baseline) - baseline)
    max_segment_length = max(segment_lengths) if segment_lengths else 0.0

    def gamma_from_length(length: float, max_gamma: float = 3.5) -> float:
        if max_segment_length <= 0:
            return 1.0
        return 1.0 + (max_gamma - 1.0) * (length / max_segment_length)

    worse_color = MAIN_FILLS[0]
    better_color = MAIN_FILLS[1]
    PP_DY, PP_H = +0.135, 0.46           # margin-span bar geometry
    DT_DY, DT_H = -0.245, 0.20           # dollar-span bar geometry

    for y, lo, hi in zip(ypos, lows, highs):
        left, right = min(lo, baseline), max(hi, baseline)
        if left < baseline:
            draw_horizontal_gradient_bar(
                ax_t, y + PP_DY, left, baseline, PP_H, worse_color,
                white_at="right", gamma=gamma_from_length(baseline - left),
            )
        if right > baseline:
            draw_horizontal_gradient_bar(
                ax_t, y + PP_DY, baseline, right, PP_H, better_color,
                white_at="left", gamma=gamma_from_length(right - baseline),
            )
        annotate_horizontal_endpoint(ax_t, lo, y + PP_DY, f"{lo:.0f}",
                                     side="left", color=MAIN_STROKES[0])
        annotate_horizontal_endpoint(ax_t, hi, y + PP_DY, f"{hi:.0f}",
                                     side="right", color=MAIN_STROKES[1])

    ax_t.axvline(baseline, color="#333333", lw=1.0, ls="--", zorder=8)
    ax_t.annotate(
        f"ATB-Mid baseline ({baseline:.0f})",
        xy=(baseline, -0.55), xytext=(-POINT_LABEL_OFFSET_PT, 0),
        textcoords="offset points",
        ha="right", va="center", fontsize=8, color="#333333", zorder=9,
    )
    ax_t.set_yticks(ypos)
    ax_t.set_yticklabels(
        [f"{label}\n(span {span:.0f} pp)" for label, span in zip(labels, spans)]
    )
    ax_t.set_xlabel("Case 2 grid-cost margin (%)")
    x_lo, x_hi = min(lows) - 90, max(highs) + 40
    ax_t.set_xlim(x_lo, x_hi)
    ax_t.set_ylim(-1.05, len(axis_rows) - 0.4)
    ax_t.set_axisbelow(True)
    ax_t.grid(axis="x", alpha=0.25, linestyle="--", linewidth=0.5)
    ax_t.tick_params(direction="out", length=3)
    for spine in ("top", "right"):
        ax_t.spines[spine].set_visible(False)

    # Secondary top scale: |dTAC| across each axis, M$/yr, bars from 0.
    ax_m = ax_t.twiny()
    dt_max = max(dtacs)
    ax_m.set_xlim(0, dt_max * 1.30)
    ax_m.set_ylim(ax_t.get_ylim())
    for y, dt, flagged in zip(ypos, dtacs, size_flags):
        ax_m.barh(
            y + DT_DY, dt, height=DT_H, left=0.0,
            facecolor=MONEY_FILL, edgecolor=BLOCK_EDGE, linewidth=0.5,
            hatch="///" if flagged else None, zorder=3,
        )
        tag = rf"\${dt:,.1f}M" if dt < 10 else rf"\${dt:,.0f}M"
        if flagged:
            tag += r"$^{\dagger}$"
        ax_m.annotate(tag, xy=(dt, y + DT_DY), xytext=(POINT_LABEL_OFFSET_PT, 0),
                      textcoords="offset points", ha="left", va="center",
                      fontsize=7.0, color=MONEY_STROKE, zorder=10)
    ax_m.set_xlabel(
        r"Case 2 TAC span across axis, $|\Delta \mathrm{TAC}|$ (M\$ yr$^{-1}$)",
        color=MONEY_STROKE,
    )
    ax_m.tick_params(axis="x", colors=MONEY_STROKE, direction="out", length=3)
    ax_m.spines["top"].set_visible(True)
    ax_m.spines["top"].set_color(MONEY_STROKE)
    for spine in ("bottom", "left", "right"):
        ax_m.spines[spine].set_visible(False)
    ax_m.set_axisbelow(True)

    # Dagger note inside the empty bottom-left strip of the panel.
    ax_t.text(
        x_lo + 8.0, -0.90,
        r"$^{\dagger}$Data-center-size axis rescales the whole system "
        r"(0.5--3.0$\times$ IT load); its absolute TAC span is not comparable "
        r"with the fixed-system axes.",
        ha="left", va="center", fontsize=6.8, color="#555555", zorder=9,
    )

    handles = [
        Patch(facecolor=worse_color, edgecolor="white",
              label="more negative than baseline"),
        Patch(facecolor=better_color, edgecolor="white",
              label="less negative than baseline"),
        Patch(facecolor=MONEY_FILL, edgecolor="white",
              label=r"$|\Delta \mathrm{TAC}|$ span (top axis)"),
    ]
    ax_t.legend(handles=handles, loc="lower right", frameon=False,
                fontsize=7.2, bbox_to_anchor=(1.0, 0.10))
    add_panel_label(ax_t, "b", x=-0.12, y=1.10)

    save_pdf(fig, "fig_policy_sensitivity_summary_rev", str(FIGURES))
    plt.close(fig)


figure_policy_sensitivity_summary_rev()

b3 = {
    "axes": [
        {
            "axis": r["axis"],
            "case2_tac_low_musd_yr": r["case2_tac_low_musd_yr"],
            "case2_tac_high_musd_yr": r["case2_tac_high_musd_yr"],
            "delta_tac_musd_yr": r["delta_tac_musd_yr"],
            "margin_span_pp": r["margin_span_pp"],
            "margin_low_pct": r["margin_low_pct"],
            "margin_high_pct": r["margin_high_pct"],
            "endpoint_runs": [r["run_low_margin"], r["run_high_margin"]],
        }
        for r in axis_rows
    ],
    "figure_path": "submission_audit/figures/fig_policy_sensitivity_summary_rev.pdf",
    "size_axis_caveat": (
        "The data-center-size axis scales the IT load, cooling and comparator "
        "capacities together (0.5-3.0x), so both the numerator and the "
        "matched Case-0 denominator grow with it; its absolute TAC span "
        "(212.8 M$/yr) measures system size, not boundary sensitivity, and "
        "is hatch/dagger-flagged in the redrawn panel rather than ranked "
        "against the fixed-system axes."
    ),
    "panel_a_note": (
        "Panel (a) follows the shipped figure (solid lines inside the solved "
        "$0-100/tCO2 range, dashed extrapolation beyond, solved-range rule); "
        "the checked-in make_figures.ipynb cell 15 predates that revision."
    ),
    "source_table": "outputs/master_kpi_table.csv (archived, unchanged values)",
}
with (AUDIT / "B3_results.json").open("w") as f:
    json.dump(b3, f, indent=2)
print("B3_results.json written;",
      {r["axis"]: round(r["delta_tac_musd_yr"], 1) for r in axis_rows})
