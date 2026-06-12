# Nature Energy Manuscript — Full-Document Consistency Audit — 2026-06-11

Scope: every change from both revision rounds on `audit-45y-fuel-revision` (16-decision model correction + manuscript rebuild, then audit passes A/C/D and the Fig. 5 solved-range fix), audited for (1) numeric consistency between prose, tables and figures, (2) logic and structure, (3) language and content.
Method: 8 parallel dimension reviewers (results-vs-outputs, si-tables, figures-vs-text, cross-section, methods-vs-code, logic-structure, language, new-edit seams) + 1 adversarial verifier per candidate finding; ground truth = outputs/master_kpi_table.csv (100 runs), value_decomp_case2.csv, willans_sweep_case2.csv, case2 dispatch.csv.gz, raw ERCOT/weather/gas data, and the src/ + config/ tree. 83 agents this run (plus cached prior passes).
Candidates: 75. Confirmed: 72 (6 cross-dimension duplicates merged below -> 66 unique). Refuted: 3. Plus 3 findings adjudicated manually in the main loop (2 confirmed, 1 refuted) -> 67 unique confirmed findings.

Severity: critical = flagship artifact contradicts the modeled policy; major = load-bearing claim or figure broken; minor = real defect, limited blast radius; nit = polish.

## Axis verdicts

1. **Numeric consistency — PASS, zero mismatches.** Every quantitative claim in the abstract, Results, Discussion, figure captions and all 9 SI tables was recomputed from the output ledgers and raw input data (TACs, margins, PTC, energy balances, absorption shares, waterfall components, crossovers, all sweep endpoints, dispatch-level claims, LMP/gas/wet-bulb statistics, scenario ledger 100-run count). No prose/table/figure number disagrees with ground truth. The only number-adjacent defects are presentation-level: one rounding-style mismatch (-69 vs -70), one misrounded table bound (351 vs 350), one mislabeled ATB edition year, one overstated sweep span, and the PUE-sweep margin-denominator definition (below).
2. **Logic & structure — one major contradiction, the rest minor.** The concluding paragraph's "carbon price *or* concessional financing" disjunction contradicts the solved WACC result stated twice earlier (financing alone never crosses parity). The new solver-disclosure sentence overclaims ("all problems... every run") against the closed-form Cases 0/3 described two sentences earlier. The closed-form justification ("absence of storage and heat recovery") is falsified by Case 1. Remaining items: acronym hygiene, SI float ordering, repeated statements, dangling "now" comparatives.
3. **Language & content — no systemic problems; copy-edit list below.** Two stale-artwork defects in Figure 1 (45U PTC label — critical; S3/Backup labels), one broken figure panel (Fig. 3c waterfall clipping), and ~50 minor/nit copy-edit items (spelling-variant mixes, hyphenation, spacing, caption-expansion gaps).

## CRITICAL (1)

### 1. Figure 1 system schematic still labels the PTC boundary input as '45U PTC' (stale Section 45U remnant)

- **Dimension:** cross-section + figures-vs-text | **Location:** `MANUSCRIPT/Nature Energy/figures/fig1_system_schematic.svg (SVG lines 214 and 216: text elements '45U' and '45U PTC'); same text present in fig1_system_schematic.pdf (the file included by main.tex line 102, Figure 1) and fig1_system_schematic.png. Visually confirmed in the 'Boundary inputs' strip (document icon labeled '45U' captioned '45U PTC', next to 'Wet-bulb' and 'CAPEX / O&M').`

**Manuscript says:** Figure 1 (the organizing system schematic, referenced at main.tex line 102/109) shows the policy boundary input to the model as a document icon labeled '45U' with caption '45U PTC'.

**Evidence:** The model and the entire manuscript text apply the Section 45Y clean-electricity PTC ($30/MWh CY2025 prevailing-wage, levelized to $19.7/MWh; main.tex lines 71, 86, 107, 114, 134, 139, 347-357, 521, 561). Per the project's 2026-06-09 revision, 45U was deleted everywhere; the only sanctioned 45U mention is the Methods eligibility contrast at line 347. Figure 1 was not regenerated on this branch (git status shows fig1_system_schematic.* unmodified; last touched in commit 5e25332).

**Why it matters:** This is exactly the '45U as current policy' stale remnant the audit targets: the flagship schematic tells readers the modeled credit is the legacy Section 45U PTC, contradicting the abstract, Results, Methods, the PTC equation block and the nomenclature table, all of which state Section 45Y. 45U and 45Y have different eligibility and values, so the figure misrepresents the modeled policy.

## MAJOR (2)

### 2. Operation-value waterfall (Fig. 3c) clips the Residual and Net bars below the y-axis floor; bottom value labels collide with tick labels

- **Dimension:** figures-vs-text | **Location:** `MANUSCRIPT/Nature Energy/figures/fig_operation_value.{svg,pdf,png} panel c; caption at main.tex line 139`

**Manuscript says:** Caption: "the residual bar reconciles the component sum with the measured $9.2 M yr^-1 difference"; the figure is supposed to show bars for Residual (-1.4) and Net vs Case 1 (-9.2).

**Evidence:** SVG geometry: axes bottom = y 478.58 px = data value -7.8 M$/yr, but the data minimum is -9.22 (value_decomp_case2.csv residual -1.42, net -9.22). The Residual bar (y 478.58-486.11, i.e. -7.8 to -9.2) lies entirely below the axis frame, the Net bar (down to y 486.11) spills past the axis floor un-clipped into the tick-label band, and the value labels -3.1 (y 481.6), -1.4 (484.4), -1.1 (487.3) and -9.2 (494.8) all sit below the axes bottom, overlapping the "VCC backup/PTC forgone/Residual/Net vs Case 1" tick labels (visible in the PNG, where the Net bar covers "Net vs Case 1" and "-9.2" is unreadable).

**Why it matters:** The y-limit (~-7.8) is tighter than the data range, so the two bars the caption explicitly highlights (residual reconciliation and the measured -9.2 endpoint) are cut off or drawn outside the plot area; the panel cannot show what the caption claims and the overprinted labels are illegible.

### 3. Concluding paragraph claims concessional financing alone reaches parity, contradicting the solved WACC result stated twice earlier

- **Dimension:** logic-structure | **Location:** `Line 202 (Discussion, final paragraph) vs lines 158 and 194`

**Manuscript says:** Line 202: "the mid-range case needs a carbon price of \$53--64~tCO$_2^{-1}$ or concessional financing to reach parity" — the disjunction implies concessional financing by itself is sufficient to reach grid parity.

**Evidence:** Line 158 (Results): "Financing therefore brings the mid-range case within reach of parity at concessional rates but cannot cross it alone" (margin -24% at the 5% WACC floor of the solved G7 sweep). Line 194 (Discussion): "at a 5% WACC the mid-range Case~2 comes within 24% of grid supply, but the sweep does not cross parity on its own."

**Why it matters:** Direct internal contradiction: the paper's own solved results show financing alone never crosses parity within the swept range, yet the final takeaway sentence presents it as an alternative sufficient route to parity. This is the concluding policy claim of the paper, so the contradiction is load-bearing.

## MINOR (30)

### 4. PUE-sweep margins divide by the fixed PUE-1.35 Case 0, but the margin definition promises a "matching" grid-only baseline

- **Dimension:** main-loop adjudication | **Location:** `main.tex:107` (margin definition) vs `main.tex:145` (G2 PUE sweep) and outputs/master_kpi_table.csv s1_pue rows

Line 107 defines the cost margin against "the matching grid-only data-center cost", but all six s1_pue rows carry tac_case0_baseline_usd_per_yr = 75.869M — the PUE-1.35 Case 0. No PUE-matched Case 0 exists in the ledger, so the printed sweep margins mix a varying nuclear PUE with a fixed grid baseline. Either compute a matching Case 0 per PUE leg or reword the definition/sweep text to say margins are quoted against the fixed PUE-1.35 baseline (the latter is a one-sentence fix and arguably the intended comparison: same IT load, conventional facility).

### 5. Inputs-overview panel b x-axis label renders literally as "Duration of year (\%)"

- **Dimension:** figures-vs-text + cross-section | **Location:** `MANUSCRIPT/Nature Energy/figures/fig_inputs_overview.{svg,pdf,png} panel b x-axis label (figure included at main.tex line 611)`

Visible typographic artifact in a submission figure; the label should read "Duration of year (%)".

### 6. Caption for inputs-overview (b) refers to "the regime labels" but the panel contains no regime labels

- **Dimension:** figures-vs-text | **Location:** `main.tex line 612, caption sentence for panel (b), vs fig_inputs_overview panel b`

The caption describes and disclaims labels that do not exist in the figure it accompanies; the sentence either points to a stale figure version or should be rephrased to refer to the year labels/prose.

### 7. Caption for inputs-overview (d) mis-describes the dashed COP segment as de-rating "below" the crystallization gate

- **Dimension:** figures-vs-text | **Location:** `main.tex line 612, caption sentence for panel (d), vs fig_inputs_overview panel d`

The caption inverts the figure's encoding: the visible dashed segment is the ungated extrapolation at/above the gate, not the de-rating below it; as written it contradicts the legend ("without gate") and the model description at lines 371-372.

### 8. Inputs-overview panel d "VCC backup" shaded band starts at 27 °C, not at the 29 °C crystallization gate

- **Dimension:** figures-vs-text | **Location:** `fig_inputs_overview panel d shaded band (SVG patch_26), vs caption main.tex line 612 and Methods Eq. abs_avail (lines 273-278)`

The band's left edge (27 °C) does not match the 29 °C gate that defines the backup region in the model, in panel a, and in the same panel's own curve cutoff; it overstates the backup region by 2 °C.

### 9. Figure 1 schematic BESS block labeled with stale scenario name "Optional / S3 sensitivity"

- **Dimension:** figures-vs-text | **Location:** `MANUSCRIPT/Nature Energy/figures/fig1_system_schematic.pdf, BESS annotation (pdftotext: "Optional / S3 sensitivity")`

A leftover label from an earlier scenario-naming scheme points readers to a scenario group that does not exist in this manuscript; it should say G3 (or just "sensitivity" as in Table 1).

### 10. Solver disclosure overstates: 30 of 100 ledger runs are closed-form, not Pyomo/Gurobi solves

- **Dimension:** methods-vs-code + new-seams | **Location:** `main.tex line 243 (Methods, Optimization formulation)`

The sentence claims all problems are formulated in Pyomo and that every run in the 100-run ledger solves to the 1e-4 tolerance, which is internally inconsistent with the same paragraph's (correct) statement that Cases 0 and 3 reduce to closed-form annual cost evaluations, and is factually wrong for 30 of the 100 runs. A reproducibility reviewer running the code would find no Gurobi log or gap for those runs. Restricting the sentence to the Case …

### 11. Methods justification for closed-form Cases 0/3 is contradicted by Case 1

- **Dimension:** logic-structure | **Location:** `Line 243 (Methods, Optimization formulation, first paragraph)`

The stated sufficient condition ('no storage and no heat recovery implies hourly independence') is falsified by the paper's own Case 1, whose hourly decisions are coupled by reactor ramping and grid trade. The actual distinguishing features (dispatchable reactor, bidirectional grid exchange) are not the ones cited, so the methods logic as written is internally inconsistent.

### 12. Acronym 'IT' used before its first-use definition; 'LiBr' never expanded at first main-text use

- **Dimension:** logic-structure | **Location:** `Line 92 (Introduction, final paragraph) vs line 118; line 134 vs line 88`

Violates define-at-first-use: a reader hits 'IT-load' in the Introduction and 'LiBr' in Results before either is defined in body text (captions do not substitute for first-use definition in running text).

### 13. Acronyms 'OPG' and 'CHP' are never expanded anywhere in the document

- **Dimension:** logic-structure | **Location:** `OPG: Figure 4 caption (line 163) and Supplementary Table S2 body (line 549). CHP: Supplementary Table S2 body (line 553)`

Both abbreviations appear only in their short forms in a caption/table whose captions otherwise diligently re-expand every acronym, so these are unambiguous omissions under the manuscript's own convention and Nature's caption-self-containment rule.

### 14. 'PCC' never defined at first use in body text and missing from both G8 caption definition lists

- **Dimension:** logic-structure | **Location:** `Lines 291-297 (Methods grid block), line 380 (Methods scenario design), Supplementary Fig. S3 caption (line 723), Supplementary Table S8 caption (line 729)`

First bare use in running text (line 380) is undefined for a reader of the main text, and the two G8 captions violate the per-caption re-expansion convention applied everywhere else in the manuscript.

### 15. Caption re-expansion gaps: several captions use acronyms absent from their own definition lists

- **Dimension:** logic-structure | **Location:** `Fig. 5 caption (line 179); Supplementary Table S5 caption (line 644); Supplementary Table S6 caption (line 663); Supplementary Table S3 caption (line 568) vs body lines 596-597; Supplementary Table S7 caption (line 695); Supplementary Table S8 caption (line 729)`

Per the Nature-portfolio convention the manuscript itself follows, every display item must be self-contained; these six captions are the inconsistent exceptions and would draw editorial queries.

### 16. Supplementary figures and tables are not numbered in order of first citation in the article

- **Dimension:** logic-structure | **Location:** `Main-text citations at lines 109, 118, 129, 145, 278, 324, 369 vs SI float order (lines 416-780)`

Nature requires supplementary items to be numbered in the order they are first cited in the article. The current numbering forces readers to jump from 'Supplementary Figure S3' (first SI figure they meet) backwards, and the very first supplementary table a reader encounters is S9.

### 17. Dangling 'now' comparatives reference a prior state never established in the paper (revision artifacts)

- **Dimension:** logic-structure + language | **Location:** `Line 174 (Results, carbon section), line 194 (Discussion), line 196 (Discussion); arguably also line 167`

Orphaned comparative claims: a fresh reader cannot resolve what 'now' contrasts with, and a referee may read these as unintended traces of an internal revision history. Line 167 is the most defensible (could contrast the 1-D G4 sweep) but the other three have no in-paper referent.

### 18. US/UK spelling mix: 'modelled' vs 'modeled'

- **Dimension:** language | **Location:** `main.tex line 200 (Discussion, limitations paragraph)`

Single UK spelling 'modelled' in an otherwise US-spelled manuscript; Nature copy desks require one variety consistently.

### 19. \checkmark gobbles following space in Table 1 caption

- **Dimension:** language | **Location:** `main.tex line 216 (Table tab:cases caption)`

LaTeX-level text bug visible in the compiled PDF; needs \checkmark{} or \checkmark\ before 'denotes'.

### 20. Three different equation-reference styles

- **Dimension:** language | **Location:** `main.tex lines 134, 307, 312, 371, 373, 380, 681`

Inconsistent cross-reference formatting ('Equation 6' vs 'Equation (6)' vs 'Eq. (1)') within one document; pick one convention.

### 21. Misattached relative clause: gate given the wet-bulb's 'annual peak'

- **Dimension:** language | **Location:** `main.tex line 371 (Methods, Data inputs)`

The relative pronoun has the wrong antecedent, producing a literally false statement ('the gate's annual peak is 28 °C'); needs rewording, e.g. '...gate; the annual wet-bulb peak is 28 °C'.

### 22. Ambiguous 'which' clause in Willans-line sentence

- **Dimension:** language | **Location:** `main.tex line 254 (Methods, Rankine steam cycle paragraph)`

Garbled relative clause: as parsed, the sentence says constant efficiency overstates the droop. Should read something like '...explicit; a constant-efficiency model overstates output at minimum load by ~8%'.

### 23. Missing comma before appositive after the alpha_w value

- **Dimension:** language | **Location:** `main.tex line 254 (Methods, sentence introducing Eq. 4-5)`

Broken parallelism plus a missing comma; needs '...and $\alpha_w=0.20...$, the marginal electricity loss intensity...,' or reorder to match the first two items.

### 24. Dangling participles: 'Holding capital..., the policy axis / the nuclear cases ...'

- **Dimension:** language | **Location:** `main.tex lines 172 and 196`

Dangling modifiers; copy editors will flag. 'With capital held at the ATB-Mid baseline, ...' fixes both.

### 25. Absorption unit nameplate labeled MW_th but cooling capacity convention is MW_c

- **Dimension:** language | **Location:** `main.tex line 212 (Methods, System configurations) and line 596 (Supplementary Table tab:equipment)`

The subscript 'th' on the 160 nameplate contradicts both the MW_c convention and the 145 MW_th steam-side limit stated in the same table cell; confusing unit inconsistency (should be 160 MW_c nominal).

### 26. ERCOT price node named inconsistently: 'Houston Hub' vs 'Houston load zone' vs 'Houston-zone'

- **Dimension:** language | **Location:** `main.tex line 544 (Supplementary Table tab:data) vs line 617 (Supplementary Note 4) vs line 624 (Table tab:market_years caption)`

Confusing terminology inconsistency about which settlement point the price series is, plus a one-off 'yearly mean' wording; readers checking reproducibility will not know which node was used.

### 27. Serial (Oxford) comma used inconsistently, including within single sentences

- **Dimension:** language | **Location:** `main.tex lines 86, 92, 158, 163, 167 (examples)`

Punctuation style flips sentence to sentence and even within sentences; Nature house style omits the serial comma except to avoid ambiguity, so the usage should be normalized.

### 28. 'derate(d)' vs 'de-rating' hyphenation mix

- **Dimension:** language | **Location:** `main.tex lines 88, 134, 139, 212, 262, 273, 278, 286, 473, 596, 612`

Inconsistent hyphenation of a key technical term; standardize on one form (the unhyphenated 'derate/derating' is the more common engineering usage).

### 29. Hard-to-parse clause: 'as the wet-bulb derate toward the 1.10 design COP tightens the steam budget'

- **Dimension:** language | **Location:** `main.tex line 134 (Results, cooling dispatch paragraph)`

Genuinely ambiguous sentence at the first definition of COP; e.g. 'retreating only when the wet-bulb COP derate (toward the 1.10 design value) tightens the steam budget' would fix it.

### 30. 'a peak hour of 142.4 MW_e' mixes time and power

- **Dimension:** language | **Location:** `main.tex line 233 (Methods, data-center load paragraph)`

Category error in the noun phrase; should be 'a peak hourly load of 142.4 MW_e'.

### 31. Confusing modifier: '270 MW_e net at the assumed capacity factor'

- **Dimension:** language | **Location:** `main.tex line 118 (Results, unit-size paragraph)`

The phrase 'at the assumed capacity factor' attaches to the rating and invites the wrong (CF-adjusted) reading of the 2.9x figure; it should be deleted or moved.

### 32. Reactor lifecycle-emissions unit written as both 'g CO2-eq' and 'g CO2'

- **Dimension:** language | **Location:** `main.tex line 552 (Table tab:data) vs lines 462, 503 (Table tab:nomen) and 594 (Table tab:equipment)`

Unit-label inconsistency for one parameter across the SI tables; lifecycle factors are CO2-equivalent and should be labeled uniformly.

### 33. SI Note 4 names the DOE CHP fact sheet but omits the \citep{doe2017chpAbsorption} citation that the parallel Table S2 row carries

- **Dimension:** new-seams | **Location:** `main.tex line 617 (Supplementary Note 4, rewritten attribution sentence, final clause)`

Inconsistent citation seam created by this editing round: the bib entry was added and wired into Table S2 but the matching Note 4 clause — the only uncited named source in the paragraph — was left bare. A reader following the Data Availability pointer to Note 4 finds the fact sheet unreferenced (and BESS/VCC cost provenance absent entirely). Add \citep{doe2017chpAbsorption} to the Note 4 clause (and optionally one clause covering BESS/VCC cost …

## NIT (34)

### 34. ATB edition labeled 2023 in baseline-results opening sentence but the ATB-Mid anchor is the NLR ATB 2024 Moderate value

- **Dimension:** results-vs-outputs | **Location:** `main.tex line 114 (Results, 'Mid-range reactor capital keeps nuclear options above grid supply'), vs. Figure 3 caption (line 163) and Methods (lines 373, 549)`

Internal inconsistency in the ATB edition year: a reader tracing the $7,615/kWe anchor to the 2023 ATB edition would not find it (the value is the ATB 2024 Moderate value cited elsewhere in the same manuscript). Rewording to attach '2023' to the market year (e.g. 'At the NLR ATB 2024 mid-range reactor-capital baseline under 2023 market conditions') removes the ambiguity. All numbers in the sentence itself are correct.

### 35. Carbon-intensity upper bound in input-data table misrounded (351 vs 350)

- **Dimension:** si-tables | **Location:** `main.tex line 545, Supplementary Table tab:data, row 'ERCOT average carbon intensity, ERCOT system'`

The printed upper bound 351 is 0.53 units of the last printed digit away from the exact value 350.47, just outside the half-unit rounding tolerance; the range should read 320--350. No downstream number depends on it (the model consumes the hourly trace directly), so severity is nit.

### 36. Inputs-overview panel c legend renders literal double hyphens: "Winter (Jan 15--22)"

- **Dimension:** figures-vs-text | **Location:** `fig_inputs_overview panel c legend entries`

Typographic artifact in figure text; inconsistent with the rest of the figure set and will print as a double hyphen in the published figure.

### 37. Prose quotes the ATB-Mid row of the capital-cost frontier as "-56 to -69%" while the figure cell and ground truth give -70%

- **Dimension:** figures-vs-text + cross-section | **Location:** `main.tex line 167 vs fig_sensitivity_boundary_atlas panel d, ATB-Mid x $1,200/kWc cell`

The prose endpoint (-69) disagrees with the printed cell value (-70) in the figure it describes, and -69.51 rounds to -70 under the rounding convention used everywhere else; the text should read "-56 to -70%" (or quote the span only).

### 38. Figure 1 schematic labels the VCC "(Backup)" while caption, Table 1 and Methods define it as shared-dispatch

- **Dimension:** figures-vs-text | **Location:** `fig1_system_schematic.pdf/.svg block "Vapor-Compression Chiller (Backup)" and legend entry "Backup role / resilience", vs main.tex lines 103 (caption), 212 (Methods) and Table tab:cases line 226`

The schematic's "(Backup)" framing contradicts the shared-dispatch description the caption and Methods deliberately adopt, re-introducing the primary/emergency split the text explicitly disclaims.

### 39. Main text says Case 2 excess cost falls 'from $56 to $26/MWh_IT across the sweep', but the G8 sweep starts at 0.5x where the excess is $102

- **Dimension:** cross-section + logic-structure | **Location:** `main.tex line 118 (Results, baseline section) vs Supplementary Table (tab:size_matching, main.tex lines 742-743) and Supplementary Note 8 (line 718).`

Cross-section imprecision: the main text attributes the 56-to-26 range to 'the sweep' (defined everywhere else as 0.5x-3.0x), while the SI table shows $102 at the sweep's 0.5x endpoint; a careful reader comparing main text to Supplementary Table S8 sees a contradiction. Fix is to say 'between the baseline and 3.0x' as in SI Note 8.

### 40. Outage-length formula printed as ceiling but implemented as round

- **Dimension:** methods-vs-code | **Location:** `main.tex line 252 (Methods, Reactor and turbine block) vs src/milp/builder.py lines 51-56`

The Methods documents a formula that is not the one implemented; the agreement at the single CF used is coincidental rounding. "Exactly 0.92" is also a slight overstatement (0.91998). Harmless to all reported results but technically inaccurate documentation.

### 41. Outage start "15 March" is 14 March in the 2024 leap-year runs

- **Dimension:** methods-vs-code | **Location:** `main.tex line 252 (Methods) and line 468 (Supplementary Table S1 nomenclature, "701 h from 15 March") vs src/milp/builder.py line 48`

For the 2024 market-year runs (G2, G6 control rows) the scheduled outage actually starts 14 March and the outage window covers one day earlier in the price/weather record than the manuscript states. Negligible economic effect, but the unconditional "15 March" claim does not hold for one of the three modeled years.

### 42. SI data table wet-bulb range covers only the 2023 baseline year, unlike its multi-year sibling rows

- **Dimension:** methods-vs-code | **Location:** `main.tex line 547 (Supplementary Table S2, tab:data, row "Houston wet-bulb temperature")`

Read alongside the explicitly multi-year rows in the same table, the −0.5 °C lower bound is wrong by ~10 K for two of the three modeled years. Adding "(2023)" to the row (consistent with Supplementary Fig. S1a's caption, which does state year 2023) would remove the ambiguity. No model result is affected because the cold-end relief is capped at 1.182 below ~12.7 °C wet-bulb.

### 43. PCC size-matching sizing rule stated twice nearly verbatim within Methods

- **Dimension:** logic-structure | **Location:** `Line 297 (Methods, grid block) and line 380 (Methods, scenario design); also repeated in SI Note 8 (line 718) and both G8 captions (lines 723, 729)`

Within-section redundancy characteristic of incremental edits; one of the two Methods statements (and the justification in at least one caption) is superfluous.

### 44. Crystallization-gate non-binding fact (29 °C gate vs 28 °C peak) stated twice within Methods and six times overall

- **Dimension:** logic-structure | **Location:** `Line 278 (Methods, absorption submodel) and line 371 (Methods, data inputs); also line 134 (Results), Fig. 3 caption (line 139), Fig. S1 caption (line 612), SI Note 6 (line 681)`

Redundancy: stating the same caveat with the same numbers twice within Methods (plus Results, two captions and an SI note) reads as duplicated drafting rather than deliberate emphasis.

### 45. Supplementary Tables S5 and S6 sit inside SI Note 5 with no introducing prose and an unrelated topic

- **Dimension:** logic-structure | **Location:** `Lines 642-678 (between Supplementary Note 5, line 619, and Note 6, line 680)`

Structural orphan within the SI: the secondary-KPI tables are topically unrelated to the note they are embedded in, breaking the otherwise consistent note-introduces-float structure.

### 46. Scenario-group label 'G6' used in Results and Discussion without any main-text gloss

- **Dimension:** logic-structure | **Location:** `Lines 183 and 196 vs Supplementary Table S9 (line 769)`

Inconsistent labeling: a main-text reader cannot resolve 'G6' without opening the SI ledger, while the parallel group labels used in the main text are all glossed at first use.

### 47. Panel-label spacing inconsistent across figure captions: '(a)~' vs '(a) '

- **Dimension:** language | **Location:** `main.tex captions at lines 123, 139, 612 vs 163, 179, 689, 723`

Inconsistent typographic treatment of panel labels; harmless but a copy-edit catch (a line break after '(a)' is possible in the plain-space captions).

### 48. Nomenclature BWRX-300 entry: 'GE--Hitachi' en-dash vs 'GE-Hitachi' hyphen elsewhere, 'Boiling Water' capitalization, missing ties

- **Dimension:** language | **Location:** `main.tex line 509 (Table tab:nomen) vs lines 163, 373, 549, 617`

Three small inconsistencies in one cell: company-name dash style differs from the rest of the text, number-unit ties are missing, and 'boiling-water' should be lowercase (and hyphenated as a compound modifier).

### 49. Thin space 'PUE\,1.10' vs word space 'PUE 1.35' for identical constructions

- **Dimension:** language | **Location:** `main.tex lines 145 and 684 vs lines 145 (end), 198, 378, 762`

Inconsistent spacing convention for the same token pair; normalize to one form.

### 50. 'Case 2'/'Cases 1, 2' without non-breaking space in SI table cells

- **Dimension:** language | **Location:** `main.tex lines 578-600 (Table tab:equipment) and line 468 (Table tab:nomen)`

Missing ~ in narrow wrapped table columns can break 'Case / 2' or '701 / h' across lines; inconsistent with the manuscript's own convention.

### 51. 'net-exports' as a hyphenated verb

- **Dimension:** language | **Location:** `main.tex line 118 (Results)`

Awkward coinage; 'exports a net 1.14 TWh yr^-1' or 'has net exports of about 1.14 TWh yr^-1' is standard.

### 52. Scenario labels lowercased in Discussion: 'bare-low'/'turnkey-high' vs 'Bare-Low'/'Turnkey-High'

- **Dimension:** language | **Location:** `main.tex line 192 vs lines 167, 373, 553`

Inconsistent capitalization of defined proper scenario labels within one paragraph that keeps 'Low-Mid' capitalized.

### 53. 'i.e.' without following comma

- **Dimension:** language | **Location:** `main.tex line 337 (Methods, fuel-price paragraph)`

Minor punctuation inconsistency with the manuscript's US style.

### 54. En-dash inside Federal Register document number

- **Dimension:** language | **Location:** `main.tex line 561 (Table tab:data, PTC row, Source column)`

The identifier renders as a numeric range '2025-16249' in range style; should be a plain hyphen (2025-16249) to avoid misreading.

### 55. Unit dropped mid-sentence: '-$12.4 M' without yr^-1

- **Dimension:** language | **Location:** `main.tex line 684 (Supplementary Note 7)`

Inconsistent unit formatting within one parenthetical, and the 'insensitive' claim sits awkwardly against its own 2024 outlier (consider 'relatively insensitive' or naming 2024 as the exception).

### 56. Repetition: 'break-even lies just beyond PUE 1.50, where ... would already sit essentially at the break-even point'

- **Dimension:** language | **Location:** `main.tex line 145 (Results, cooling-efficiency sweep)`

Redundant wording in a key sentence; 'where a pre-credit accounting would already be essentially at parity' avoids the echo.

### 57. Hyphenation of 'direct(-)site-water increment' inconsistent

- **Dimension:** language | **Location:** `main.tex line 143 vs lines 695 and 711`

Inconsistent compound hyphenation for the same term across main text and SI.

### 58. 'ERCOT' used in abstract without expansion

- **Dimension:** language | **Location:** `main.tex line 71 (abstract)`

Nature-portfolio abstracts are self-contained; an unexplained regional-market acronym in the abstract is a standard copy-edit catch (spell out or gloss, e.g. 'in the Texas (ERCOT) market').

### 59. Missing hyphen in '200 MW_e rated hyperscale data center'

- **Dimension:** language | **Location:** `main.tex line 210 (Methods, System configurations)`

Needs '200 MW_e-rated' or rewording ('a single hyperscale data center rated at 200 MW_e').

### 60. Nomenclature expansion of IT includes 'load'

- **Dimension:** language | **Location:** `main.tex line 516 (Table tab:nomen, Abbreviations)`

Expanding IT as 'information-technology load' makes phrases like 'net levelized cost of IT supply' expand nonsensically; drop 'load' from the gloss.

### 61. Broken parallelism: 'from a deep merchant-export surplus ... to a net importer'

- **Dimension:** language | **Location:** `main.tex line 718 (Supplementary Note 8)`

Non-parallel series; 'to a net import position' (or 'net-import deficit') restores parallelism.

### 62. Missing 'at' in comparison: 'more efficiently than its full-load design point'

- **Dimension:** language | **Location:** `main.tex line 238 (Methods, PUE paragraph)`

Elliptical comparison needs 'than at its full-load design point'.

### 63. Duplicated CRF-amortization statement within the Objective subsection

- **Dimension:** language | **Location:** `main.tex lines 324 and 344 (Methods, Objective)`

Verbatim-level repetition within one subsection; fold the formula into the first statement or trim the second.

### 64. Redundant horizon phrase duplicates the paragraph's opening sentence

- **Dimension:** new-seams | **Location:** `main.tex line 243 (Methods, Optimization formulation paragraph)`

Insertion seam: the new solver sentence restates the horizon that the paragraph opened with, so the paragraph names the 8760-hour horizon twice within four sentences. Reads as a bolted-on disclosure rather than one-sitting prose; dropping "over the full 8760-hour horizon" from the new sentence loses nothing.

### 65. Nominal-WACC sentence pre-empts and partially duplicates the WACC-sweep sentence that immediately follows

- **Dimension:** new-seams | **Location:** `main.tex line 344 (Methods, Objective paragraph, end)`

Seam artifact of the insertion: a definite reference ("the WACC sweep") precedes its in-section introduction, and the sweep is effectively introduced twice in consecutive sentences. Swapping the order or merging ("...and the 5% leg of the WACC sweep in Section ref, which sweeps i over {5, 6.7, 10}%, bounds the size of the effect") would read as written in one sitting. No numerical issue.

### 66. Table S2 source column cites NLR ATB inconsistently across rows after the edit

- **Dimension:** new-seams | **Location:** `main.tex Table S2 (tab:data), lines 549-561`

Visible citation-style asymmetry within one table is a seam fingerprint of the latest edit (citations were added to the touched rows only). Either cite atb2024nuclear in all ATB-sourced rows or none; and if precision matters, the financial-assumptions row points to a different ATB page than the cited bib entry's URL.

### 67. references.bib header verification comments do not cover the newly inserted doe2017chpAbsorption entry; whitespace insertion artifact around it

- **Dimension:** new-seams | **Location:** `references.bib lines 3-5 (header) and lines 300-311 (entry insertion point)`

The header asserts a complete verification provenance for the file's entries; the one entry added in this round falls outside all stated verification batches, making the header claim slightly stale (e.g. add "; doe2017chpAbsorption added and verified 2026-06-10"). The irregular blank-line pattern is a paste artifact that marks the insertion point.

## REFUTED (4)

1. `\label{sec:results:wacc}` on a `\runinhead` — verifier confirmed the reference resolves acceptably in the sn-jnl class; not a defect.
2. Author contributions "conceived" appearing twice — standard CRediT-style phrasing; not a defect.
3. "reactors ... are a conditional ... strategy" — plural subject with singular predicate nominative is grammatical; not a defect.
4. (Main-loop adjudication) "FOAK + carbon price" Discussion claim — exact, because Cases 0/3 are closed-form linear in carbon price and the FOAK shift is intercept-only; the extrapolated statement is mathematically valid as written.

## Out of scope / intentionally not flagged

- NLR (National Laboratory of the Rockies) naming — intentional, project-wide.
- The single Methods mention of legacy Section 45U (eligibility contrast, line 347) — sanctioned.
- Applied Energy manuscript — deliberately stale pending wholesale sync from the Nature Energy version.
- Disclosed-midpoint "~$59" nuclear crossover (actual $53.1/$64.3) — described as a range elsewhere; presentation choice, not an error.
