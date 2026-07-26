"""Assemble submission_audit/results.json from the per-task artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SA = ROOT / "submission_audit"


def load(p: Path):
    with p.open() as f:
        return json.load(f)


results = {
    "meta": {
        "generated_for": "NUCLEAR-DC run-and-backfill brief (submission audit)",
        "date": "2026-07-26",
        # Short SHA, as elsewhere in this file: the full 40-hex form reads as a
        # high-entropy string to the repository's detect-secrets hook.
        "git_head": "485a072",
        "git_head_subject": "Rework the Applied Energy figures and make "
                            "every caption self-contained",
        "model_code_last_changed": "2026-06-10 (5b37dd5); worktree clean in src/ config/ data/ scripts/",
        "solver": "Gurobi 13.0.2 academic (expires 2026-12-16), Pyomo 6.9, "
                  "Method=2 barrier, Seed=42, MIPGap=1e-4, Threads=4/solve x 16 workers "
                  "(identical to the archived production grid)",
        "new_solves": {
            "gate": {"runs": 4, "wall_s": 40.0, "solve_s_sum": 22.9},
            "b1": {"runs": 9, "wall_s": 15.3, "solve_s_sum": 102.5},
            "b2_g9": {"runs": 72, "wall_s": 70.0, "solve_s_sum": 972.4,
                      "max_mip_gap": 4.348e-05},
        },
        "manuscript_note": (
            "main_applied_energy_v5.tex is NOT on this machine (searched "
            "repo + home). Local candidates (MANUSCRIPT/'Applied Energy'/"
            "main.tex at HEAD and the untracked Overleaf_upload_package_"
            "2026-06-26 snapshot) both lack the three v5-only anchor "
            "sentences from the brief, so v5 is a later evolution on the "
            "editing side. Per brief §0.1 the deliverable is therefore "
            "numbers-only; §11 backfill was not performed."
        ),
    },
    "gate": load(SA / "runs_gate" / "gate_check.json"),
    "B1": load(SA / "runs_b1" / "B1_results.json"),
    "B2": load(SA / "runs_b2" / "B2_results.json"),
    "B3": load(SA / "audit" / "B3_results.json"),
    "C5": load(SA / "audit" / "C5_results.json"),
    "C6": {
        "deliverables": [
            "submission_audit/C6_supplementary_note.tex",
            "submission_audit/C6_sources.md",
        ],
        "new_bibtex_keys": [
            "lenzen2008nuclear", "macknick2012water", "boulay2018aware",
            "wri2023aqueduct",
        ],
        "reused_bibtex_keys": ["atb2024nuclear", "li2026nuclearH2"],
        "compile_check": (
            "note inserted into a scratch copy of the repo manuscript and "
            "compiled (pdflatex+bibtex+pdflatex x2): 0 errors, 0 undefined "
            "citations/references; factor table auto-numbers after S5"
        ),
    },
    "M5": {
        "figure_label_shown": "-7.5",
        "unrounded_value_musd_yr": -7.545347124037054,
        "figure_regenerated": False,
        "verdict": (
            "The unrounded Willans extraction opportunity cost is "
            "-7,545,347.12 $/yr = -7.5453 M$/yr. At one decimal this rounds "
            "to -7.5, so the shipped fig_operation_value.pdf panel (c) label "
            "(-7.5) is already the correct unrounded-derived print and no "
            "regeneration is needed. Table S4's -7.55 is the correct "
            "two-decimal print of the same number. v5's change of the §3.2 "
            "prose from $7.5M to $7.6M is a double-rounding error "
            "(7.5453 -> 7.55 -> 7.6) and should be reverted to $7.5M."
        ),
        "source": "outputs/figures/value_decomp_case2.csv "
                  "(turbine_gen_lost_usd_per_yr, main_baseline/base row)",
    },
    "F": load(SA / "audit" / "F_results.json"),
}

with (SA / "results.json").open("w") as f:
    json.dump(results, f, indent=2)
    f.write("\n")  # keep the file end-of-file-fixer clean on regeneration
print("results.json written:",
      {k: (len(v) if isinstance(v, (list, dict)) else v)
       for k, v in results.items() if k != "meta"})
