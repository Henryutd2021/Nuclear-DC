"""Nuclear-DC paper figure helpers.

Sources the NPPH2 palette + style + helper plot functions from the personal
``sci-figure`` skill at ``~/.claude/skills/sci-figure/scripts/``.  Adds project-
specific case/component mappings on top of that base.

This file stays framework-agnostic (no project imports beyond sci-figure) so
notebooks and scripts in this folder can be run standalone.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt

# --- Hook sci-figure into the import path -----------------------------

SCI_FIGURE_DIR = Path.home() / ".claude" / "skills" / "sci-figure" / "scripts"
if str(SCI_FIGURE_DIR) not in sys.path:
    sys.path.insert(0, str(SCI_FIGURE_DIR))

from sci_figure_helpers import (  # noqa: E402
    PALETTE as _SCI_PALETTE,
    apply_sci_style,
    save_triplet,
    add_panel_label,
    tornado,
    radar,
    duration_curve,
    bivariate_heatmap,
    violin_grouped,
    multi_stream_dispatch,
)


# --- Output locations -------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
FIG_DIR = OUTPUTS_DIR / "figures"
MASTER_CSV = OUTPUTS_DIR / "master_kpi_table.csv"
DATA_DIR = REPO_ROOT / "data"


# --- Palette (NPPH2 master + Nuclear-DC project overlays) ------------
#
# Cases map onto the NPPH2 case-identity axis; cost components map onto the
# stacked-cost axis; directional sign accents are reserved. See
# ``~/.claude/skills/sci-figure/references/palette.md`` for full provenance.

PALETTE = dict(_SCI_PALETTE)  # inherit all 23 sci-figure entries

# Project aliases — re-exported with paper-facing names for convenience
PALETTE.update({
    # Stacked TAC layers (used in Fig 2a)
    "capex":      PALETTE["fill_blue"],     # #BEE8FF
    "fom":        PALETTE["fill_orange"],   # #FFD37F
    "vom":        "#FFE6B3",                 # variant of fill_orange, lighter
    "fuel":       PALETTE["fill_salmon"],   # #FF7F7F
    "grid_buy":   PALETTE["stroke_clay"],   # #A46A4D
    "grid_sell":  "#62AE9E",                 # NPPH2 muted teal (positive flow)
    # Directional cues
    "pos":        PALETTE["accent_teal"],   # #29BD9A — Premium > 0
    "neg":        PALETTE["fill_salmon"],   # #FF7F7F — Premium < 0
    "neutral":    PALETTE["fill_gray"],     # #B9B9B9
    "zero_line":  "#222222",
    # Dispatch streams (Fig 4)
    "P_IT":         PALETTE["fill_blue"],   # large fill, IT base load
    "Q_cool":       PALETTE["fill_orange"], # large fill, cooling demand
    "P_orc":        PALETTE["accent_teal"], # positive flow
    "Q_abs":        PALETTE["fill_orange"], # supplied cooling (same hue as demand to show coverage)
    "P_grid_buy":   PALETTE["stroke_clay"], # warm, dirty
    "P_grid_sell":  "#62AE9E",               # positive flow
})


CASE_LABELS = {
    0: "C0\nGrid-only DC",
    1: "C1\nBWRX (no HR)",
    2: "C2\nBWRX cogen",
    3: "C3\nBWRX + ORC",
    4: "C4\nNGCC on-site",
}

SHORT_LABELS = {0: "C0", 1: "C1", 2: "C2", 3: "C3", 4: "C4"}


def case_color(case_id: int) -> str:
    """Return the canonical case-identity color for case_id in {0..4}."""
    return PALETTE[f"case{case_id}"]


def premium_color(value: float) -> str:
    """Return the directional Premium color: positive teal / negative salmon / neutral gray."""
    if value > 0:
        return PALETTE["pos"]
    if value < 0:
        return PALETTE["neg"]
    return PALETTE["neutral"]


# --- Style (sci-figure rcParams) -------------------------------------

def apply_nature_style() -> None:
    """Apply the sci-figure rcParams (NPPH2 + Nature-portfolio conventions).

    Kept under the legacy name so existing callers don't break; internally
    delegates to ``apply_sci_style`` with the AE single-column default.
    """
    apply_sci_style(width="ae_single")


# --- Sizes (Applied Energy / Nature column widths) -------------------

MM_PER_INCH = 25.4


def mm(*vals):
    """Convert a tuple of mm values to inches for ``figsize``."""
    return tuple(v / MM_PER_INCH for v in vals)


SINGLE_COL_MM = 89
ONE_HALF_COL_MM = 120
DOUBLE_COL_MM = 183


# --- Export ----------------------------------------------------------

def save_fig(fig: plt.Figure, stem: str, *,
             formats: Iterable[str] = ("pdf", "svg", "png")) -> None:
    """Export figure to FIG_DIR as PDF + SVG + PNG (legacy name)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    save_triplet(fig, stem, outdir=str(FIG_DIR))
    plt.close(fig)


# --- Panel labels (legacy name; delegates to sci-figure) -------------

def panel_label(ax, letter: str, *, x: float = -0.18, y: float = 1.06) -> None:
    """Add a bold panel label (a, b, c, ...) at standard offset."""
    add_panel_label(ax, letter, x=x, y=y, fontsize=8)


# --- Re-exports -------------------------------------------------------

__all__ = [
    # Palettes + labels
    "PALETTE", "CASE_LABELS", "SHORT_LABELS",
    # Paths
    "REPO_ROOT", "OUTPUTS_DIR", "FIG_DIR", "MASTER_CSV", "DATA_DIR",
    # Style + sizing
    "apply_nature_style", "apply_sci_style", "mm",
    "SINGLE_COL_MM", "ONE_HALF_COL_MM", "DOUBLE_COL_MM",
    # Export + labels
    "save_fig", "save_triplet", "panel_label", "add_panel_label",
    # Helpers
    "premium_color", "case_color",
    # sci-figure plot helpers (re-exported)
    "tornado", "radar", "duration_curve",
    "bivariate_heatmap", "violin_grouped", "multi_stream_dispatch",
]
