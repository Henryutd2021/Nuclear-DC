#!/usr/bin/env python3
"""B1 boundary exploration — load-matched reactor sizing.

Question: the manuscript headline is a ~222% cost premium for colocated SMR
(Case 2) vs grid (Case 0). But the BWRX-300 is ~2x oversized vs the data
center's electricity load, net-exporting ~1.3 TWh/yr of merchant power.
Hypothesis: the premium is partly an OVERBUILD artifact.

Test: re-size the reactor so its annual NET generation ~= the data center's
annual electricity demand (eliminating the structural merchant surplus), then
re-run the 2023 ATB-Mid PUE-1.3 baseline for Cases 0/1/2 and recompute the
Heat-Recovery Premium HRP = 1 - TAC_case / TAC_case0.

Sizing rule (documented):
    required_net_capacity_MWe = annual_DC_electricity_load_MWh / (8760 h * CF)
    scale = required_net_capacity_MWe / current_net_MWe(=270)
    new thermal_power_MWth = 870 * scale ; new electric_power_net_MWe = 270*scale
    reactor CAPEX = $/kWe * capacity  ->  scales linearly with the resized capacity.

The annual DC electricity load is the on-site electricity the reactor must
serve = IT + VCC-electric + absorption parasitics, read from each case's
ORIGINAL-sizing dispatch at the baseline (= P_turb_net_annual - net_export).
This is exactly the quantity that, when matched, drives the structural net
export to ~0. CF = reactor.capacity_factor (0.92).

Everything else (prices, PUE 1.30, ATB-Mid $7,615/kWe, WACC 6.7%, absorption
block, VCC, BESS-off) is held identical to main_baseline.

Writes outputs/_b1_loadmatched/{b1_results.csv,b1_results.json}. Does NOT
touch main, master_kpi_table.csv, or the original configs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cases.case0 import solve_case0  # noqa: E402
from src.cases.case1 import solve_case1  # noqa: E402
from src.cases.case2 import solve_case2  # noqa: E402
from src.config import RunConfig, load_config, with_reactor_capex  # noqa: E402
from src.data import load_time_series  # noqa: E402

OUT_DIR = PROJECT_ROOT / "outputs" / "_b1_loadmatched"
YEAR = 2023
PUE = 1.30
DT = 1.0  # hourly
SOLVER = "gurobi"

CASE_SOLVERS = {0: solve_case0, 1: solve_case1, 2: solve_case2}


def baseline_cfg(case_id: int) -> RunConfig:
    """main_baseline cfg: 2023, PUE 1.30, ATB-Mid for nuclear cases."""
    cfg = load_config(case_id=case_id, project_root=PROJECT_ROOT)
    if case_id in (1, 2):
        cfg = with_reactor_capex(cfg, "ATB_Mid", PROJECT_ROOT)
    return cfg


def scale_reactor(cfg: RunConfig, scale: float) -> RunConfig:
    """Return a copy of cfg with the reactor scaled by `scale`.

    Scales the physics capacity (thermal_power_MWth and the
    capacities.reactor_thermal_capacity_MWth that bounds P_rx) and the
    cost-driving net electric capacity (electric_power_net_MWe). CAPEX is
    $/kWe * capacity, so capex_annual scales linearly with the resized
    electric_power_net_MWe (capex_usd_per_kWe is held identical).
    """
    rx = cfg.case.reactor
    new_rx = rx.model_copy(
        update={
            "thermal_power_MWth": rx.thermal_power_MWth * scale,
            "electric_power_net_MWe": rx.electric_power_net_MWe * scale,
        }
    )
    cap = cfg.case.capacities
    base_th = cap.reactor_thermal_capacity_MWth or rx.thermal_power_MWth
    new_cap = cap.model_copy(
        update={"reactor_thermal_capacity_MWth": base_th * scale}
    )
    new_case = cfg.case.model_copy(update={"reactor": new_rx, "capacities": new_cap})
    return cfg.model_copy(update={"case": new_case})


def annual(series, n: int) -> float:
    return float(series.sum() * DT * (8760.0 / n))


def solve_one(case_id: int, cfg: RunConfig, ts):
    if case_id == 0:
        r = solve_case0(cfg, ts, pue=PUE)
        n = r.P_IT_MW.shape[0]
        return {
            "tac": float(r.tac_usd_per_yr),
            "capex_annual": float(r.capex_annual_usd),
            "grid_revenue": -float(r.grid_annual_usd),  # revenue = -net grid cost
            "grid_annual_cost": float(r.grid_annual_usd),
            "net_export_MWh": 0.0,
            "grid_buy_MWh": annual(r.P_grid_buy_MW, n),
            "grid_sell_MWh": 0.0,
            "dc_elec_load_MWh": annual(r.P_grid_buy_MW, n),  # grid covers all DC elec
            "turb_net_MWh": 0.0,
        }
    solver = CASE_SOLVERS[case_id]
    r = solver(cfg, ts, pue=PUE, solver_name=SOLVER)
    n = r.P_IT_MW.shape[0]
    buy = annual(r.P_grid_buy_MW, n)
    sell = annual(r.P_grid_sell_MW, n)
    turb_net = annual(r.P_turb_net_MW, n)
    # DC on-site electricity load served by the reactor = turbine net minus the
    # structural net export (= IT + VCC-elec + absorption parasitics).
    dc_elec_load = turb_net - (sell - buy)
    return {
        "tac": float(r.tac_usd_per_yr),
        "capex_annual": float(r.capex_annual_usd),
        "grid_revenue": -float(r.grid_annual_usd),  # net grid is negative -> revenue
        "grid_annual_cost": float(r.grid_annual_usd),
        "net_export_MWh": sell - buy,
        "grid_buy_MWh": buy,
        "grid_sell_MWh": sell,
        "dc_elec_load_MWh": dc_elec_load,
        "turb_net_MWh": turb_net,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = load_time_series(project_root=PROJECT_ROOT, year=YEAR, num_hours=8760)

    cfg0 = baseline_cfg(0)
    cfg1 = baseline_cfg(1)
    cfg2 = baseline_cfg(2)

    cf = cfg2.case.reactor.capacity_factor          # 0.92
    cur_net_MWe = cfg2.case.reactor.electric_power_net_MWe  # 270
    cur_th_MWth = cfg2.case.reactor.thermal_power_MWth      # 870

    # ---- ORIGINAL sizing --------------------------------------------------
    print(">>> ORIGINAL sizing (main_baseline reproduction)")
    orig = {
        0: solve_one(0, cfg0, ts),
        1: solve_one(1, cfg1, ts),
        2: solve_one(2, cfg2, ts),
    }
    for c in (0, 1, 2):
        print(f"  Case {c}: TAC=${orig[c]['tac']/1e6:.3f}M  "
              f"net_export={orig[c]['net_export_MWh']/1e3:.1f} GWh  "
              f"dc_elec_load={orig[c]['dc_elec_load_MWh']/1e3:.1f} GWh")

    # ---- Load-matched sizing ----------------------------------------------
    # Use Case 2's on-site DC electricity load as the common sizing basis
    # (Case 2 is the flagship). Required net capacity = load / (8760 * CF).
    dc_load_MWh = orig[2]["dc_elec_load_MWh"]
    required_net_MWe = dc_load_MWh / (8760.0 * cf)
    scale = required_net_MWe / cur_net_MWe
    new_net_MWe = cur_net_MWe * scale
    new_th_MWth = cur_th_MWth * scale

    print("\n>>> LOAD-MATCHED sizing")
    print(f"  CF                       = {cf}")
    print(f"  DC annual elec load      = {dc_load_MWh:,.1f} MWh  "
          f"(avg {dc_load_MWh/8760.0:.2f} MW)")
    print(f"  required_net_MWe         = {required_net_MWe:.3f} MWe")
    print(f"  current_net_MWe          = {cur_net_MWe}")
    print(f"  scale                    = {scale:.4f}")
    print(f"  new electric_power_net   = {new_net_MWe:.2f} MWe")
    print(f"  new thermal_power        = {new_th_MWth:.2f} MWth")

    cfg1_lm = scale_reactor(cfg1, scale)
    cfg2_lm = scale_reactor(cfg2, scale)
    lm = {
        0: orig[0],  # Case 0 has no reactor; unchanged
        1: solve_one(1, cfg1_lm, ts),
        2: solve_one(2, cfg2_lm, ts),
    }
    for c in (0, 1, 2):
        print(f"  Case {c}: TAC=${lm[c]['tac']/1e6:.3f}M  "
              f"net_export={lm[c]['net_export_MWh']/1e3:.1f} GWh")

    # ---- HRP ---------------------------------------------------------------
    tac0_orig = orig[0]["tac"]
    tac0_lm = lm[0]["tac"]

    rows = []
    for sizing, res, tac0 in (("original", orig, tac0_orig),
                              ("load_matched", lm, tac0_lm)):
        for c in (0, 1, 2):
            d = res[c]
            hrp = 1.0 - d["tac"] / tac0
            rows.append({
                "case": c,
                "sizing": sizing,
                "TAC_usd_per_yr": d["tac"],
                "capex_annual_usd": d["capex_annual"],
                "grid_revenue_usd_per_yr": d["grid_revenue"],
                "grid_annual_cost_usd_per_yr": d["grid_annual_cost"],
                "net_export_MWh": d["net_export_MWh"],
                "grid_buy_MWh": d["grid_buy_MWh"],
                "grid_sell_MWh": d["grid_sell_MWh"],
                "HRP": hrp,
            })

    # CSV
    import csv
    csv_path = OUT_DIR / "b1_results.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # JSON (with sizing provenance)
    payload = {
        "question": "B1 load-matched reactor sizing vs 222% premium overbuild hypothesis",
        "baseline": {"year": YEAR, "pue": PUE, "reactor_scenario": "ATB_Mid",
                     "wacc_nominal": cfg2.financial.WACC_nominal,
                     "crf": cfg2.financial.capital_recovery_factor},
        "sizing": {
            "capacity_factor": cf,
            "dc_annual_elec_load_MWh": dc_load_MWh,
            "dc_avg_load_MW": dc_load_MWh / 8760.0,
            "required_net_MWe": required_net_MWe,
            "current_net_MWe": cur_net_MWe,
            "scale": scale,
            "new_electric_power_net_MWe": new_net_MWe,
            "new_thermal_power_MWth": new_th_MWth,
            "current_thermal_power_MWth": cur_th_MWth,
        },
        "results": rows,
        "hrp": {
            "original": {c: 1.0 - orig[c]["tac"] / tac0_orig for c in (0, 1, 2)},
            "load_matched": {c: 1.0 - lm[c]["tac"] / tac0_lm for c in (0, 1, 2)},
        },
    }
    json_path = OUT_DIR / "b1_results.json"
    with json_path.open("w") as f:
        json.dump(payload, f, indent=2)

    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")

    # ---- Sanity check vs manuscript ---------------------------------------
    print("\n>>> SANITY CHECK vs manuscript (original sizing)")
    print(f"  Case0 TAC ${orig[0]['tac']/1e6:.2f}M (manuscript ~$64.3M)")
    print(f"  Case1 TAC ${orig[1]['tac']/1e6:.2f}M (manuscript ~$203M)")
    print(f"  Case2 TAC ${orig[2]['tac']/1e6:.2f}M (manuscript ~$207M)")
    print(f"  HRP Case2 {100*(1.0 - orig[2]['tac']/tac0_orig):.1f}% (manuscript ~-222%)")


if __name__ == "__main__":
    main()
