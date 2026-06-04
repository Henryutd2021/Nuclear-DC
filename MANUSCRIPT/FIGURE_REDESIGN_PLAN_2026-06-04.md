# Figure & Table Redesign Plan -- Nature Energy version

Date: 2026-06-04. Scope: a from-scratch redesign of the *entire* display set (main text + SI),
driven by the paper's thesis, the un-visualized findings in `outputs/`, and the redundancy in the
current set. Nothing here is implemented yet -- this is the plan to approve before any figure or
manuscript edit.

Method: three independent design proposals (thesis-minimal / evidence-complete / reviewer-defensive)
were generated against a fresh data mining of `outputs/` (22 quantities catalogued, 7 with no current
figure) and a redundancy map read off the *rendered* figures, then merged into one recommended scheme.
Every load-bearing number below was verified directly against `master_kpi_table.csv`,
`dispatch.csv.gz` (8760 rows), `value_decomp_case2.csv`, and the wet-bulb input file. No reruns are
needed; no number is invented.

---

## Controlling thesis (the ring every display item must serve)

> A colocated BWRX-300 SMR with double-effect LiBr absorption cooling is a **conditional**, not
> categorical, low-carbon supply for a 200 MW_e hyperscale data center in ERCOT. The **binding
> condition is reactor capital reaching NOAK combined with the Section 45U credit**; absorption cooling
> is approximately cost-neutral and does **not** move the boundary, which is set by reactor capital.

The five argument beats: **B0** define the system + the conditional framing -> **B1** the reference-point
cost penalty and the carbon prize -> **B2** the PTC is the decisive lever (only at NOAK) -> **B3**
absorption is a characterized cost-neutral no-op -> **B4** reactor capital is the control across every axis.

---

## Target: 5 figures + 3 tables (= 8 main display items), SI = 9 figures + 9 tables

This matches the Fig 1-5 / Table 1-3 the author hinted, holds the Nature Energy main set at the 8-item
ceiling, and pushes every secondary result to a referenced-but-not-load-bearing SI home.

---

## MAIN TEXT

### Figure 1 -- Orientation + conditional framing (Beat 0)
*Provenance: reuse `fig1_system_schematic`; UPGRADE the inset.*
- **(a)** Engineered system schematic. BWRX-300 -> HP turbine -> mid-pressure extraction -> double-effect
  LiBr absorber for DC cooling, VCC backup, ~1.43 TWh/yr net export to ERCOT. The four cases are toggles
  on this one boundary, sharing one exogenous IT-load trace.
- **(b)** Boundary-condition inset, upgraded from a conceptual box to **real miniature exogenous traces**:
  ERCOT LMP duration (median ~$20/MWh) + Houston wet-bulb duration. Previews *why* the result is
  conditional. Data: `data/price_grid.csv`, `data/weather/houston_wet_bulb_combined.csv`.

### Figure 2 -- Reference-point cost penalty + the carbon prize (Beat 1)
*Provenance: reuse `fig2_tac_stack` as (a); NEW four-case CO2 panel (b). Old 2b scatter CUT; old 2c -> SI S6.*
- **(a)** Stacked-bar TAC decomposition, 4 cases (capex / FOM / VOM / fuel / net-grid / **45U credit as a
  distinct slice**). Case0 $78.1M; Case1 $192.2M (credit -$26.4M); Case2 $194.6M (credit -$25.8M);
  Case3 $55.7M. The Case2-Case1 gap is a near-invisible +$2.4M sliver -- the gap is a capital problem,
  not a cooling one. Data: `master_kpi_table.csv` group `main_baseline`.
- **(b)** Diverging horizontal bar: **signed net annual CO2, all four cases** (with kg/MWh_IT intensity
  labels). Case0 +369 / Case3 +486 (emitters) vs Case1 -388 / Case2 -448 ktCO2/yr (net-negative via the
  export credit). Only the SMR cases are net-negative -- the climate prize, stated once across the full
  case set. Replaces the off-thesis Pareto scatter and the nuclear-only accounting bars.

### Figure 3 -- THE PTC lever (Beat 2) -- NEW, the paper's missing headline
*Provenance: NEW from `s4_capex` + `s2_price`. This is the #1 missing figure; all three proposals made it non-negotiable.*
- **(a)** Paired **dumbbell / slope**: pre-credit vs post-credit grid-cost margin at FOAK / ATB-Mid / NOAK,
  Case1 and Case2 side by side. The credit is a near-constant **+0.34 margin step**; the pre-credit gap is
  -4.06/-3.72 (FOAK), -1.80/-1.46 (ATB), but only -0.089 pre -> **+0.249 post** at NOAK (Case1; Case2
  -0.112 -> +0.218). Only at NOAK is the pre-credit gap small enough for the fixed step to cross zero.
  *Verified against `s4_capex`.*
- **(b)** Grouped bar: **realized 45U credit by market year vs the NOAK pre-credit gap band**. The
  price-indexed credit collapses to $7.6-7.8M in low-price 2022 vs $26.4M (2023) / $28.5M (2024). Since the
  NOAK pre-credit gap is only +$6.9-8.7M, a 2022-style year would barely close it -- the lever is itself
  contingent on energy prices saturating the credit. *Verified against `s2_price`; previously prose-only.*

### Figure 4 -- Absorption is a characterized cost-neutral no-op (Beat 3)
*Provenance: NEW gate curve (a) from dispatch+wet-bulb; reuse `fig4bis_value_decomp` as (b). Both dispatch weeks -> SI S2.*
- **(a)** Binned curve + hour-count underlay: **VCC-backup share of cooling vs wet-bulb temperature**
  (annual, 2023). The crystallization/peak gate is a *smooth thermal derating*, not a hard cutoff: VCC
  share climbs from ~25% of hours below 15 C to ~58% (28.8 MW_th mean) above 26 C across 763 hours, yet
  absorption still meets 93.5% of annual cooling. Shows exactly when/why absorption cedes load.
  Data: `dispatch.csv.gz` (Q_abs_cool, Q_VCC_cool) joined to wet-bulb on hour.
- **(b)** Value waterfall: Case2-Case1 = **-$2.39M/yr**. +$15.98M net avoided VCC electricity is offset by
  -$4.15M lost turbine generation, -$13.22M absorber capex+FOM, -$2.26M crystallization backup, -$2.04M
  forgone export PTC. Absorption is a genuine wash, far too small to move the capital-set boundary.
  *Verified against `value_decomp_case2.csv`.*

### Figure 5 -- Reactor capital is the control (Beat 4) -- the robustness atlas
*Provenance: reuse `boundary_atlas` heatmap (a) + `policy_summary` tornado (b) + old Fig 3a load-margin (c).
Consolidates four previously over-told beats. Old Fig 6a/6b/6c, old Fig 3b/c/d, old Fig 7a all cut/demoted.*
- **(a)** 5x5 heatmap: Case2 margin over reactor-capex x absorber-capex with the parity contour. Margin
  crosses positive **only in the NOAK band** (grid span -3.83 to +0.27); absorber capital never crosses
  parity at any reactor tier and shifts margin by <0.06. Reactor capital sets the boundary; absorption is
  near-orthogonal. *Verified: 25 cells, min -3.829 max +0.270.*
- **(b)** Ranked tornado: Case2 margin sensitivity across all solved axes. Reactor capex dominates by an
  order of magnitude; WACC (~106 pp), market year, load-matching follow; PUE (~22 pp) and BESS (~0.8 pp)
  negligible. *WACC span -115/-149/-221% verified.*
- **(c)** Line: Case2 margin vs load multiplier 0.5x-3.0x with the parity line and the net-export-zero
  marker (~2.5x). Scale helps but never reaches parity -- a bigger DC is not a substitute for cheaper
  reactor capital. Data: `s8_case2_cost_audit.csv` + `s8_size_matching`.

### Table 1 -- Case configuration matrix
*Reuse current `tab:cases`.* Rows Case0-3; columns grid import/export, BWRX-300, HP-turbine extraction,
LiBr absorber, VCC (primary/backup), NGCC, BESS, grid connection, 45U eligibility.

### Table 2 -- Reference-point ledger (NEW)
One row per case at 2023 ATB-Mid: TAC, capex/FOM/VOM/fuel/net-grid split, 45U credit, margin M, net CO2,
CO2 intensity (kg/MWh_IT), water (L/MWh_e), net export (TWh). Puts every number behind Figs 2-3 in one
auditable place. Data: `main_baseline` + per-run `summary.json`.

### Table 3 -- Capital-tier headline table (NEW)
Rows FOAK / ATB-Mid / NOAK; columns Case1 M_pre, M_post, Case2 M_pre, M_post, 45U credit ($M),
**carbon-abatement cost ($/tCO2)**. NOAK +25%/+22% post-credit; FOAK -372/-375%; CAC -26 (NOAK, cheaper
AND cleaner) to +384 (FOAK). Makes the zero-crossing at NOAK explicit and attaches the policy currency.
*CAC verified -25.67 to +383.84 against `s4_capex`.*

---

## SUPPLEMENTARY INFORMATION

### SI figures
- **S1** Exogenous inputs overview (wet-bulb dist., LMP duration, IT-load weeks, COP-vs-wet-bulb). *Reuse `fig_inputs_overview`.*
- **S2** Representative-week hourly dispatch (winter + summer), annotated that both weeks stay below the gate. *Reuse old Fig 4a/4b, relocated.*
- **S3** DEFENSIVE: NGCC running-cost vs LMP duration overlay -- the ~42-44% of hours grid is cheaper that islanded Case3 forgoes, + single-unit availability gap. *NEW; previously prose-only.*
- **S4** DEFENSIVE: water-carbon tension across four cases (Case2 8491 L/MWh_e & 5.5 m3-eq vs grid 1999, NGCC 1148). Low-carbon = high-water. *NEW; previously no figure.*
- **S5** DEFENSIVE: carbon crossover + abatement cost vs export-credit retention (100/50/0%) -- halving the 1.43 TWh credit roughly doubles the crossover. *Arithmetic on solved CO2; previously prose-only.*
- **S6** Four-case net-CO2 intensity + per-year nuclear internals (demoted from main). *NEW from `main_baseline` + `s2_price`.*
- **S7** PUE cooling-response detail: TAC diff + net cooling saving vs PUE, break-even ~1.40. *From `value_decomp_case2.csv` `s1_pue`.*
- **S8** Size-matching one-axis detail: margin + net export vs load 0.5-3.0x. *Reuse `fig12_s8_size_matching` margin/export panels.*
- **S9** BESS on/off: ~$0.63M/yr (~0.8 pp), never changes ranking. *NEW from `s3_battery`.*

### SI tables
- **S1** Nomenclature.
- **S2** Input-data sources + provenance URLs.
- **S3** Full equipment / techno-economic parameters (superset of main).
- **S4** Market-by-year results (carries the cut Fig 6a year beat).
- **S5** Absorption value-decomposition ledger across PUE/year/capex.
- **S6** Size-matching full ledger (TAC, margin, $/MWh_IT, excess, net export).
- **S7** WACC sensitivity (carries the cut Fig 6c beat).
- **S8** Section 45U PTC realization by case and year (statute mapping + realized $/yr).
- **S9** Scenario ledger / full run manifest (reproducibility).

---

## What gets cut (all audit-confirmed) and where it goes

| Current item | Verdict | Disposition |
|---|---|---|
| Fig 2b cost-vs-CO2 scatter | off-thesis, redundant with 2a+2c | **cut** (years -> Table S4) |
| Old Fig 2c nuclear-only accounting (6 bars) | 6 bars, 2 numbers, nuclear internals only | replaced by four-case 2b; internals -> SI S6 |
| Fig 3b / 3c / 3d (size-matching) | one-axis over-tell; rescalings of 3a | numbers -> Table S6; export -> SI S8; 3a survives as Fig 5c |
| Fig 5b / 5c / 5d (cooling response) | 5c rescales 5a; 5b duplicates Table S5; 5d mis-placed carbon panel | beat now told by Fig 4a; break-even -> SI S7 |
| Fig 6a / 6b / 6c (one-axis sweeps) | 6b IS the $750 column of the 6d heatmap; 6a -> Table S4; 6c -> tornado | collapse into Fig 5a + 5b; year -> Table S4, WACC -> Table S7 |
| Both dispatch weeks (old Fig 4a/4b) | both stay below the gate; texture not mechanism | -> SI S2; mechanism now Fig 4a gate curve |
| Fig 7a carbon-crossover lines | the demoted secondary route | -> Table 3 CAC column + SI S5 |

## What gets added (un-visualized findings now surfaced)

1. **PTC pre/post-credit dumbbell** (Fig 3a) -- the paper's headline mechanism, previously prose-only.
2. **PTC price-fragility** (Fig 3b) -- credit collapses to ~$7.6M in 2022; NOAK viability is price-contingent.
3. **Crystallization-gate derating curve** (Fig 4a) -- VCC share vs wet-bulb; when/why absorption fails.
4. **Four-case signed CO2 sign-flip** (Fig 2b) -- the carbon prize across the full case set.
5. **Carbon-abatement cost** (Table 3) -- the policy currency, -26 to +384 $/tCO2.
6. **Water-carbon tension** (SI S4) -- the genuine low-carbon/high-water trade-off, ~4-7x grid/NGCC.
7. **Export-credit dependence of the carbon route** (SI S5) -- the crossover's fragility.
8. **NGCC merit-order/islanding gap** (SI S3) and **BESS** (SI S9) -- defensive completeness.

---

## Build note (not a user decision -- a correctness guard)

`ptc_annual_usd` is stored as a **negative** value (a credit). The dumbbell math is
`M_pre = 1 - (tac - ptc)/tac0` with `ptc` kept negative, so removing the credit *raises* TAC. Building
off the prose sign (`~$26M` positive) would invert the dumbbell and silently invert the headline. Bake
`assert ptc < 0` and `assert M_post > M_pre` into the plotting script so the convention cannot regress.

---

## Decision points (yours)

1. **Carbon route placement.** Keep it out of the main figures (CAC in Table 3, crossover + export-credit
   dependence in SI S5) -- *recommended*; or spend a main Fig 5 panel on it; or a 6th main figure (breaks
   the ceiling). *Rec: Table 3 + SI -- the carbon route is the paper's explicitly demoted secondary route.*
2. **Dispatch weeks.** Move both weeks to SI S2 and make Fig 4 the gate curve + waterfall -- *recommended*;
   or keep both weeks in main Fig 4 (3 panels); or keep one summer week. *Rec: SI -- both weeks stay below
   the gate, so they show texture, not the mechanism.*
3. **Fig 1 inset.** Upgrade to real LMP + wet-bulb duration miniatures -- *recommended*; or keep the
   conceptual box; or LMP-only. *Rec: real traces -- they preview the two conditions that make the result
   conditional, at trivial cost.*
