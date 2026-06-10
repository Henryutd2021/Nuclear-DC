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


PROJECT_ROOT = Path("/home/honglin/Nuclear-DC")
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
        r"LiBr gate: $T_{wb}\geq29\,^\circ$C": r"LiBr gate: $T_{\mathrm{wb}}\geq 29\,^\circ$C",
        r"Design: $T_{wb}=26\,^\circ$C": r"Design: $T_{\mathrm{wb}}=26\,^\circ$C",
        r"Wet-bulb $T_{wb}$ ($^\circ$C)": r"Wet-bulb $T_{\mathrm{wb}}$ ($^\circ$C)",
        r"design anchor\n(26 $^\\circ$C, COP 1.10)": r"design anchor\n(26 $^\\circ$C, COP 1.10)",
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
        'add_panel_label(ax_d_frame, "d", x=-0.075, y=1.03)': (
            'add_panel_label(ax_d_frame, "d", x=0.005, y=1.045)'
        ),
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    return source


def main() -> None:
    nb = json.loads(NB.read_text())
    env: dict[str, object] = {}

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
        exec(compile(src, f"paper_figures.ipynb:cell{idx}", "exec"), env)
        for ext in ("pdf", "svg", "png"):
            src_path = OUT_FIGS / f"{name}.{ext}"
            if src_path.exists():
                shutil.copy2(src_path, NATURE_FIGS / src_path.name)
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
