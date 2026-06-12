#!/usr/bin/env python3
"""Regenerate Nature Energy manuscript figures with journal-style unit labels.

This script executes the existing paper_figures.ipynb plotting cells that feed
the Nature Energy main text and Supplementary Information, but normalizes all
axis labels and in-figure annotations that use slash/per-unit notation into
negative-exponent notation. It also forces Arial/Arial mathtext for consistency.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NB = PROJECT_ROOT / "notebooks" / "paper_figures.ipynb"
OUT_FIGS = PROJECT_ROOT / "outputs" / "figures"
NATURE_FIGS = PROJECT_ROOT / "MANUSCRIPT" / "Nature Energy" / "figures"

FIGURE_CELLS = {
    6: "fig_inputs_overview",
    8: "fig12_s8_size_matching",
    12: "fig_sensitivity_cooling_response",
    13: "fig_sensitivity_boundary_atlas",
    15: "fig_policy_sensitivity_summary",
}

ARIAL_RC = {
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


def normalize_units(source: str) -> str:
    """Convert figure text from slash/per units to negative-exponent units."""
    replacements = {
        r"M\\$/yr": r"M\\$ yr$^{-1}$",
        r"M\$/yr": r"M\$ yr$^{-1}$",
        r"M$/yr": r"M\\$ yr$^{-1}$",
        r"TWh/yr": r"TWh yr$^{-1}$",
        r"kt CO$_2$/yr": r"kt CO$_2$ yr$^{-1}$",
        r"kt/yr": r"kt yr$^{-1}$",
        r"\$/MWh$_\mathrm{e}$": r"\$ MWh$_\mathrm{e}^{-1}$",
        r"\$/MWh$_\mathrm{IT}$": r"\$ MWh$_\mathrm{IT}^{-1}$",
        r"\$/kW$_\mathrm{e}$": r"\$ kW$_\mathrm{e}^{-1}$",
        r"\$/kW$_\mathrm{c}$": r"\$ kW$_\mathrm{c}^{-1}$",
        r"\$/tCO$_2$": r"\$ tCO$_2^{-1}$",
        r"/tCO$_2$": r" tCO$_2^{-1}$",
        'f"{gap_25_myr:.0f} M\\\\$/yr\\ngap at 2.5x"': 'f"{gap_25_myr:.0f}\\ngap at 2.5x"',
        'f"{gap_25_myr:.0f} M\\\\$ yr$^{-1}$\\ngap at 2.5x"': 'f"{gap_25_myr:.0f}\\ngap at 2.5x"',
        r"USD per MWh IT gap": r"cost gap",
        r"LiBr gate: $T_{wb}\geq29\,^\circ$C": r"LiBr gate: $T_{\mathrm{wb}}$ >= 29 °C",
        r"Design: $T_{wb}=26\,^\circ$C": r"Design: $T_{\mathrm{wb}}$ = 26 °C",
        r"Wet-bulb $T_{wb}$ ($^\circ$C)": r"Wet-bulb $T_{\mathrm{wb}}$ (°C)",
        r"design anchor\n(26 $^\\circ$C, COP 1.10)": r"design anchor\n(26 °C, COP 1.10)",
        r"Absorption COP$_a$": r"Absorption COP$_{\mathrm{a}}$",
        r"SMR OCC": r"Reactor capital",
        r"SMR CAPEX": r"Reactor capital",
        r"Absorption CAPEX": r"Absorber capital",
        r"DC size": r"Data-center size",
        r"Reactor LCA": r"Reactor lifecycle",
        'f"{data[i, j]:+.0f}%"': 'f"{data[i, j]:+.0f}"',
        'f"{v:+.0f}%"': 'f"{v:+.0f}"',
        'f"{lo:.0f}%"': 'f"{lo:.0f}"',
        'f"{hi:.0f}%"': 'f"{hi:.0f}"',
        'f"ATB-Mid baseline ({baseline:.0f}%)"': 'f"ATB-Mid baseline ({baseline:.0f})"',
        'f"Nuclear\\n~\\\\${nuclear_cross:.0f}/tCO$_2$"': 'f"Nuclear\\n~{nuclear_cross:.0f}"',
        'f"Nuclear\\n~\\\\${nuclear_cross:.0f} tCO$_2^{-1}$"': 'f"Nuclear\\n~{nuclear_cross:.0f}"',
        'f"NGCC\\n~\\\\${crossings[3]:.0f}/tCO$_2$"': 'f"NGCC\\n~{crossings[3]:.0f}"',
        'f"NGCC\\n~\\\\${crossings[3]:.0f} tCO$_2^{-1}$"': 'f"NGCC\\n~{crossings[3]:.0f}"',
        '"Nuclear\\nless than\\nGrid and NGCC"': '"Nuclear\\nless than\\ngrid and NGCC"',
        "Grid and NGCC": "grid and NGCC",
        "fig, axes = plt.subplots(2, 2, figsize=(BODY_W, 5.0))": (
            "fig, axes = plt.subplots(2, 2, figsize=(BODY_W, 4.75))"
        ),
        "fig.tight_layout(h_pad=1.7, w_pad=1.2)": (
            "fig.tight_layout(h_pad=0.85, w_pad=0.85)"
        ),
        "fig.tight_layout(w_pad=1.35, h_pad=1.05)": (
            "fig.tight_layout(w_pad=0.95, h_pad=0.90)"
        ),
        (
            "    ax.text(94.7, -438, \"1x load\", ha=\"center\", va=\"bottom\",\n"
            "            fontsize=8, color=\"#333333\", rotation=90)"
        ): (
            "    ax.text(106.0, -360, \"1x load\", ha=\"center\", va=\"center\",\n"
            "            fontsize=8, color=\"#333333\", rotation=90,\n"
            "            bbox=dict(facecolor=\"white\", edgecolor=\"none\", alpha=0.78, pad=0.6))"
        ),
        (
            "    ax.annotate(\n"
            "        f\"{gap_25_myr:.0f}\\ngap at 2.5x\",\n"
            "        xy=(c2.loc[c2.load_multiplier == 2.5, \"avg_it_mw\"].iloc[0],\n"
            "            c2.loc[c2.load_multiplier == 2.5, \"tac_myr\"].iloc[0]),\n"
            "        xytext=(-22, -34),"
        ): (
            "    gap_row_25 = c2.loc[c2.load_multiplier == 2.5].iloc[0]\n"
            "    gap_x = gap_row_25[\"avg_it_mw\"]\n"
            "    gap_grid = gap_row_25[\"grid_myr\"]\n"
            "    gap_tac = gap_row_25[\"tac_myr\"]\n"
            "    gap_arrow_x = gap_x + 12.0\n"
            "    gap_arrow_grid = float(np.interp(gap_arrow_x, c2.avg_it_mw, c2.grid_myr))\n"
            "    gap_arrow_tac = float(np.interp(gap_arrow_x, c2.avg_it_mw, c2.tac_myr))\n"
            "    ax.annotate(\n"
            "        \"\",\n"
            "        xy=(gap_arrow_x, gap_arrow_grid),\n"
            "        xytext=(gap_arrow_x, gap_arrow_tac),"
        ),
        (
            "        ha=\"right\",\n"
            "        va=\"top\",\n"
            "        arrowprops=dict(arrowstyle=\"->\", color=\"#555555\", lw=0.7),\n"
            "    )\n"
            "    ax.set_ylabel(\"Annual TAC (M\\$ yr$^{-1}$)\")"
        ): (
            "        textcoords=\"data\",\n"
            "        arrowprops=dict(arrowstyle=\"<->\", color=\"#555555\", lw=0.75,\n"
            "                        shrinkA=0, shrinkB=0),\n"
            "        zorder=28,\n"
            "        annotation_clip=False,\n"
            "    )\n"
            "    ax.text(\n"
            "        gap_x - 58.0,\n"
            "        gap_tac + 22.0,\n"
            "        f\"Gap at 2.5x\\n{gap_25_myr:.0f} M\\$ yr$^{{-1}}$\",\n"
            "        ha=\"left\",\n"
            "        va=\"center\",\n"
            "        fontsize=TEXT_SIZE,\n"
            "        color=\"#333333\",\n"
            "        zorder=30,\n"
            "        clip_on=False,\n"
            "    )\n"
            "    ax.set_ylabel(\"Annual TAC (M\\$ yr$^{-1}$)\")"
        ),
        (
            "    ax.annotate(\n"
            "        \"\",\n"
            "        xy=(gap_arrow_x, gap_arrow_grid),\n"
            "        xytext=(gap_arrow_x, gap_arrow_tac),\n"
            "        textcoords=\"offset points\",\n"
            "        fontsize=TEXT_SIZE,\n"
            "        color=\"#333333\",\n"
            "        ha=\"right\",\n"
            "        va=\"top\",\n"
            "        arrowprops=dict(arrowstyle=\"->\", color=\"#555555\", lw=0.7),\n"
            "    )"
        ): (
            "    ax.annotate(\n"
            "        \"\",\n"
            "        xy=(gap_arrow_x, gap_arrow_grid),\n"
            "        xytext=(gap_arrow_x, gap_arrow_tac),\n"
            "        textcoords=\"data\",\n"
            "        arrowprops=dict(arrowstyle=\"<->\", color=\"#555555\", lw=0.75,\n"
            "                        shrinkA=0, shrinkB=0),\n"
            "        zorder=28,\n"
            "        annotation_clip=False,\n"
            "    )\n"
            "    ax.text(\n"
            "        gap_x - 58.0,\n"
            "        gap_tac + 22.0,\n"
            "        f\"Gap at 2.5x\\n{gap_25_myr:.0f} M\\$ yr$^{{-1}}$\",\n"
            "        ha=\"left\",\n"
            "        va=\"center\",\n"
            "        fontsize=TEXT_SIZE,\n"
            "        color=\"#333333\",\n"
            "        zorder=30,\n"
            "        clip_on=False,\n"
            "    )"
        ),
        (
            "    apply_vertical_bar_gradients(ax_a, bars, tac_colors, white_at_zero=True)\n"
            "    ax_a.axhline(0, **ZERO_LINE_KW)\n"
            "    for b, v in zip(bars, tac_gap):"
        ): (
            "    apply_vertical_bar_gradients(ax_a, bars, tac_colors, white_at_zero=True)\n"
            "    for b, v in zip(bars, tac_gap):"
        ),
        "    ax_b.set_ylim(0, max(cooling_elec_saving) * 1.28)": (
            "    ax_b.set_ylim(-1.5, max(cooling_elec_saving) * 1.28)"
        ),
        "    ax.set_ylim(55, 440)": (
            "    ax.set_ylim(70, 220)"
        ),
        (
            "    for b, v in zip(bars, cooling_elec_saving):\n"
            "        annotate_vertical_value(ax_b, b.get_x() + b.get_width() / 2, v, f\"{v:.1f}\", fontsize=8)"
        ): (
            "    for b, v in zip(bars, cooling_elec_saving):\n"
            "        label_v = 0.0 if abs(v) < 0.05 else v\n"
            "        annotate_vertical_value(\n"
            "            ax_b, b.get_x() + b.get_width() / 2, label_v, f\"{label_v:.1f}\",\n"
            "            fontsize=8, force_positive_side=label_v >= 0,\n"
            "        )"
        ),
        "    ax_b.set_ylim(-530, 25)": (
            "    ax_b.set_ylim(-320, 112)"
        ),
        "    ax_a.set_ylim(-735, 45)": (
            "    ax_a.set_ylim(-500, 65)"
        ),
        "    ax_c.set_ylim(-335, 20)": (
            "    ax_c.set_ylim(-200, 25)"
        ),
        "    cb.set_ticks([_vmin, -300.0, -200.0, -100.0, 0.0, 10.0, 20.0, _vmax])": (
            "    cb.set_ticks([_vmin, -200.0, -100.0, 0.0, 30.0, 60.0, _vmax])"
        ),
        "    cb.set_ticklabels([f\"{int(_vmin):d}\", \"-300\", \"-200\", \"-100\", \"0\", \"+10\", \"+20\", f\"+{int(_vmax):d}\"])": (
            "    cb.set_ticklabels([f\"{int(_vmin):d}\", \"-200\", \"-100\", \"0\", \"+30\", \"+60\", f\"+{int(_vmax):d}\"])"
        ),
        'add_panel_label(ax_d_frame, "d", x=-0.075, y=1.03)': (
            'add_panel_label(ax_d_frame, "d", x=0.005, y=1.045)'
        ),
        "    label_offsets = {0: -7.5, 1: 9.0, 2: -9.5, 3: 8.0}": (
            "    label_offsets = {0: -7.5, 1: 19.0, 2: 8.0, 3: 8.0}"
        ),
        (
            "    ax_c.text((nuclear_cross + ngcc_cross) / 2 - 4, 76, \"Nuclear\\nless than\\ngrid\","
        ): (
            "    ax_c.text((nuclear_cross + ngcc_cross) / 2 + 14, 198, \"Nuclear\\nless than\\ngrid\","
        ),
        (
            "    ax_c.text((ngcc_cross + 250) / 2 + 4, 70, \"Nuclear\\nless than\\ngrid and NGCC\","
        ): (
            "    ax_c.text((ngcc_cross + 250) / 2 + 4, 198, \"Nuclear\\nless than\\ngrid and NGCC\","
        ),
        (
            "        ax_c.text(253.5, y_end + label_offsets[cid], text,\n"
            "                  ha=\"left\", va=\"center\", fontsize=TEXT_SIZE, color=direct_label_colors[cid])"
        ): (
            "        label_x = {1: 185.0, 2: 225.0}.get(cid, 253.5)\n"
            "        label_y = {1: 35.0, 2: 56.0}.get(cid, y_end + label_offsets[cid])\n"
            "        ax_c.text(label_x, label_y, text,\n"
            "                  ha=\"left\", va=\"center\", fontsize=TEXT_SIZE, color=direct_label_colors[cid])"
        ),
        "    ax_c.set_ylim(40, 235)": (
            "    ax_c.set_ylim(25, 235)"
        ),
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    return source


def main() -> None:
    nb = json.loads(NB.read_text())
    env: dict[str, object] = {}

    setup3 = "".join(nb["cells"][3]["source"])
    assert "Shared setup for all figure cells" in setup3, (
        "paper_figures.ipynb was restructured; positional cell indices are stale"
    )
    for idx in (2, 3, 4):
        src = "".join(nb["cells"][idx]["source"])
        exec(compile(src, f"paper_figures.ipynb:cell{idx}", "exec"), env)

    plt = env["plt"]
    plt.rcParams.update(ARIAL_RC)
    original_style = env["apply_manuscript_style"]

    def apply_manuscript_style_arial(width: str = "ae_single") -> None:
        original_style(width)
        plt.rcParams.update(ARIAL_RC)

    env["apply_manuscript_style"] = apply_manuscript_style_arial
    env["FIGURES"] = OUT_FIGS

    for idx, name in FIGURE_CELLS.items():
        src = normalize_units("".join(nb["cells"][idx]["source"]))
        assert f'"{name}"' in src, (
            f"cell {idx} does not produce {name}; notebook cells moved"
        )
        exec(compile(src, f"paper_figures.ipynb:cell{idx}", "exec"), env)
        for ext in ("pdf", "svg", "png"):
            src_path = OUT_FIGS / f"{name}.{ext}"
            if src_path.exists():
                shutil.copy2(src_path, NATURE_FIGS / src_path.name)
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
