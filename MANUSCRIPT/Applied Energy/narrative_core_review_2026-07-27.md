# Narrative-core review of the Applied Energy manuscript

Date: 2026-07-27
Scope: Read-only editorial review of the current `main.tex` / compiled `main.pdf`; no manuscript source was modified.
Lens: Which findings are load-bearing, whether the current argument has a clear hierarchy, and which material can be compressed or moved to the Supplementary Information.

## Executive judgment

The paper already has a defensible and publishable central message. The problem is not a lack of results; it is insufficient hierarchy among them. The manuscript currently gives baseline economics, market years, FOAK/ATB-Mid/NOAK capital, a two-dimensional capital grid, WACC, PUE, BESS, data-center size, carbon price, emissions, water, EPBT and dispatch results nearly equal rhetorical weight. This makes a comparatively simple boundary result feel more complicated than it is.

The one-sentence thesis should be:

> For the modeled Houston data center, SMR competitiveness is controlled primarily by reactor capital, market/export value and policy—not by recovered-heat cooling: with Section 45Y and 2023 prices, parity begins near \$5,000 kW_e−1, whereas the absorption chiller dispatches rationally but remains an uneconomic incremental investment across the tested range.

Carbon pricing is a conditional second pathway, not a co-equal technology driver. PUE, BESS and size matching are modifiers or robustness checks, not headline findings.

## Four load-bearing conclusions

### 1. At the mid-range reactor-capital anchor, neither nuclear configuration is competitive with grid procurement

This is the necessary starting point. Under the 2023 ATB-Mid baseline, Cases 1 and 2 have TACs of \$113.4 and \$122.6 million yr−1 versus \$75.9 million yr−1 for Case 0, even after the Section 45Y credit; the margins are −49% and −62% (`main.tex`, lines 577–582). Reactor capital recovery dominates the cost stack (`main.tex`, line 580).

This conclusion answers the first procurement question: “Does colocation work under the stated present/mid-range assumptions?” The answer is no.

### 2. Reactor capital determines the technology-cost boundary, but the numerical threshold is market-specific

The central contribution is not the NOAK point estimate; it is the parity boundary. Under 2023 prices and the baseline policy assumptions, Case 2 straddles parity at approximately \$5,000 kW_e−1, while changing absorption-chiller capital across its full tested range moves the margin by no more than 13 percentage points (`main.tex`, lines 646–651). The reactor-capital axis moves the outcome by hundreds of percentage points (`main.tex`, lines 631–634 and 671).

The qualification is load-bearing: this is not a universal \$5,000 kW_e−1 threshold. At the NOAK anchor in the low-price 2024 year, Case 1 is approximately at parity and Case 2 remains 34% more expensive than grid supply (`main.tex`, line 632). Therefore the correct claim is “reactor capital is the dominant technology-cost lever, conditional on market/export value,” not “reactor capital alone sets viability.”

### 3. Absorption cooling is operationally responsive but investment-negative

The optimization produces a credible operational mechanism: the absorber runs in expensive-electricity hours and the VCC serves cheap hours and the refueling outage (`main.tex`, lines 597–607). It supplies 38% of annual cooling (`main.tex`, line 602), yet Case 2 costs \$9.2 million yr−1 more than Case 1 because avoided VCC electricity does not cover absorption capital, lost turbine work and forgone PTC (`main.tex`, line 611).

The PUE sweep strengthens this conclusion: from full-load PUE 1.10 to 1.50, Case 2 remains \$13.2–2.4 million yr−1 more expensive than Case 1 (`main.tex`, lines 613–618). This is the paper’s most conceptually interesting finding because it distinguishes “the optimizer uses the technology” from “the technology creates net value.”

### 4. Carbon pricing can close the mid-range gap, but only under the stated export-emissions convention

At ATB-Mid capital, Cases 1 and 2 cross the grid-only TAC at approximately \$53 and \$64 tCO2−1 (`main.tex`, lines 653–658). This is a legitimate second route to parity. It is also convention-dependent: the nuclear cases become net-negative only because merchant exports are credited at the ERCOT hourly average emissions factor (`main.tex`, lines 667–669). The model does not endogenize carbon-price pass-through into LMPs (`main.tex`, line 689).

The caveat is part of the result, not merely a limitation. The abstract/highlights/conclusion should always state “under hourly average export crediting” with these thresholds.

## Existing argument chain

The manuscript’s intended chain is sound:

1. **Motivation:** hyperscale loads are growing; SMRs offer firm low-carbon power; absorption cooling might improve colocation economics (`main.tex`, lines 260–264).
2. **Knowledge gap:** prior work does not jointly resolve hourly cooling physics, market prices, reactor capital, production credits and carbon accounting into a boundary map (`main.tex`, line 266).
3. **Test design:** compare grid, SMR-only, SMR plus absorption and NGCC using hourly co-optimization and sensitivity sweeps (`main.tex`, lines 268 and 278–310).
4. **Baseline falsification:** at ATB-Mid capital, nuclear is not at grid parity and absorption makes the nuclear case more expensive (`main.tex`, lines 580–582).
5. **Mechanism:** absorption dispatch follows the price signal, but its incremental investment value is negative (`main.tex`, lines 600–618).
6. **Boundary identification:** reactor capital is the dominant technology lever; 2023 parity appears near \$5,000 kW_e−1, conditional on market year and the PTC (`main.tex`, lines 631–651).
7. **Alternative policy pathway:** a carbon price closes the ATB-Mid gap under export crediting (`main.tex`, lines 653–669).
8. **Decision rule:** evaluate a proposal through capital, market/export value, policy and carbon-accounting assumptions; do not treat heat recovery as the source of competitiveness (`main.tex`, lines 693–698).

The chain becomes obscured mainly between steps 4 and 7, where secondary endpoints and every sensitivity axis receive standalone prose.

## Narrative inconsistencies or overclaims

### “Boundary” is sometimes treated as invariant and sometimes as market-dependent

The Discussion says secondary factors change the distance to parity “without moving the boundary” (`main.tex`, line 681), but market year and carbon price demonstrably move or cross the boundary. A more accurate formulation is:

> These factors change the location of the parity boundary without changing the hierarchy of drivers.

Likewise, the abstract says the boundary is “set instead by reactor capital” (`main.tex`, line 124). Because the 2024 result overturns Case 2 even at NOAK capital, “reactor capital is the dominant technology-cost axis” is more defensible than “reactor capital sets the boundary.”

### The abstract conflates the \$5,000 threshold and the \$2,250 NOAK outcome

The sentence “The viable region opens near \$5,000 … nth-of-a-kind capital makes them 77–89% cheaper” (`main.tex`, line 123) puts two different capital anchors in one clause. Separate the parity threshold from the NOAK endpoint, or retain only the threshold and state that the result is market-sensitive.

### The conclusion overstates the causal role of the PTC at NOAK

The Conclusion says the credit “brings both nuclear cases below grid cost” at NOAK (`main.tex`, line 696), but the Results state that both already reach parity before the credit, with pre-credit margins of +32% and +22% (`main.tex`, line 632). Suggested correction:

> At NOAK capital, both nuclear cases are below 2023 grid cost even before the credit; the credit widens that advantage.

### “Load large enough” is introduced as a necessary condition without a solved minimum-load boundary

The Conclusion lists “a load large enough to use the smallest commercial reactor” as one of the conditions that “must coincide” (`main.tex`, line 698). The size sweep shows that matching improves utilization but does not close the ATB-Mid gap (`main.tex`, line 584); it does not identify a minimum load required for parity across capital and market regimes. Replace this with a supported condition such as “adequate on-site utilization or remunerated export capability,” or solve and report an actual load-size boundary.

### Extreme percentage margins distract from the decision rule

Values such as −322% and +109% arise from the normalized grid-cost margin and are sensitive to a small grid-only denominator (`main.tex`, lines 626, 632 and 671). “109% cheaper” is not ordinary-language meaningful because it corresponds to negative net TAC. For headline prose, use capital thresholds and absolute TAC; reserve extreme percentages for figures/tables, and write “grid-cost margin of +109%” rather than “109% cheaper.”

### Incidental source issue

At `main.tex`, line 324, `Gurobi 13.0.%` starts a LaTeX comment. Consequently, the compiled manuscript drops the remainder of that source line, including the solver method, tolerance and realized-gap statement. This is not a narrative issue, but it should be corrected before submission.

## Alignment of Abstract, Highlights and Conclusion

### Overall

They support the same broad story, but the hierarchy is only partially aligned. All three contain the baseline penalty, low-capital upside, carbon-price pathway and weak role of absorption. The main problems are overloading, missing conditionality and a few causal/semantic mismatches.

### Abstract (`main.tex`, lines 122–125)

Strengths:

- States the baseline penalty.
- Gives the approximate capital threshold.
- Includes carbon thresholds with export-crediting context.
- States both the 38% cooling share and \$9.2 million yr−1 penalty.

Recommended change:

- Remove most of the 2022/2024 endpoint list.
- Clearly distinguish the \$5,000 parity threshold from the \$2,250 NOAK scenario.
- State that reactor capital is the dominant *technology-cost* driver and that market value controls transferability across years.

### Highlights (`main.tex`, lines 127–133)

The current bullets are coherent, but the first is a method statement while the crucial market-conditionality result is absent. Replace either the method bullet or the unqualified NOAK bullet with a result such as:

> The \$5,000 kW_e−1 parity threshold is specific to 2023 market conditions.

The final absorption bullet should be more concrete:

> Absorption supplies 38% of cooling but adds \$9.2 million yr−1.

### Conclusion (`main.tex`, lines 693–698)

The Conclusion repeats too many endpoint numbers and adds the unsupported “load large enough” condition. It should retain only:

1. baseline Case 2 penalty or the mid-range non-parity result;
2. the approximate \$5,000 kW_e−1 conditional threshold;
3. absorption’s negative incremental value;
4. carbon pricing as an accounting-dependent second route.

The 2022 and 2024 NOAK numbers, FOAK statement, PUE break-even detail and full procurement checklist have already been established and do not all need to reappear.

## Section-by-section compression plan

### Front matter and Introduction

| Location | Action | Reason |
|---|---|---|
| Abstract, lines 123–124 | Reduce to four results: baseline gap; conditional capital threshold; negative absorption value; conditional carbon route | Current sentence contains too many anchors and blurs \$5,000 with NOAK |
| Highlights, lines 127–133 | Replace one bullet with market dependence; make the absorption bullet quantitative | Aligns all front matter with the actual boundary argument |
| Introduction, lines 260–264 | Retain the three-part motivation but reduce demand statistics and SMR background by ~20% | The gap statement, not the number of demand projections, carries the paper |
| Introduction, line 268 | Group sensitivities into capital, market, cooling and policy rather than enumerate every axis | The full scenario ledger is methodological provenance |
| Introduction, line 270 | Retain as the thesis paragraph, but use qualitative carbon wording or fewer numbers | It currently pre-repeats the Results |
| Introduction, line 272 | Delete the roadmap paragraph | It adds no scientific content in a conventional short article |

### Methodology and main-text displays

| Location | Action | Reason |
|---|---|---|
| Figure 1 and Table 1, lines 281–310 | Retain; shorten prose that repeats case definitions already visible in the table/schematic | Essential system orientation |
| PUE discussion, lines 312–319 | Keep definition and electric-only caveat; move realized-PUE values and anchor interpretation to SI | The paragraph mixes methods, results and limitations |
| Optimization implementation, line 324 | Keep one reproducibility sentence; move solver diagnostics to SI/repository documentation | Important but not central narrative |
| Figure 2 and lines 453–460 | Move input-trace figure to SI | It validates inputs but does not carry a main conclusion |
| Tables 2–4, lines 464–533 | Keep one compact “key baseline assumptions” table; move detailed cost, lifetime and technical tables to SI | These tables substantially duplicate one another and the prose |
| Table 5, lines 540–567 | Move the 109-run ledger to SI; retain one sentence listing the major axes | Provenance rather than result |

This would reduce the main display set from six figures/five tables to approximately five figures/two tables without sacrificing reproducibility.

### Results

| Location | Action | Reason |
|---|---|---|
| Baseline, lines 580–582 | Retain and merge into one decisive baseline paragraph | Load-bearing evidence |
| Size matching, line 584 | Reduce to one sentence and leave detailed values in existing Supplementary Note 1 | Already fully documented in SI |
| Figure 3, lines 586–593 | Retain panel a; if a harder cut is needed, move the multi-year cost–carbon scatter and component accounting to SI | Panel a establishes baseline; panels b/c partly overlap later market/carbon sections |
| Secondary endpoints, line 595 | Delete from main Results or reduce to one sentence | NLCS, EPBT and water do not change ranking and already have SI tables |
| Cooling dispatch, lines 600–602 | Keep price-response mechanism and annual 38% share; remove weekly means, 26 MW detail and extraction-sweep endpoints from prose | Figure/caption and SI already contain these details |
| Waterfall, line 611 | State avoided electricity, combined offsets and net \$9.2 million result; move the six-component list to SI table | The mechanism matters more than every component value |
| PUE subsection, lines 613–618 | Merge into the cooling subsection as two sentences | It is robustness evidence for the absorption conclusion, not a separate pillar |
| Market year, lines 623–626 | Retain one high-price/low-price contrast and the 2024 NOAK counterexample; move full case-year numbers to SI | Market dependence is load-bearing, but every annual mean and margin is not |
| Battery, lines 628–629 | Move entirely to SI and mention only in Figure 6b/global ranking | It changes no ranking and shifts margin by one point |
| Reactor capital, lines 631–634 | Retain the threshold, PTC role and one market-transfer caveat; remove the complete FOAK/Mid/NOAK × year list | Central section is currently buried under endpoint reporting |
| WACC, lines 636–637 | Compress to one sentence or move detailed endpoints to SI | Useful procurement modifier, not the primary boundary |
| Joint frontier, lines 646–651 | Retain, but collapse three paragraphs to one focused paragraph | This is the central boundary result |
| Carbon, lines 656–669 | Retain \$53/\$64 crossings and export-credit caveat; remove the four footprint values and NGCC \$165 extrapolation from the main story | The NGCC extrapolation is not load-bearing and complicates Figure 6a |
| Global ranking, line 671 | Retain the qualitative rank and absolute-cost warning; leave all percentage spans in the panel labels/source table | This paragraph should synthesize rather than repeat the whole atlas |

Suggested Results architecture:

1. **Baseline economics: mid-range nuclear is not at parity**
2. **Absorption cooling: rational dispatch, negative incremental value**
3. **Competitiveness boundary: reactor capital, market value and financing**
4. **Conditional policy pathway: carbon pricing under export crediting**

This removes the standalone PUE and BESS detours while preserving their evidence in SI.

### Discussion and Conclusion

Do not merge them solely to save space. The current Discussion is approximately 844 source words and the Conclusion approximately 327; a one-page Discussion is not intrinsically excessive. The issue is repetition.

Recommended structure:

- **Discussion paragraph 1 (~180 words):** interpret why fixed capital plus market/export value dominates and why the \$5,000 threshold is conditional.
- **Discussion paragraph 2 (~150 words):** explain the “dispatch value is not investment value” insight for absorption cooling and its relevance to prior cogeneration claims.
- **Discussion paragraph 3 (~220 words):** retain only limitations that can materially move the boundary: export-emissions factor, carbon-price pass-through, market/load/climate transferability, outage/reliability treatment and PTC levelization.
- **Conclusion (~150–180 words):** one decision rule and three findings; no complete replay of all years and scenarios.

Specific cuts:

- Lines 679–681 repeat the Results almost verbatim. Keep interpretation; remove the row-by-row result recap.
- Line 685 repeats the dispatch and cost decomposition. Keep the conceptual distinction between operational use and net investment value.
- Lines 689–691 contain important limitations, but the alternate levelization re-solve values (12.1/11.8 points, \$4,800, \$66/\$76) should move to SI. Retain the direction and statement that conclusions do not change.
- Lines 696–698 should lose the FOAK, full multi-year NOAK list and unquantified minimum-load condition.

An achievable target is a 20–25% reduction in main-text prose (roughly 1,500–2,000 words), mainly by moving already-documented sensitivity detail to SI. This would sharpen the argument without reducing evidentiary coverage.

## Missing direct answer: when does Case 2 beat Case 1 as absorption CAPEX falls?

The current manuscript does **not** directly present this decision threshold.

- Figure 4c gives the baseline Case 2−Case 1 value decomposition (`main.tex`, lines 604–611).
- The PUE sweep shows that Case 2 remains more expensive over PUE 1.10–1.50 (`main.tex`, lines 613–618).
- The joint capital-cost frontier in Figure 5d varies absorption CAPEX, but its outcome is Case 2 versus Case 0/grid, not Case 2 versus Case 1 (`main.tex`, lines 646–651).

This missing result matters because it closes the investment question raised by the cooling contribution: the present manuscript proves that absorption is not the *grid-viability driver*, but it does not state how cheap the absorber must become to create positive incremental value relative to reactor-only cooling.

For the fixed 160 MW_c installed design, no additional hourly optimization appears necessary to calculate the baseline threshold, because absorption CAPEX enters TAC as a dispatch-neutral fixed term. Using the current values:

- baseline absorption CAPEX = \$750 kW_c−1;
- Case 2−Case 1 penalty = \$9.22 million yr−1;
- 25-year CRF at 6.7% = 0.08350;
- installed capacity = 160,000 kW_c.

The implied break-even CAPEX is approximately:

> \$750 − \$9.22 million / (0.08350 × 160,000 kW_c) ≈ \$60 kW_c−1.

This is far below the tested \$450–1,200 kW_c−1 range. It could be reported as a derived baseline threshold with a clear assumption that fixed O&M and dispatch remain unchanged. New solves are needed only if chiller size/installation becomes endogenous, fixed O&M changes with CAPEX, or the authors want a multi-dimensional threshold across PUE, extraction penalty, market year or PTC treatment.

The cleanest presentation would be a small Case 2−Case 1 break-even line or inset, not another large scenario atlas:

- x-axis: absorption CAPEX;
- y-axis: ΔTAC = TAC(Case 2) − TAC(Case 1);
- horizontal zero line;
- shaded observed cost range \$450–1,200 kW_c−1;
- one labeled break-even near \$60 kW_c−1.

This directly supports the manuscript’s heat-recovery conclusion with fewer numbers than the current PUE and component-detail prose.
