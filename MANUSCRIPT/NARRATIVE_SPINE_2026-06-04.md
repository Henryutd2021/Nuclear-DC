# Narrative Spine -- Nature Energy version (text line)

Date: 2026-06-04. Scope: the prose argument framework (the "text line"), designed to be read together
with the figure line in `FIGURE_REDESIGN_PLAN_2026-06-04.md`. This is an architecture, not drafted prose:
each unit states the job it does and the verified number it carries. Nothing is implemented yet.

Method: three independent narrative architectures (boundary-identity / mechanism-first / decision-framing)
were merged into one spine, then a claim-figure correspondence audit checked that every figure has a
Results home and every headline claim has a figure + number. Two links are flagged for a pre-drafting
build-gate (below).

Venue (Nature Energy Article, locked): abstract = 150 words, single unreferenced paragraph with a
"Here we ... We show ..." pivot; main text ~3000 words; introduction has no heading; Results may use
short subheadings; Discussion has no subheadings; Methods last; title <=20 words.

---

## Controlling thesis and one-sentence argument

> **Thesis:** A colocated BWRX-300 SMR with double-effect LiBr absorption cooling is a **conditional**, not
> categorical, low-carbon supply for a 200 MW_e hyperscale data center in ERCOT, **because** the Section 45U
> credit is a near-constant +0.34 grid-cost-margin step whose only zero-crossing is at nth-of-a-kind
> reactor capital; absorption cooling is cost-neutral and never moves that boundary.

The chosen framing reconciles honesty and novelty: the conditional verdict is the **what**, the
fixed-credit-step-at-NOAK is the **why**, and the data prove they are the same finding. Lead every framing
unit with the verdict stated *as* the located mechanism.

---

## Abstract (150 words, single paragraph, 6 sentences)

| # | Role | What the sentence does |
|---|---|---|
| S1 | context | Data centers are a fast-growing near-continuous load intensifying demand for firm low-carbon supply; colocated SMRs with absorption cooling could meet it while reusing reactor heat. |
| S2 | gap | Their economics are rarely tested with hourly cooling physics, multi-year market prices and current U.S. tax policy together, so whether the strategy is categorical or only conditional is unresolved. |
| S3 | here-we-show pivot | Here we co-optimize the annualized cost of a 200 MW_e ERCOT data center at hourly resolution across four configurations and eight sensitivity axes, with the Section 45U credit applied throughout. |
| S4 | key result -- the mechanism = the honest verdict | The credit is a near-constant margin step that flips both SMR configurations below grid cost (by 25 and 22%, no carbon price) **only once reactor capital reaches nth-of-a-kind**; at mid-range capital they cost about 2.5x grid and only on-site gas undercuts it. |
| S5 | key result -- the no-op + the control | Absorption cooling is close to cost-neutral (net -$2.4M/yr) and does not move the boundary, which a joint reactor-by-absorber capital atlas confirms is set almost entirely by reactor capital. |
| S6 | boundary / takeaway | SMR supply for data centers is therefore conditional on nth-of-a-kind capital under the credit -- itself contingent on prices saturating the credit and on crediting merchant exports -- a procurement condition that travels to other markets, climates and campus sizes. |

---

## Introduction (5 paragraphs, ~600 words; cut from the current 8)

| Para | Role | Job |
|---|---|---|
| P1 | demand shock + firm-low-carbon need | The demand shock and where it lands. U.S. DC consumption nearly doubled 2019-2023, projected 6.7-12% of U.S. power by 2028 (LBNL); IEA ~945 TWh global by 2030; ERCOT large-load queue >138 GW. The new load is continuous and concentrated in ERCOT/PJM, making firm dispatchable low-carbon supply the binding need. Carry only the LBNL share + ERCOT queue numbers. |
| P2 | why SMR + absorption is the candidate system | Fold old load-requirements + SMR-fit. DC loads (CF near 1, five-nines, cooling 20-40% and wet-bulb-sensitive in Texas) match 50-300 MW_e SMRs, whose steam cycle can drive a double-effect absorber from extraction heat (high driving temperature from the steam cycle, not rack exhaust). Recent hyperscaler-reactor deals make it a live option. End by naming the system: BWRX-300 + LiBr absorber for a 200 MW_e campus. |
| P3 | two converging prior-work streams + the gap | Fold both literature streams + the gap into one. Stream 1 (SMR cost competitiveness: Asuega et al., INL meta-analysis, ATB FOAK-NOAK >6x spread) finds nuclear above grid absent carbon, capital as a one-axis sweep. Stream 2 (waste-heat/absorption) scores heat reuse categorically vs a no-recovery baseline. Gap: no one couples wet-bulb COP derating + crystallization gate to multi-year ERCOT/Henry Hub prices, reactor-capital paths AND the 45U credit, nor builds a multi-axis envelope -- so viability hinges on the chosen year and capital path, and the field has missed how a fixed policy instrument interacts with the capital axis. |
| P4 | here we present -- study as a boundary analysis | One paragraph. Hourly MILP co-optimizing power/cooling/storage at 8760-h for four cases (0 grid+VCC; 1 SMR+VCC; 2 SMR+absorption with VCC backup + crystallization gate; 3 NGCC+VCC), eight axes, 2022-2024 ERCOT/Henry Hub/wet-bulb, 45U on the nuclear cases. Frame explicitly as a boundary analysis -- not yes/no but under which conditions the boundary closes. Point to Table 1. |
| P5 | three advances + headline thesis (no numbers) | Three advances as what the paper settles: (i) first co-optimization coupling an hourly absorption submodel (wet-bulb COP derating + crystallization gate) to multi-year price and reactor-capital paths under live 45U; (ii) isolates the credit as a fixed margin step and locates its sole zero-crossing at NOAK, separating the two-axis capital test from one-axis moves toward parity; (iii) converts the envelope into a joint reactor-by-absorber atlas + portable procurement conditions. Payoff sentence (no numbers): the decision turns on reactor capital reaching NOAK under the credit, and absorption does not move that boundary. |

---

## Results (~1500 words, four figure beats, one Results part each; short subheadings allowed)

### Beat 0 -- "A colocated SMR-absorption system on the ERCOT boundary" (~220 words; lightest)
Owns **Fig 1** (schematic + real LMP/wet-bulb duration inset) + **Table 1** (case matrix).
Opening claim: the four configurations are block-toggles on one engineered boundary serving a single
exogenous 200 MW_e load, exposed to two exogenous drivers (ERCOT price, Houston wet-bulb) that make the
result conditional. Unfolds: (1) orient on Fig 1a (BWRX-300 -> HP turbine -> extraction -> LiBr absorber,
VCC backup, ~1.43 TWh/yr net export; 270 MW_e-net reactor ~2.9x the 94.7 MW_e mean campus); (2) Fig 1b
previews *why* conditional -- the LMP duration (median ~$20/MWh) and wet-bulb duration the credit value and
absorber availability ride on; (3) Table 1 anchors the clean four-case structure; (4) state the two
organizing facts and hand off (mid-range ~2.5x grid even after the credit; the gap closes only on the
lowest-capital edge).

### Beat 1 -- "A large baseline cost penalty alongside a net-negative carbon footprint" (~340 words)
Owns **Fig 2a** (4-case TAC stack, 45U as own slice) + **Fig 2b** (4-case signed net-CO2) + **Table 2**.
Opening claim: at 2023 ATB-Mid both SMR cases cost ~2.5x grid even after the credit, yet only the SMR cases
are net-carbon-negative -- penalty and prize coexist. Unfolds: (1) Fig 2a -- Case0 $78.1M (93% the ERCOT
bill), Case1 $192.2M (credit -$26.4M), Case2 $194.6M (credit -$25.8M), Case3 $55.7M (+29%, the only on-site
winner, 2023 gas $2.63/MMBtu); reactor capital dominates; (2) the no-op made visible early -- Case2-Case1 is
a +$2.4M sliver, a capital not a cooling problem (foreshadows Beat 3); (3) Fig 2b -- the sign-flip:
Case0 +369 / Case3 +486 (emitters) vs Case1 -388 / Case2 -448 ktCO2/yr (net-negative via the export credit);
(4) Table 2 carries the auditable per-case detail; (5) close on the tension -> what closes the cost gap?

### Beat 2 -- "The credit is a fixed margin step that flips the sign only at NOAK" (~420 words; MOST space)
Owns **Fig 3a** (pre/post-credit dumbbell FOAK/ATB/NOAK) + **Fig 3b** (PTC by year vs NOAK gap) + **Table 3**.
Opening claim: the 45U credit is a near-constant +0.34 margin step decisive precisely at NOAK -- where the
pre-credit gap is small enough for the fixed step to cross zero -- and immaterial against the far larger
FOAK/mid-range gaps; a zero-crossing a capital-only analysis omitting the credit would miss. Unfolds:
(1) Fig 3a -- the credit adds a near-fixed +0.338 (C1)/+0.330 (C2) at every tier; pre-credit margins
-4.06/-1.80/-0.089 (C1 FOAK/ATB/NOAK), so only at NOAK does the step land positive (+0.249 C1 / +0.218 C2);
(2) headline cleanly: NOAK +25%/+22%, FOAK -372%/-375%, ATB -146%/-149%; (3) Fig 3b price-fragility --
realized credit collapses to ~$7.6M in 2022 vs $26.4M (2023)/$28.5M (2024), and the NOAK pre-credit gap is
only +$6.9-8.7M, so a 2022-style year barely closes it; (4) Table 3 attaches the policy currency
(M_pre/M_post + credit + carbon-abatement cost -$26/tCO2 at NOAK to +$384 at FOAK); (5) close by locating
the boundary on the reactor-capital axis -- the rest of the paper asks whether anything else moves it.

### Beat 3 -- "Thermal integration is a characterized wash" (~300 words)
Owns **Fig 4a** (VCC-share vs wet-bulb gate curve) + **Fig 4b** (Case2-Case1 value waterfall, -$2.39M/yr).
Opening claim: adding absorption is a genuine wash (net -$2.39M/yr), far too small to move a capital-set
boundary, and its failure mode is a smooth derating not a hard cutoff. Unfolds: (1) Fig 4a -- VCC share
climbs ~25% (<15 C) to ~58% (28.8 MW_th mean, >26 C) across 763 h, yet absorption meets 93.5% of annual
cooling; full shutdown rare (~115 h/yr); replaces dispatch-week texture with the mechanism; (2) Fig 4b --
+$15.98M net avoided VCC electricity offset by -$4.15M lost turbine, -$13.22M absorber capex+FOM, -$2.26M
backup, -$2.04M forgone PTC; (3) the sign is conditional but small -- break-even near PUE ~1.40, positive
only against an inefficient chiller or with carbon priced (defer PUE detail to SI); (4) close on the
structural point: ~3 pp of margin against a capital axis spanning hundreds of points, so the absorber is
specified on cooling merit, boundary untouched.

### Beat 4 -- "A viability atlas confirms reactor capital sets the boundary" (~340 words)
Owns **Fig 5a** (5x5 capital heatmap) + **Fig 5b** (tornado) + **Fig 5c** (load sweep).
Opening claim: across the joint capital frontier and every solved axis the ranking is governed almost
entirely by reactor capital; no other lever opens a viable region alone. Unfolds: (1) Fig 5a -- margin
crosses positive only in the NOAK band (span -3.83 to +0.27); whole NOAK row competitive (+27% to +14%);
absorber shifts margin <13 pp, never crosses parity; (2) Fig 5b -- reactor capex dominates by an order of
magnitude; WACC follows (-115/-149/-221% at 5/6.7/10%); PUE ~22 pp and BESS ~0.8 pp negligible; (3) Fig 5c
-- scaling 0.5-3.0x cuts cost intensity ($235->$143/MWh_IT) and reaches export balance ~2.5x but never
parity (52% above grid even at 3.0x); (4) close by naming the carbon route as the explicitly weaker second
path (crossover ~142-151 $/tCO2, extrapolated, export-credit contingent), so the Discussion opens on the
conditional result rather than re-deriving it.

---

## Discussion + Conclusion (~900 words, 8 paragraphs, no subheadings; NE merges Conclusion into the close)

| Para | Role | Job |
|---|---|---|
| D1 | thesis as located mechanism | Lead: across four cases and eight axes the ranking is governed by reactor capital + the 45U credit; mid-range +149% above grid even after the credit, NOAK -22%/-25% below with no carbon price; the economics turn on whether capital reaches NOAK, not on thermal integration. Present "above grid except at NOAK" as a precise location, not a weakness. |
| D2 | the binding boundary + the mechanism (primary contribution) | The joint reactor-by-absorber frontier is the binding boundary; reactor axis controls it (absorber <13 pp; one tier above NOAK drops below -60%); the credit is decisive at NOAK because that is the only tier where the fixed +0.34 step meets a pre-credit gap (~10%) small enough for a ~$26M credit to cross zero. The discovery a capital-only reading misses. |
| D3 | the other axes shape but do not open parity | Size matching removes overbuild (export balance at 2.5x) but stays 62% above the matched grid baseline (excess $140->$49/MWh_IT); market regime sets only the gas window (NGCC wins 2023, not 2022/2024); financing + storage compress but cannot eliminate the gap. Nuclear's ranking is a capital question. |
| D4 | carbon price = weaker, contingent second route | Demote explicitly: nuclear falls below grid only near $142-151/tCO2 (extrapolated beyond solved $0-100) and only by crediting ~1.43 TWh/yr export at hourly average intensity; halving the credit ~doubles the crossover, removing it pushes it beyond any modeled price. The NOAK route needs no carbon price -- the more robust path. |
| D5 | absorption refines prior work | Position the +$2.4M/yr (3.1 pp) penalty (sign flips above PUE ~1.40 or with carbon priced) vs the two streams: waste-heat studies scoring integration categorically overstate it for a steam-cycle reactor serving an efficient campus; SMR TEAs placing nuclear above grid absent carbon (Asuega) hold at mid-range but not at NOAK under the credit. Correction (categorical -> conditional), not a null. Name the water-carbon tension (Case2 ~8491 vs grid 1999, NGCC 1148 L/MWh_e) as a genuine unpriced trade-off. |
| D6 | limitations that bound the conclusions | The load-bearing ones: single hyperscale load shape/climate; one uniform carbon price on both average-intensity export credit and direct-emissions debit using average not marginal factors; demand charges/ancillary revenues unmodeled (on-site penalties conservative); gas comparator omits five-nines redundancy (erodes its 29% edge); PTC at full prevailing-wage PPA value on all net generation, nominal through 2032 (behind-the-meter or expiry weakens NOAK competitiveness); single smallest reactor not an optimized multi-module buildout. |
| C1 | procurement synthesis (conditions that must coincide) | Convert the boundary into a procurement short list: NOAK reactor capital, the 45U credit, a load large enough to absorb the smallest commercial reactor, and an ERCOT price regime that saturates the credit. Where they hold, the plant beats grid with no carbon price and the absorber is specified on cooling merit; where capital stays FOAK/mid-range, neither thermal integration nor any plausible carbon price closes the gap. |
| C2 | generalization + outlook | Close on portability: the SI envelope + provenance support re-running the boundary analysis with region-specific tariff, market-service and marginal-emissions data for other ISOs, climates and sizes; the conditional finding travels as a transferable method, and the binding condition -- reactor capital -- is expected to persist. |

---

## Word budget (~3000 words; abstract + Methods excluded)

Intro ~600 (5 x ~120) | Results ~1500 (Beat0 ~220, Beat1 ~340, Beat2 ~420, Beat3 ~300, Beat4 ~340) |
Discussion+Conclusion ~900 (8 x ~110). Each headline number appears once in Results, echoed once in
Discussion, never re-derived.

---

## Claim <-> figure correspondence (every figure has a Results home; every claim a number)

All links **locked** except two, flagged below. Locked examples: Fig 2a -> Beat 1 ($78.1/192.2/194.6/55.7M);
Fig 3a -> Beat 2 (step +0.338/+0.330, NOAK -0.089->+0.249); Fig 4b -> Beat 3 (net -$2.39M, exact);
Fig 5a -> Beat 4 (span -3.83 to +0.27); Table 3 -> Beat 2 (CAC -25.7 to +383.8).

### Two flagged links (pre-drafting build-gates)
1. **Fig 4a gate curve (WEAK).** The waterfall (4b) is exactly verified; the gate-curve numbers
   (VCC share 25%->58%, 763 h, 93.5% annual cooling, ~115 h shutdown) are asserted in the redesign plan /
   current prose but **not re-derived** from the `dispatch.csv.gz` x wet-bulb join in this audit. Build-gate:
   recompute `Q_abs_cool / (Q_abs_cool + Q_VCC_cool)` binned by wet-bulb and the 93.5% before writing the
   caption -- same assert-pattern that protects the 4b sign.
2. **Carbon-route crossover (WEAK by design).** ~$142-151/tCO2 nuclear, ~$191 NGCC are **extrapolations**
   beyond the solved $0-100 range and depend on the export-credit accounting. Kept out of the main figures
   on purpose; lives in Discussion D4 (full paragraph) + Table 3 CAC + SI S5. Caption/prose must say
   "extrapolated."

---

## Decision points (yours)

1. **Abstract assertiveness.** Lead conditional (safe), lead mechanism (Nature-flagship), or **reconcile**
   -- state the conditional verdict *as* the mechanism in the "We show" sentence. *Rec: reconcile -- the
   honest number and the novel number are one sentence (credit flips below grid 25/22% only at NOAK; ~2.5x
   at mid-range).*
2. **Carbon route's main-text weight.** A main figure panel (breaks the 8-item ceiling), or **one
   Discussion paragraph (D4) + Table 3 CAC + SI S5**, or one closing sentence. *Rec: D4 + Table 3 + SI --
   demote explicitly (and say why it is fragile); do not cut to a sentence, the explicit demotion is what
   protects the capital route as the robust one.*
3. **Beat-0 placement.** Results opening (Fig 1 + Table 1 light, ~220 words), Methods only, or split.
   *Rec: Results opening -- Fig 1's real LMP/wet-bulb inset earns the "conditional" verb before any number;
   keep it the shortest beat; restate Table 1 in Methods. Do not open Results cold on Beat 1 economics.*
4. **Fig 4a build-gate (correctness, not style).** Build the gate curve as planned but **re-derive its
   numbers from `dispatch.csv.gz` x wet-bulb first**, or keep the dispatch weeks in main and move the gate
   curve to SI. *Rec: build it (the weeks show texture not mechanism), but lock the share/threshold numbers
   before drafting the caption -- it is the only main-figure link not yet exactly verified.*
