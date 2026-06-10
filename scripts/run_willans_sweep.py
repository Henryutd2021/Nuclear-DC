"""Supplementary alpha_w sensitivity: Case 2 at the 2023 ATB-Mid baseline with
the extraction Willans penalty swept over the physically plausible range.

Reported in Supplementary Note 7 alongside the value decomposition. Run:

    PYTHONPATH=. python3 scripts/run_willans_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cases.case1 import solve_case1  # noqa: E402
from src.cases.case2 import solve_case2  # noqa: E402
from src.config import load_config  # noqa: E402
from src.data import load_time_series  # noqa: E402

SLOPES = [0.08, 0.15, 0.20, 0.25]


def main() -> None:
    ts = load_time_series(PROJECT_ROOT, year=2023, num_hours=8760)
    cfg1 = load_config(case_id=1, project_root=PROJECT_ROOT)
    tac1 = solve_case1(cfg1, ts).tac_usd_per_yr

    rows = []
    for slope in SLOPES:
        cfg2 = load_config(case_id=2, project_root=PROJECT_ROOT)
        turbine = cfg2.case.turbine.model_copy(
            update={"extraction_willans_slope_MWe_per_MWth": slope}
        )
        case = cfg2.case.model_copy(update={"turbine": turbine})
        cfg2 = cfg2.model_copy(update={"case": case})
        r2 = solve_case2(cfg2, ts)
        abs_share = float(
            r2.Q_abs_cool_MWth.sum()
            / (r2.Q_abs_cool_MWth + r2.Q_VCC_cool_MWth).sum()
        )
        rows.append(
            {
                "alpha_w_MWe_per_MWth": slope,
                "tac_case2_usd_per_yr": r2.tac_usd_per_yr,
                "tac_case1_usd_per_yr": tac1,
                "case2_minus_case1_usd_per_yr": r2.tac_usd_per_yr - tac1,
                "absorption_share": abs_share,
            }
        )
        print(
            f"alpha_w={slope:.2f}: C2 TAC {r2.tac_usd_per_yr/1e6:.2f} M, "
            f"gap {(r2.tac_usd_per_yr-tac1)/1e6:+.2f} M, abs share {abs_share:.1%}"
        )

    out = PROJECT_ROOT / "outputs" / "figures" / "willans_sweep_case2.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
