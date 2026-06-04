# Figure Role Audit — Nature Energy version

Date: 2026-06-04. Question asked: **what is each figure's job in the argument** — not rendering quality.
Three sub-questions: (1) do any figures duplicate each other in *meaning*? (2) does each figure contribute
to the paper's structure / logic / story? (3) is any claim that *should* be a figure currently missing one?

Method: I decomposed the manuscript's argument into **story beats** (the ordered claims the paper makes),
then asked of every figure: which beat does it advance, and does any beat get told twice or not at all.

---

## The argument as a beat sequence (what the paper claims, in order)

| Beat | The claim the reader must accept | Figure that carries it |
|---|---|---|
| B0 setup | four supply configs exist; here is the cogeneration mechanism | **Fig 1** + Table 1 |
| B1 headline gap | at 2023 mid-capital SMR costs ~2.5× grid even with the credit; only NGCC beats grid; absorption adds only $2.4 M | **Fig 2a** (TAC stack) |
| **B2 the credit is the lever** | **the 45U credit is decisive at NOAK and immaterial at FOAK/ATB, because only at NOAK is the pre-credit gap (~$26 M) small enough for the credit to close** | **— none —** |
| B3 carbon position | nuclear is low-carbon (net-negative via exports); gas/grid are high-carbon | Fig 2c (accounting) + Fig 2b (scatter) |
| B4 dispatch | absorption carries most cooling hour-by-hour; VCC backs up on hot afternoons / gate hours | Fig 4a,b |
| B5 absorption value | adding absorption is ~cost-neutral, and why (waterfall) | Fig 4c |
| B6 cooling sensitivity | absorption pays only when the electric chiller is inefficient (high PUE) | Fig 5 (a/b/c/d) |
| B7 market boundary | the ERCOT year / gas price sets the gas option's window | Fig 6a |
| B8 capital boundary | **the binding result:** the joint reactor×absorber frontier; the NOAK row is competitive | Fig 6d (+ Fig 6b) |
| B9 financing boundary | WACC compresses but does not close the gap | Fig 6c |
| B10 carbon route | a carbon price near $150 is a weaker second route | Fig 7a |
| B11 robustness | which axis dominates the margin | Fig 7b |

Read this table two ways: **a beat with two figures = a candidate duplication (Q1); a figure advancing no
unique beat = no narrative contribution (Q2); a beat with no figure = a missing visual (Q3).**

---

## Q1 — Meaning-level duplication (a beat told by more than one figure)

**1. B3 (carbon position) is told twice — Fig 2b duplicates Fig 2c + Fig 2a.**
Fig 2b (the TAC-vs-CO2 scatter) makes the reader believe "nuclear is clean but dear, gas/grid cheap but
dirty, nobody dominates." But that exact conclusion is already delivered by Fig 2a (which shows nuclear is
dear) plus Fig 2c (which shows nuclear is clean / net-negative). The scatter contributes **no beat that 2a
and 2c do not already carry**; its only original framing — a *cost–carbon Pareto trade-off* — is a
**different story than the paper tells** (the paper's axis is reactor capital, not a cost–carbon frontier).
This is the panel you remembered cutting; the recent consolidation silently reinstated it. → **Fig 2b is
the clearest meaning-duplication. Cut it.**

**2. B6 (cooling sensitivity) is told twice inside Fig 5 — 5a and 5c are the same beat.**
Both say "absorption flips from penalty to saving as the chiller gets less efficient." 5a says it in
dollars, 5c says it in margin points — same three runs, same crossover, one is a rescaling of the other.
A reader learns nothing from the second telling. Additionally **5d belongs to B10, not B6** (it is a
carbon-axis panel sitting inside the cooling figure), and B10 is already owned by Fig 7a. → **Fig 5 tells
one beat with four panels; it needs two: the driver (5b) + one statement of the flip (5a or 5c).**

**3. B8 (capital boundary) is told twice — Fig 6b is the Case-2 column of Fig 6d.**
6b's "reactor capital decides; NOAK flips Case 2" is exactly the message of the 750-$/kW column of the 6d
heatmap. 6d says the same thing **plus** the absorption axis (the actual two-factor result). 6b's only
non-duplicated content is the Case 1 bars. → **6b mostly re-tells B8; keep it only if you want the explicit
Case 1 vs Case 2 contrast, otherwise fold it into the text.**

**Net effect on the carbon thread:** beats B3 + B10 are currently spread over four panels (2b, 2c, 5d, 7a)
for a route the text itself calls "weaker" and "extrapolated." Removing 2b and 5d leaves 2c (mechanism) +
7a (threshold) — carbon told once, in proportion to its weight in the thesis.

---

## Q2 — Narrative contribution (does each figure earn its place in the story?)

Every figure advances a distinct beat **except** the duplications above:

- **Pulls its weight (unique beat, load-bearing):** Fig 1 (B0), Fig 2a (B1), Fig 2c (B3 mechanism — it
  underwrites the carbon route, since the net-negative footprint is *why* the TAC-vs-carbon line slopes
  down), Fig 3 (B2), Fig 4a-c (B4-B5), Fig 5b (B6 driver), Fig 6a (B7), Fig 6c (B9), Fig 6d (B8 — the
  headline), Fig 7a (B10), Fig 7b (B11).
- **Advances no unique beat (no narrative contribution beyond repetition):** Fig 2b, Fig 5c, Fig 5d,
  Fig 6b. These are the cut/fold candidates from Q1.
- **Over-serves its beat (one beat, too many panels):** Fig 3 spends four panels (margin / TAC / intensity
  / export) on B2; the beat is carried by **3a (never reaches parity) + 3d (the export-balance reason)**.
  3b and 3c re-state the same "size helps but does not close the gap" in other units. Not a duplication of
  *another* figure, but an internal over-telling.

So at the story level the figure set is **logically sound and well-ordered** (setup → gap → mechanism →
boundaries → ranking); the problems are localized over-tellings, not a broken structure.

---

## Q3 — Missing visual: the paper's central mechanism (B2) has no figure

This is the most important finding, and it is the opposite of redundancy.

The paper's headline contribution — stated in the abstract and conclusion — is: *"with the credit and
NOAK capital, both SMR configs fall below grid cost, opening a viable region **that capital-only analyses
miss**."* The mechanism behind that sentence is **B2: the credit is decisive precisely at NOAK because the
pre-credit gap to grid (~$26 M) has shrunk to the size of the credit, whereas at FOAK/ATB the same fixed
credit is a rounding error against a multi-hundred-million gap.**

**That mechanism is currently invisible.** It lives only in one prose sentence. Look at what the figures
show:
- Fig 2a shows the credit bar, but **at one capital level only** (ATB-Mid) — you cannot see the
  credit-vs-gap interaction across trajectories.
- Fig 6b/6d show the **post-credit** margin across capital — the credit is already baked in, so the
  reader cannot see what the credit *did* (the pre- vs post-credit gap).

A reader therefore has to take the single most novel claim of the paper on faith. **The missing figure** is
a small panel showing, for Case 1 and Case 2 across FOAK / ATB-Mid / NOAK, the **gap to grid without the
credit vs with the credit** (a before/after bar pair, or two lines). It would make the paper's thesis
mechanism land visually — "the credit only matters where the bar is already short." All the data exists
(`tac_usd_per_yr`, `ptc_annual_usd`, `tac_case0_baseline_usd_per_yr` in `master_kpi_table.csv`); no rerun.

Two natural homes: (i) replace the cut Fig 2b slot, keeping Fig 2 at 3 panels (TAC stack · **PTC lever** ·
carbon accounting); or (ii) add it as Fig 6 panel (next to the frontier it explains). I recommend (i) —
it puts the lever right after the headline gap, where the argument needs it.

No other beat is missing a figure: the cooling physics (COP, wet-bulb gate) sit in the SI inputs figure and
are exercised in Fig 4; the size break-even and the carbon threshold each have their panel.

---

## Bottom line

- **Duplicated in meaning (cut/fold):** Fig 2b (carbon position, off-thesis), Fig 5c (= 5a), Fig 5d
  (= carbon, owned by 7a), Fig 6b (= Case-2 column of 6d). Over-told: Fig 3 (4→2).
- **Every other figure earns a distinct beat;** the *structure and ordering are sound.*
- **One genuine gap:** the credit-as-lever mechanism (B2) — the paper's headline claim — has no figure and
  should get one (ideally in the freed Fig 2b slot).

## Decision points

1. **Cut Fig 2b** (restores your earlier decision; removes the only off-thesis figure) — yes/no?
2. **Add the missing "PTC lever" panel** (gap-to-grid with vs without credit, across FOAK/ATB/NOAK) in its
   place — yes/no? *(This is the one that strengthens the story, not just trims it.)*
3. **How far on the over-tellings:** (a) also do Fig 5 4→2 and Fig 3 4→2 and fold Fig 6b; (b) only Fig 2b
   swap + Fig 5; (c) only the Fig 2b → PTC-lever swap for now.

Once chosen: regenerate the affected figures from existing `outputs/` data, update captions and the few
orphaned sentences, recompile. No model rerun.
