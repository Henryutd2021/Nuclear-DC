# Manuscript handoff — Tier-1 refinements + Section 45U PTC

Pasteable text and a number checklist for the manuscript. Nothing here has been
written into `main.tex`/`references.bib` — apply what you want. All numbers are
from the regenerated `outputs/master_kpi_table.csv` (full year 2023, PUE 1.30,
ATB-Mid reactor), main_baseline rows.

---

## 1. New Methods paragraph — Section 45U nuclear PTC (LaTeX-ready)

> **Nuclear production tax credit (Section 45U).** The annualized cost of the
> nuclear cases includes the Inflation Reduction Act's zero-emission nuclear
> power production credit (26~U.S.C.~\S\,45U; IRA~2022 \S\,13105). At the
> prevailing-wage rate the credit is \$15/MWh (1.5\textcent/kWh) and is subject
> to the statutory gross-receipts phaseout: it holds at the full value while the
> hourly market price $p$ (\$/MWh) stays at or below the \$25/MWh
> (2.5\textcent/kWh) threshold, then declines by \$0.80 for each \$1/MWh above it
> (the statutory 16\% reduction scaled by the prevailing-wage multiplier),
> reaching zero at \$43.75/MWh (4.375\textcent/kWh):
>
> \begin{equation}
> C_{45U}(p)=
> \begin{cases}
> \$15, & p \le \$25,\\[2pt]
> \$15\left(1-\dfrac{p-\$25}{\$18.75}\right), & \$25 < p < \$43.75,\\[4pt]
> \$0, & p \ge \$43.75.
> \end{cases}
> \end{equation}
>
> The credit is applied to net nuclear generation in each hour, with the ERCOT
> hourly LMP used as the per-kilowatt-hour gross-receipts proxy. We assume a
> power-purchase-agreement structure in which the data center is an unrelated
> offtaker, so that all delivered nuclear generation qualifies. Statutory amounts
> are inflation-indexed after 2024; we hold the nominal 2024 values. The credit
> applies to tax years through 2032 and is claimed on IRS Form~7213; in the
> single-representative-year framework it is applied to an operating year within
> the eligibility window.

**Disclosures to make sure land somewhere (Methods or Limitations):**
- PPA / unrelated-offtaker assumption (this is why all generation qualifies, not
  just grid exports). A behind-the-meter same-owner reading would limit 45U to
  exported MWh only.
- No inflation indexing; LMP used as the gross-receipts proxy.
- For a *new* SMR the strict vehicle is 45Y (flat \$15/MWh, no price phaseout,
  10-yr window); 45U and 45Y deliver the same \$15/MWh, so the result is
  insensitive to which is named. (Optional one-liner if a reviewer might press.)

## 2. Methods sentence — part-load efficiency (P1)

> **Part-load performance.** Chiller electricity follows the AHRI~550/590
> integrated-part-load COP curve, which peaks near 40–50\% load; in the nuclear
> MILP this is an SOS2 piecewise map of electricity on cooling output. The NGCC
> heat rate rises below the design point per a representative F-class
> combined-cycle curve, raising fuel use and combustion emissions together.

(Note: the NGCC part-load curve is a representative shape, flagged in
`src/performance.py` — swap for a plant-specific source if you have one.)

## 3. Table 3 caption fix — per-component annualization (L1/L2/L3)

Replace "all CAPEX annualization uses the 20-year project CRF" with:

> Each asset's CAPEX is annualized over its own engineering life (reactor and
> main turbine 20~yr, vapor-compression and absorption chillers 25~yr, NGCC
> 30~yr, battery 15~yr with a 5\% end-of-life salvage credit). The absorption
> chiller carries a 0.95 maintenance availability.

---

## 4. Number-update checklist

| Where | Old | New |
|---|---|---|
| Abstract headline (Case 3 grid-cost margin) | "by 25\%" | **"by about 29\%"** (+28.65\%) |
| Case 0 TAC | — | **\$78.1 M/yr** (LCOE \$94.1/MWh) |
| Case 1 TAC | — | **\$192.2 M/yr** (LCOE \$231.6/MWh) |
| Case 2 TAC | — | **\$194.6 M/yr** (LCOE \$234.5/MWh) |
| Case 3 TAC | — | **\$55.7 M/yr** (LCOE \$67.1/MWh) |
| New PTC line, Case 1 | — | **−\$26.4 M/yr** (credit) |
| New PTC line, Case 2 | — | **−\$25.8 M/yr** (credit) |
| Case 3 lifecycle CO2 | — | **486,300 t/yr** (586 kg/MWh) — part-load raised it ~3.6\% |
| Heat-recovery delta (Case 2 − Case 1) | — | **+\$2.4 M/yr** — absorption still does not pay back at ATB-Mid/2023; the PTC widens the gap slightly because diverting steam to the chiller cuts creditable generation |
| Figures | — | re-run `notebooks/paper_figures.ipynb` against the regenerated `outputs/` |

Net CO2 for the nuclear cases is **negative** (Case 1 −388 kt, Case 2 −448 kt):
the overbuilt reactor exports clean power and is credited the dirtier ERCOT
marginal mix it displaces. Already in the model; worth a sentence if not present.

---

## 5. BibTeX for the new citations

```bibtex
@misc{usc26_45u,
  title        = {26 U.S.C. \S\,45U --- Zero-emission nuclear power production credit},
  author       = {{U.S. Code}},
  year         = {2022},
  howpublished = {Office of the Law Revision Counsel},
  note         = {Inflation Reduction Act of 2022, Pub. L. 117--169, \S\,13105},
  url          = {https://uscode.house.gov/view.xhtml?req=(title:26+section:45U+edition:prelim)}
}

@misc{irs_45u,
  title        = {Zero-Emission Nuclear Power Production Credit},
  author       = {{Internal Revenue Service}},
  year         = {2024},
  howpublished = {IRS Credits and Deductions; claimed on Form 7213},
  url          = {https://www.irs.gov/credits-deductions/zero-emission-nuclear-power-production-credit}
}
```

(26 CFR \S\,1.45U-3 for the prevailing-wage 5x multiplier, and CRS Insight
IN12557 for the phaseout explainer, are available if you want secondary cites.)
