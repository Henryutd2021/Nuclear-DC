# Nuclear-DC（Nature Energy 版）手稿全维度证据链审计报告

> 审计对象：`/home/honglin/Nuclear-DC/MANUSCRIPT/Nature Energy/main.tex`（≈752 行）+ 配套 `references.bib`、`figures/`、`make_figures.ipynb`、`outputs/`、`src/`、`config/`。
> 审计日期：2026-06-04。本报告由综合分析师汇编自 5 份事实层证据卡（A1–A5）+ 4 份判断层证据卡（B2/B4/B5/B6）+ 一轮对抗式验证后存活的 confirmed / partially-confirmed 结论。
> 行文约定：中文叙述，但所有 manuscript 引文、数字、`file:line`、术语、推荐改法均保留英文/原记号。每条结论先给 verdict，再给 evidence chain（manuscript location → claimed value/text → data/code/source value → verdict）。

---

## 0. 执行摘要 — 总体判断 + 按严重度排序的 Top 问题

**总体判断（实事求是）**：这是一份**数据极其自洽、模型实现忠实于 Methods、thesis 一以贯之**的高质量稿件。A1 逐条核验了几乎全部 headline 经济数字（TAC、margins、PTC、LCOE、CAC、EPBT、water、CO2、crossover、spans、2D grid corners、size-matching、WACC、carbon slopes），无一与 `outputs/master_kpi_table.csv` 及四个 case summary 矛盾；A4 把每条 Methods 方程逐行映射到 `src/`+`config/`，结论是 "faithful，无 equation-vs-code 行为级偏差"；B4 的 thesis-ring 测试判定核心论点（"reactor capital, not heat recovery, sets the viability boundary"）在 STRONG 证据下成立。**没有任何已发现的缺陷推翻论文结论。** 绝大多数问题属 rewrite-text / fix-citation / replace-or-move-figure 级，唯一真正"硬错误"是引用归属。

**Top 问题（按严重度）：**

1. **[CRITICAL · fix-citation] ATB 被归属到一个不存在的机构 "National Laboratory of the Rockies (NLR)" / `atb.nlr.gov`，而真实来源是 NREL / `atb.nrel.gov`。** 驱动：`references.bib:126` `institution={National Laboratory of the Rockies}`、`:131` `url=https://atb.nlr.gov/...`；`main.tex:597` 明文 "follow the National Laboratory of the Rockies 2024 Annual Technology Baseline"。这是论文**最核心成本数据**（reactor/NGCC/BESS CAPEX、FOM、CF、asset life）的 provenance，且是一次失败的 find-replace（`src/kpi.py:41,44` 仍保留 "NREL"），无法以 single-blind 匿名为由辩护（稿件自己署名 Li/She/Zhang）。

2. **[HIGH · rewrite-text] gross grid buy/sell（2.16 / 0.73 TWh）是 LP 退化产物，只有 net export（1.43 TWh）是物理量。** 驱动：`main.tex:109` 报 "2.16 TWh/yr gross sales against 0.73 TWh/yr grid imports"；`dispatch.csv.gz` 中 5,912/8,760 小时同时 buy+sell，重叠量 732.6 GWh ≈ 整个报告进口量；`builder.py:408-414` buy/sell 同价、无 round-trip loss、无互斥约束 → LP 对任意 (buy,sell) 分解严格无差异。TAC 与碳核算只依赖 net，**不变**，但 0.73 TWh 进口数字会被审稿人当作不合理 dispatch 抓住。

3. **[HIGH · rewrite-text] Methods/SI 完全未披露求解器与全部求解设置。** 驱动：`main.tex:234,277` 只写 "MILP/SOS2"，全文 grep `gurobi/solver/seed/mip_gap/barrier/method/threads` 零命中；而 `config/base.yaml:8-18` 实配 `gurobi, mip_gap 1e-4, method 2 (barrier), seed 42, threads 16`，`summary.json` 仅存 `solve_seconds`。这是 Nature Energy 可复现门槛的标准 reviewer flag。

4. **[HIGH · replace-figure] Fig 5(a) carbon crossover 把 >$100/tCO2 的外推区画成与求解区无法区分的实线，并烤入 "Nuclear ~146"/"NGCC ~191" 标签。** 驱动：solved grid 仅 `{0,50,100}`（`outputs/s6_carbon_price/`），两个 crossover（C2 $142.4、NGCC $190.8）全在外推区；`make_figures.ipynb` cell-15 整段实线无 dashing、无 `axvline(100)` 参考线。文本已披露（`main.tex:165,170,187`），故为 figure-honesty 问题而非数字错误。

5. **[HIGH · rerun/repackage] 手稿图无法用随附的 `make_figures.ipynb` 复现。** 驱动：`main.tex:113,129` `\includegraphics{fig_baseline_economics, fig_operation_value}`，但 grep 该 notebook 两个文件名均 NOT FOUND；两张 composite 只由 `notebooks/make_composite_figures.py`（硬编码 `NB=notebooks/paper_figures.ipynb`）生成；三个图脚本还硬编码作者机器路径 `/home/honglin/.claude/skills/sci-figure/scripts`（未随仓库分发）。

6. **[MEDIUM · rewrite-text] 同一 size-matching 序列在图与正文用了不同端点：Fig (c) 标 "140 → 58"（2.5×），`main.tex:109` 写 "$140 to $49"（3.0×）。** 两端点各自正确（140.4 / 57.9 / 48.7，均源自 master_kpi），但交叉核对的 reviewer 会看到 58 vs 49 的表面矛盾。

7. **[MEDIUM · rewrite-text] "100 model runs" 略微夸大独立优化数。** 100 行 master 表只含 76 个 unique TAC / 79 个 unique input vector（21 行是 4 个 anchor 在各 group 的 re-listing，Case0/Case3 的 bess_on 行 `bess_applied=False` 与 bess_off 完全相同）。注意：Methods L234/L370 与 Table S9 footnote L747 已部分披露此事，故为透明度润色而非硬错误。

**两条次级但值得修的会计/物理 caveat（B6，均已被作者披露，仅需文字收紧）：**
- `main.tex:250` "Willans coefficient roughly **one order of magnitude** smaller" 实际比值 η_r/α_w = 0.345/0.083 = **4.16×**，非 ~10×；
- net-negative CO2（C1/C2 −388/−448 kt）仅因 1.43 TWh 出口按 ERCOT **hourly-average** EF 计入避排，作者已在 `main.tex:174,191` 诚实披露。

---

## 1. 图（Figures）逐张分析（8 张，依据 B2_cards.md + A3_figures.md，所有 PNG 已作为图像直读）

Thesis ring = "reactor capital, not heat recovery, sets the viability boundary"。Verdict 图例：KEEP MAIN / MOVE-TO-SI / DEMOTE-PANEL / MERGE / REPAIR。

### Fig 1 — System schematic（`fig1_system_schematic.pdf`, main.tex:91-96）
- **作用/thesis**：建立 Case-2 架构（reactor→HP turbine→mid-P extraction→double-effect LiBr→LP turbine；VCC backup；ERCOT PCC；BESS），间接服务 thesis。
- **正确性**：手绘，无数据可矛盾；标签（BWRX-300、200 MW IT、BESS 100 MWh/50 MW、PCC、double-effect LiBr）与正文 L83/L217-219 及 Table 1 一致 ✓。
- **可读性**：清晰，色盲友好。**Verdict：KEEP MAIN。** 小注：DC 侧未标 "270 MWe net"，无害。

### Fig 2 — Baseline economics（`fig_baseline_economics.pdf`, 复合三联, main.tex:111-116）
- **(a) TAC stack**：thesis 最承重 panel。On-figure C0 78/+0%, C1 192/−146%, C2 195/−149%, C3 56/+29%，全部 VERIFIED ✓。
- **(b) cost-carbon scatter** + **(c) nuclear CO2 accounting**：on-figure 全部 VERIFIED（net −411/−388/−364 (C1)、−476/−448/−422 (C2)）。
- **Verdict：(a) KEEP MAIN；(b),(c) DEMOTE / MOVE-TO-SI。** 驱动（B2 KEY-2）：carbon 故事在 2b/2c/5a 讲了三遍；thesis 已把 carbon 降级为 "contingent"，却把 baseline 图 3 panel 中 2 个给了 carbon。建议把 2(c) 移 SI，2(b) 并入 Fig 5。
- **可选增强（B2 KEY-1）**：(a) 改为 Case0→nuclear 的 waterfall/bridge（+capital,+O&M,+fuel,−export,−PTC）。Action：replace/redesign-figure（optional）。

### Fig 3 — Operation & value（`fig_operation_value.pdf`, 复合, main.tex:127-132）
- **(a,b) 冬/夏 dispatch**：absorber 承担 ~94% 制冷、VCC 仅热午后顶峰。VERIFIED（winter P_tn 125.9–268.4、P_rx max 870、summer Q_VCC max 29.5）✓。
- **(c) value-decomposition waterfall**：+18.2/−4.1/−13.2/−2.3/−0.6/−0.04/residual −0.35/net −2.4，与 `value_decomp_case2.csv` **逐项精确吻合** ✓。
- **Verdict：KEEP MAIN。** (c) 是 absorption 接近 break-even 的最佳证据。
- **重要 caveat（A2-01）**：waterfall 只在 anchor 处闭合（residual 14.6% of net）；off-anchor 急剧发散（load×3.0 384%、co2_$50 437%、2022 1471%）。**手稿只发布 anchor（Fig 3c）与 PUE-sweep（Table S7），两处 residual 都小，故图本身无缺陷**。验证发现 `value_decomposition.py:216-217` 把 `price_export = price_import`（同序列），A2 所称"价格故意非对称"**未被激活**，residual 由 fixed slope + post-hoc 归因驱动。**建议**：SI 加一句说明该 decomposition 是近 anchor 有效的 approximate post-hoc attribution。

### Fig 4 — Boundary atlas（`fig_sensitivity_boundary_atlas.pdf`, 4 panel, main.tex:151-156）
- **作用/thesis**：**核心 thesis 图**。(b)/(d) 显示 reactor capital 移动 margin ~397 pp 且唯一跨越 parity；(d) 显示 absorption ≤13 pp。
- **正确性**：(a) 2022 −120/−120、2023 −146/−149、2024 −487/−510；(b) FOAK −372/−375、ATB −146/−149、NOAK +25/+22；(c) −115/−149/−221；(d) NOAK +27..+14、FOAK −370..−383，**全部 VERIFIED** ✓。
- **冗余（轻）**：(b) 是 (d) 的 SMR 轴子集，但 (b) 额外带 Case1 与 $-tick，属可接受 primer。
- **Verdict：KEEP MAIN（thesis 最强图）。** 不依赖 carbon crossover ✓。

### Fig 5 — Policy & sensitivity（`fig_policy_sensitivity_summary.pdf`, 2 panel, main.tex:167-172）
- **(a) carbon crossover**：**HIGH 缺陷（B2-02, confirmed）**。solved 仅 `{0,50,100}`，实线一路画到 $250（xlim 0–272），>$100 区为纯外推却与求解区**视觉无法区分**（无 dashing、无 `axvline(100)`——已核 cell-15 源码确认全缺）。两 crossover 与两 shaded band 全在外推区。**文本已充分披露**（L165/L170/L187），故非数字错误。**建议（replace-figure）**：>$100 段改 dashed + 加 "$100 = max solved" 竖线。
- **(b) tornado**：thesis 最佳单图总结——reactor capital 397pp、market year 391pp 主导；absorption 13、PUE 4、BESS 1。VERIFIED ✓。
- **Verdict：(b) KEEP MAIN（thesis crown panel）；(a) KEEP MAIN 但 REPAIR 标注。**

### SI Fig — Inputs overview（`fig_inputs_overview.pdf`, main.tex:589-594）
- 4 条外生 trace。(c) IT load mean 95/peak 142 ✓；(d) gated-solid vs ungated-dashed COP 与 `builder.py` 一致 ✓。**Verdict：KEEP SI。**

### SI Fig — Cooling response（`fig_sensitivity_cooling_response.pdf`, main.tex:663-668）
- absorption value 随 PUE/carbon 变号。(a)13.0/4.6/−4.6;(b)1.9/13.8/23.0;(c)−16.6/−5.8/+5.9;(d)−3.1/+0.6/+3.1 全 VERIFIED ✓。(a)/(c) 同一 C2-C1 差的 $/pp 两表达，可合一。**Verdict：KEEP SI。**

### SI Fig — Size matching（`fig12_s8_size_matching.pdf`, main.tex:694-699）
- 经核图读 **master MILP TAC**（非 `s8_case2_cost_audit.csv`），与 Table S8 一致 ✓。
- **缺陷（MEDIUM, B2-03/B1-02, confirmed）**：panel (c) 烤入 "140 → 58"（2.5×），`main.tex:109` 写 "$140 to $49"（3.0×）。两值各自正确，但交叉核对见 58 vs 49。SI Note 8 "235→143" 是**另一指标**（cost intensity），已正确标注，不构成第三矛盾。**建议（rewrite-text）**：统一端点（首选图改 "140→49"@3.0×）。**Verdict：KEEP SI。**

**跨图横切**：carbon 在主图占比偏高（2b/2c/5a），整合到 Fig 5 可更聚焦 capital thesis；仅 Fig 5a 依赖外推，需视觉标注边界。

---

## 2. 表（Tables）逐张分析（1 主表 + 9 SI 表，依据 B2_cards.md + A1）

### Table 1 — Cases（main.tex:205-222）
block-enabled matrix，与 Methods L203 及 config 一致 ✓。**KEEP MAIN，无冗余。**

### Table S1 — Nomenclature（main.tex:413-509）
|T|=8760、C={0,1,2,3}，Methods 符号全列 ✓。**KEEP SI（必需）。**

### Table S2 — Input data sources（main.tex:515-544）
- **Verdict：KEEP SI**，但 **DEDUPLICATE（rewrite-text, B2-04, confirmed）**。与 S3 重复 7 个成本行：BWRX $7,615/$121（S2:530-531 vs S3:558）、absorption $450–1,200/$750（S2:534 vs S3:560）、VCC $250（S2:535 vs S3:561）、BESS $405+$1,620（S2:536 vs S3:562）、NGCC $1,330（S2:537 vs S3:563）、lives 20/25/25/15/30（S2:540 vs S3 Life）。逐字一致且与 `plant_case*.yaml` 吻合，纯维护风险（偏 low）。S2 非 S3 子集（多带 FOAK/NOAK 界）。**建议**：S2 改纯 provenance（source+units+"see Table S3"）。
- **两条 source 行缺 bib key（MEDIUM, A5-03, confirmed）**：L539 WACC 6.7% → "MIT nuclear-finance survey"（bib 无 MIT 条目）；L534 absorption capex → "ASHRAE TC **8.3**" 无 `\citep`，唯一 ASHRAE 条目是 TC **9.9** Thermal Guidelines（非成本源）。**建议（fix-citation）**：补可引 MIT 文献或改 authors' assumption；attach 真实 chiller-cost 文献（`ahri2020standard550`/`herold2016absorption`/`srikhirin2001absorption`），reconcile/删 "TC 8.3"。

### Table S3 — Equipment cost & performance（main.tex:546-583）
每值经 A4 对 config 核验 ✓。technical 子表唯一。**KEEP SI。**

### Table S4 — Market years（main.tex:602-617）
LMP 70/57/28、gas 6.53/2.63/2.35、Case0 86.2/78.1/36.9、Case3 87.1/55.7/53.6、NGCC margin −1.1/+28.7/−45.1，2023 VERIFIED ✓。**KEEP SI。**

### Table S5 — Secondary cost & carbon KPIs（main.tex:619-636）
LCOE 94.1/231.6/234.5/67.1 ✓；CO2 +369/−388/−448/+486 ✓。**关键诚实点**：LCOC 仅 Case0=25.3，Cases1/2/3 正确标 "--"（A2-02 NaN），**无 overclaim**。**KEEP SI。** CAC $142.7/150.8 与 Fig 5a 外推 crossover 数值巧合但已分源（§2.2 用 CAC、§2.5 用外推），OK。

### Table S6 — Water（main.tex:638-655）
四 case 全 VERIFIED ✓。**KEEP SI。**

### Table S7 — Value decomposition（main.tex:670-689）
baseline col +18.24/−2.26/−13.22/−4.15/−0.62/−0.04/−0.35、net −2.39 ✓；PUE net −12.96/−4.56/+4.64 ✓。所示范围 residual 皆小，诚实。**KEEP SI**（Methods 宜声明 anchor-/PUE-valid）。

### Table S8 — Size matching（main.tex:701-718）
TAC 154.3/.../355.5（= master MILP）✓；margin −295/.../−52 ✓；excess 278/140/95/72/58/49 ✓。"excess over grid"（140@1.0×→49@3.0×）是 L109 之源，与图标 "140→58"（2.5×）端点不一致——见 §1，需统一。**KEEP SI。**

### Table S9 — Scenario ledger（main.tex:723-749）
group counts 与 master EXACT MATCH ✓。**内容 flag（rewrite-text, B2-05/A2-03, confirmed）**："Total 100"/"100 model runs"（L83/L181）夸大独立优化数（实 76 unique TAC / 79 unique input vector，21 行 re-listing）。**已部分披露**：L747 footnote "control denotes duplicated control rows ... optimized only for Cases 1 and 2 because Cases 0 and 3 are closed-form"，L234/L370 亦说明。**建议**：加注 "100 ledger rows = 79 unique input configurations / 76 distinct optimized TAC"，正文软化为 "100 scenario evaluations spanning 79 configurations"。**KEEP SI。**

---

## 3. 优化与计算结果分析（依据 A1/A2/B1/B3）

### 3.1 数据可复现性（结论：REAL & 高度自洽）
A1："Every headline economic number reproduces from `master_kpi_table.csv` and the case summaries to within rounding. All 100 run-group counts match Table S9 exactly. All 37 citation keys resolve; all 54 `\ref` targets resolve. No hard contradictions found." A4 手算 Case1 baseline TAC buckets 到分（Reactor CAPEX $189.575M + VCC $3.34M = $192.915M = `capex_annual_usd` 192,914,879 exactly）。

### 3.2 数字溯源 match 覆盖率
A1 ledger 覆盖 **150+ 条 claim**，几乎全标 ✓。明确 **UNVERIFIED**（取作 declared input/result）：32%/5% wet-bulb hours（L361）、2,870/115 hours（L658）、42% NGCC hours（L658）、126/861/863 GWhc cooling-by-PUE（L136）、320–351 CI range（L526）、S5 LMP means（L610）、net-export full row（L713）；均与已核相邻值自洽，宜更深一轮对 dispatch/raw traces 复核。

### 3.3 所有 mismatch / untraceable / inconsistent
- **[gross grid 退化, B3-01, HIGH, confirmed]** L109 "2.16 TWh gross / 0.73 TWh imports"：5,912 小时同时 buy+sell、重叠 732.6 GWh = 100.0% of gross buy；真实净进口仅 ~0.3 GWh。根因 `builder.py:408-414`（同 LMP、无 loss、无互斥）；2023 DAM LMP min $1.55、零负价，无套利动机。Case1 同病（gross buy 861,823 MWh）。**只有 net（1.43 TWh）确定**。**建议（rewrite-text）**：L109 只报 net，或加 "gross split is non-unique under symmetric LMP; only net is determinate"。
- **[s8 audit CSV orphan, A2-04/B1-03, LOW-MED, partially-confirmed]** `outputs/s8_case2_cost_audit.csv` 是 manifest 未登记孤儿，TAC（@1.0× 207.35M）与 master MILP（194.57M）系统性不一致，**但无任何 figure/table/正文引用**（grep 全零命中）。订正：master TAC **也是线性**（恒定 +40.227M/step），二者是不同斜率的线，非 "linear vs non-linear"。**建议（repo-hygiene）**：删除或重命名 + 登记 manifest。**非**手稿问题。

### 3.4 外推标注（结论：充分披露，图需视觉标注）
carbon crossover $142-151/$191 是 **3 点线性拟合**外推至 >$100。B4 §0/B6 核：因 TAC 对 carbon price 严格线性，全程拟合 crossover 与 static CAC 重合（C2 142.4≈142.67，C1 150.5≈150.80），**非杜撰**；文本三处披露。唯一遗留：Fig 5a 未视觉区分（见 §1）。小注：crossover 有 fit-dependence（2-pt segment 给 131/137），宜加一句 "linear fit across all three solved points"。

### 3.5 唯一运行数 vs "100 runs"（结论：透明度润色）
100 行 = 79 unique input vector = 76 unique TAC。订正：normalized 后为 76（与 unique TAC 一致），真实 redundancy 24 行。手稿从不称 "100 independent optimizations"（一贯 "model runs"/"run ledger"），L234/L370/L747 已部分披露。**Action：rewrite-text（optional polish）**。

### 3.6 敏感性完整性
8 group（G0–G8）覆盖 case×year×pue×load×SMR-capex×abs-capex×bess×co2×wacc，group counts 与 Table S9 EXACT MATCH。**未变动维度（已披露）**：export-credit retention 未在 G6 扫（L174）；reactor=smallest unit 非 optimized buildout（L191）。

### 3.7 确定性/可复现（结论：可复现但披露不足）
模型近乎纯 LP（唯一整数结构 VCC SOS2，无 binary），seed/MIP-gap 对最优值影响极小；但 **求解器与设置全未披露**（A4-D1，见 §0 第 3 条），`solve.py:24` 默认 mip_gap 0.005 ≠ `base.yaml:9` 0.0001（A4-D2，wired path 用 config，无现结果影响）。`manifest.json` notes 有 "Pyomo MILP solved with Gurobi"（求解器名在 archive，settings 无；手稿本体全无）。

---

## 4. 方法与物理稳健性 + 代码一致性（依据 B6/A4）

### 4.1 代码忠实度（结论：FAITHFUL）
A4 映射每条 Methods 方程到 `src/`+`config/`，**无 equation-vs-code 行为级偏差**。逐条 ✓：reactor bounds/ramp/CF、Willans(0.083)、η_r(0.345)、COP anchors(1.10/1.30/0.015/26)、gate(32−5=27)、VCC SOS2、BESS SOC、energy balances、TAC buckets、PTC(15/25/43.75, slope 0.80)、carbon(Θ=1e-3, hourly-avg θ(t))、NGCC(η_hhv 0.495, γ_ng 420)。B6 手算 carbon slopes/crossover/PTC slope/Willans 全吻合。

### 4.2 会计约定（可辩护，关键 caveat 已披露）
- **carbon export-credit（B6-4）**：C1/C2 net CO2 负**仅因** 1.43 TWh 出口按 hourly-AVERAGE θ(t) 计避排（`builder.py:421-427`）。用 average 而非 marginal EF 偏**保守**（低估出口避排），把 crossover 推**高**而非低。L174/L191 已披露。**建议**：net-negative CO2 引用处必带 export-credit caveat（A2-06）。
- **PTC**：45U $15/MWh，slope 0.80（=0.16×5）复现 L347 "16% reduction" ✓；applied to net gen 假设 PPA unrelated-offtaker，L191 已 flag。
- **CRF/asset lives**：20/25/30/15 yr @ WACC 6.7%，CRF20=0.0922 已核；turbine bundled into $7,615/kWe，一致。

### 4.3 物理假设可辩护性
- **[B6-1, rewrite-text] Willans "one order of magnitude"**：L250 实为 4.16×，应改 "about four times / a factor of several"。
- **[B6-2, flag/SI provenance] absorption COP**：double-effect 真实 1.2–1.4；design 锚 1.10@26°C、cap 1.30 偏**保守**；0.015/°C 斜率方向对但 magnitude + 用 wet-bulb 是简化且**无引用源**。
- **[B6-3, flag/可作 robustness rerun] crystallization 硬 binary cutoff**：27°C 全开/全关（`builder.py:63-74`），实操多用 dilution control 连续降容。理想化**偏保守**（强迫 VCC backup 扛 ~115 h，抬高 Case2 成本）。
- **[B6-5, fix-citation] NGCC part-load 曲线**：`performance.py:26-27` 自带 caveat "confirm against a preferred plant-specific source before publication"；Methods L322 无引用，**provenance gap**。

### 4.4 缺失项（披露与偏向）
- **forced outages / unit commitment**：未建模（L243 披露）。
- **N+1 / five-nines（最 ranking-relevant 遗漏）**：Case3 +29% 建立在 islanded 单列无冗余无 grid tie，L191 披露 "five-nines ... would erode its baseline advantage"，但 headline +29% 未内联 caveat。
- **interconnect CAPITAL（部分披露 gap）**：无 300 MW 双向 interconnect 资本（`builder.py:345-378` 仅功率限无 $/MW），**偏向 nuclear**（免费出口路径赚 2.16 TWh），L191 列 demand charges 但未列 interconnect capital。
- **PPA/retail tariff/demand charge 基准（B4-04/05）**：Case0 = wholesale DA LMP only，真实 hyperscale 还付 demand/T&D/capacity；Case0 偏低**放大** −146/−149% 负 margin（方向对作者不利的偏置）。L191 披露但 headline/abstract 未带方向性 caveat。

---

## 5. 逻辑架构与 thesis 一致性（依据 B4）

### 5.1 Claim→Evidence 矩阵（B4 §1 节选）
| # | Headline claim | Where | Strength | Note |
|---|---|---|---|---|
| H1 | 146-149% more than grid even with PTC | L62/L105/L145 | STRONG | reproduces exactly |
| H2 | NOAK 22-25% cheaper, no carbon | L62/L145 | STRONG | |
| H3 | absorption supplies 94% cooling | L62/L189 | **MODERATE** | baseline-only; PUE1.10 跌至 13.7% |
| H4 | absorption changes cost by only $2.4M/yr | L62/L107/L134 | **MODERATE** | baseline-only; PUE sweep −13.0~+4.6M |
| H5 | **reactor capital sets boundary (THESIS)** | Title/L83/L181 | **STRONG** | SMR 397pp vs absorber 13pp |
| H6 | only NGCC beats grid (+29%, 2023) | L107/L141 | STRONG | market-year-specific（已注） |
| H7 | carbon crossover $142-151/tCO2 | L165/L187 | WEAK-disclosed | 外推 >$100，已标注 |
| H8 | G5 frontier: 仅 NOAK 行 viable | L158/L183 | STRONG | thesis-proving panel |
| H9-H11 | size 2.5× still −62% / WACC far above / BESS negligible | L109/L149/L143 | STRONG | reproduce |

### 5.2 Abstract↔Body scope drift（B4-01, rewrite-text）
`main.tex:62` 把两个 **baseline-only** 数字（"94% cooling"、"$2.4M/yr"）**无条件**陈述。Body（L136, Table S7）显示 PUE1.10 时 absorber share 跌到 ~14%（126 GWhc），$2.4M 在 sweep 内翻为 −$13.0M/+$4.6M。**建议**：abstract 加 "at the baseline (full-load PUE 1.35)" 限定。Abstract **未**声称 "100 runs"（仅 body），故 count 漂移仅限 body。

### 5.3 内部矛盾
未发现 hard numeric contradiction（所有图与 CSV 吻合）。"94% but adds little value" 仅 baseline 自洽；sign-flip 已披露（break-even ~PUE 1.40）。建议单独引用处加 "at the baseline" tag。

### 5.4 结构/叙事顺序（B4-03, optional）
**thesis 最清晰两证据（Fig 4d 第 4 图 panel d；tornado 末图 panel b）都到很晚出现**，略埋 lede。§2.3 cooling（null result）先于 §2.4 frontier（headline），可辩护（先消解读者疑问）。属编辑判断，非缺陷。

### 5.5 过度声称
未发现 OVER 级 claim。LCOC 对非 Case0 正确留空；carbon crossover 标外推；BESS/carbon 诚实降级。

---

## 6. 语言/叙事/科学严谨性/AI 指纹（依据 B5；带行号与原文）

### Tier 1 — AI-fingerprint（最高杠杆，作者要求 human read）
- **[B5-01] 两个 "Here we" 开头**：abstract L62 "...remains uncertain ... **Here we** use an hourly techno-economic co-optimization"；intro L83 "**Here we** present a techno-economic boundary analysis"。**改一处**（如 intro: "We present..." 或 "This study maps..."）。
- **[B5-02] L185 "This finding changes how the data-center nuclear question should be framed"**：空洞 significance 模板。**替换**为实质 lead，如 "Three supporting levers — load matching, market regime and financing — narrow but never close the gap."
- **[B5-03] "X sets/does not set the boundary" 三连**：Title L51 "governs"、abstract L62 "sets the viability boundary"、intro L83 "does not set the economic boundary"、discussion L181 "do not set the boundary"。**至少一处换动词**。
- **[B5-04] 三元/串列 list 在相邻两句堆叠**：abstract L62 与 intro L83 共 5 个 "X, Y and Z"，L83 单句承载 3 个。**拆句、其一改散文**。
- **[B5-05] "far above grid cost/supply" 三次**（L83/L141/L185）：数字已存在（−146/−149%），**两处删 "far above" 改数值**。

### Tier 2 — 措辞严谨性
- **[B5-06] "about"(18×)/"roughly"(10×) 带精确已核数字**："about 2.9 times"(2.85×)、"about 115 hours"、"roughly 42%"、"on the order of 10%"(实 8.9%)。dispatch 读数处给精确值更严谨。
- **[B5-07] "far too small"/"comfortably below"/"essentially parity"**：L145/L141 处量化（"$26M offsets <1 pp of −372% gap"；"+25% and +22% below grid cost"；删 "essentially"）。
- **[B5-08] L145 "reactor capital outweighs all other costs by roughly a factor of five"**：A1 ledger 中**唯一未独立核验**的精确倍数；追溯 FOAK TAC stack 引用或软化为 "dominates the total"。

### Tier 3 — 术语/缩写
- **[B5-11] "VCC" body L125 先用后定义**（仅 caption L130/SI L439 展开）；**首次 body 出现处加 "(VCC)"**。
- **[B5-12] "PUE" caption L114 先于 body L136 定义**：把 "(PUE)" 移到首个 Results 用处。
- **[B5-14] L125 "$\sim 270$ MWe net"**：固定 nameplate，他处无 ~，**删 tilde**。

### Tier 4 — 叙事（优点）
- **[B5-16]** boundary-map framing（L81 问句 + L193 收尾）干净，margin（L98）一次定义贯穿——**无 action**。
- **[B5-18]** "$2.4 M/yr" 出现 6+ 次；Discussion L189 可改 reference 而非 restate（low priority）。

---

## 7. 引用与参考文献完整性（依据 A5；NLR/NREL 为首要）

### 7.1 [CRITICAL · fix-citation] ATB 归属到虚构机构 NLR（A5-01/A1-01, confirmed）
- **驱动**：`references.bib:126` `institution={National Laboratory of the Rockies}`、`:129` `address={Golden, CO}`（恰是 NREL 所在地）、`:131` `url=https://atb.nlr.gov/...`；`references.bib:29` `vercellino2026aiworkload` `institution={National Laboratory of the Rockies Data Catalog}`；正文经核命中 `main.tex` **19+ 行**：105,114,154,170,361,363,490,517,529,530,531,536,537,540,597,666,672,703,725，L597 明文 "follow the National Laboratory of the Rockies 2024 Annual Technology Baseline"。
- **真相**（web-verified）：ATB 是 NREL 产品，canonical host `atb.nrel.gov/electricity/2024/{nuclear,about}`。"National Laboratory of the Rockies"/`nlr.gov` 不是真实机构。
- **是 botched find-replace，非 blinding**：`src/kpi.py:41` "NREL ATB 2024 LCI screening value"、`kpi.py:44` "NREL Macknick 2012" 仍保留 NREL；`data/MANUAL_COLLECTION.md:56` 存盘到 `data/economics/nrel_atb_2024_raw/`（NREL 路径）而 L50-55 用 `atb.nlr.gov`（同文件自相矛盾）。仓库 ~101 NLR 命中 vs 22 残存 NREL。
- **Verdict：CRITICAL confirmed（甚至偏 understated）**。数值输入（$14,700/$7,615/$2,250 kWe）本身正确。
- **Action**：全局 `National Laboratory of the Rockies`→`National Renewable Energy Laboratory`、`NLR`→`NREL`、`atb.nlr.gov`→`atb.nrel.gov`，覆盖 bib 两条目 + ~19 行 main.tex + 同步仓库 docs（`data/SOURCES.md:158`、`data/MANUAL_COLLECTION.md:50-55`、`data/workload/profile_stats.yaml`、`data/equipment/*.yaml`、`data/economics/financial_parameters.yaml:38` 等）。

### 7.2 [HIGH→MED · fix-citation] IT-load 单一来源 + 作者名拼错（A5-02, partially-confirmed）
- **确认**：`references.bib:27` first-author 误作 "Robert"，arXiv:2604.07345 实为 "**Roberto** Vercellino"（web 核实）。唯一**硬错误**（fix-bib）。
- **确认**：IT-load 是唯一外生需求输入，由 10 MW profile **线性 ×20**（`build_real_ai_workload.py:46` `(power_W/1e6)*20`，`it_load.csv` mean 94.71/max 142.44 吻合），无独立 trace 验证；arXiv 预印本（2026-04-08，~2 月龄未 peer-review）。
- **订正/refuted 子项**：finding 称 institution "NLR-alias" 是错误——实则 arXiv 上该来源**自称** "National Laboratory of the Rockies (NLR), Golden, CO"，手稿一致使用同 alias；**不应**改成 "NREL Data Catalog"。single-profile caveat 已存在 `main.tex:191`。
- **Action**：仅 `Robert`→`Roberto`（必改）；可选加一句 Methods caveat。建议 high→medium。

### 7.3 [MEDIUM · fix-citation] 两表内 source 无 bib backing（A5-03，见 §2 Table S2）
WACC 6.7% 的 "MIT nuclear-finance survey"（L539）+ absorption capex 的 "ASHRAE TC 8.3"（L534）均无 key；唯一 ASHRAE 条目是 TC 9.9 Thermal Guidelines（非成本源）。

### 7.4 其他（rewrite-text / 文档级，A5-04~07）
- `references.bib:2` 注释 "cas-model2-names.bst" 与实际 sn-vancouver.bst 不符（仅注释）；
- `references.bib:6-8` 声称末尾有 commented-out entries，实则没有（stale）；
- **10 条 defined-but-uncited**：7 条是 Intro 该讨论的 related-work（`bhowmik2026nuclearDC`、`zhang2026nuclearDC`、`debnath2025smrDER`、`you2025dynamicEquilibrium`、`haywood2012thermodynamic`、`ebrahimi2015thermoeconomic`、`eia2024nuclearDC`），3 条作者自引。**建议 cite-or-drop**。
- **OK 项**：36/36 cited keys 全 resolve；54 `\ref` 全 resolve；policy/data 源 keys 归属正确。

---

## 8. 审稿人预演（Nature Energy）

> **诚实声明**：本任务 prompt 称提供 "Two reviewer pre-mortems (JSON below)"，但该 JSON **未实际出现在输入中**。以下预演是综合分析师**基于已核证据自行推演**的合理场景，**非**对原 pre-mortem 文本的转述——标记 **unverified（推演）**，不应当作既有 reviewer 意见引用。

**Reviewer 1（techno-economic / energy systems）——倾向 Major Revision：**
- 反对：(a) 比较基准是 wholesale DA LMP only，Case0 偏低**放大** −146/−149% 负 margin（§4.4）——要求加 delivered-tariff sensitivity 或 headline 标方向性 caveat；(b) interconnect capital 未入任何 CAPEX bucket，偏向 nuclear；(c) carbon crossover 全靠外推 + hourly-average EF，要求 Fig 5a 视觉标注并讨论 marginal-EF。
- 正面：认可数据自洽、模型透明、limitations 诚实。

**Reviewer 2（核工程 / 方法严谨度）——倾向 Minor-to-Major Revision：**
- 反对：(a) **求解器与设置完全未披露**（§3.7），code-availability 标准下必补；(b) 引用完整性——ATB 归到不存在的 NLR、dead URL（§7.1），copy-editing/verification 不会放过；(c) gross grid 0.73 TWh 进口物理上不合理（§3.3）；(d) abstract 的 94%/$2.4M 是 baseline-only 却无条件陈述（§5.2）；(e) Willans "order of magnitude" 名不副实（§4.3）。
- 正面：认可 SOS2/MILP 表述清晰、CRF/PTC 公式可复现、frontier 设计巧妙。

**编辑层面预判（推演）**：核心发现成立且新颖（capital-not-heat-recovery boundary map），但 Top-7 含 1 个 CRITICAL（引用）+ 4 个 HIGH 必须在 revision 解决方能过 reviewer verification 与 copy-editing；这些**全是 rewrite-text/fix-citation/replace-figure/repackage 级，无需重跑模型或重做研究**——本稿可在一轮 revision 内救回。

---

## 9. 行动清单（按 action_type 分组）

### A. fix-citation（必改）
1. **[A5-01/A1-01, CRITICAL]** 全局 `National Laboratory of the Rockies`→`National Renewable Energy Laboratory`、`NLR`→`NREL`、`atb.nlr.gov`→`atb.nrel.gov`：bib（`atb2024nuclear` L126/128/129/131；`vercellino2026aiworkload` L29）+ main.tex 19 行 + 仓库 data/config docs。
2. **[A5-02]** `references.bib:27` `Robert`→`Roberto`（仅作者名；institution NLR alias **保留**以维持 anonymization 一致性）。
3. **[A5-03]** Table S2 的 WACC（L539）补可引 MIT 文献或改 "authors' assumption"；absorption capex（L534）+VCC（L535）attach 真实 chiller-cost 文献，reconcile/删 "TC 8.3"。
4. **[B6-5]** NGCC part-load 曲线（Methods L322）补 plant-specific 引用或 SI 标 provenance caveat。

### B. fix-number（必改）
5. **[B6-1]** `main.tex:250` "roughly one order of magnitude smaller" → "about four times smaller"（η_r/α_w=4.16×）。
6. **[B1-02/B2-03]** size-matching 端点统一（见 D 区）。
7. **[A4-D2, LOW]** `solve.py:24` 默认 `mip_gap` 0.005 对齐 config 0.0001。

### C. rewrite-text（按优先级）
8. **[B3-01, HIGH]** L109 gross grid → 只报 net，或加 "gross split is non-unique under symmetric LMP; only net is determinate"。
9. **[A4-D1/B3-04, HIGH]** Methods 加一句：solved with Gurobi (version), barrier (Method=2), seed 42, MIP gap 1e-4, 8760-h horizon；可选写入 summary.json metadata。
10. **[B4-01, MED]** abstract L62 的 "94%"/"$2.4M/yr" 加 "at the baseline (full-load PUE 1.35)"；body 单独引用处统一加 "at the baseline" tag。
11. **[B2-05/A2-03, MED]** Table S9 加注 "100 ledger rows = 79 unique input configurations / 76 distinct optimized TAC"；正文 L83/L181 软化为 "100 scenario evaluations spanning 79 configurations"。
12. **[B2-04, LOW]** Table S2 改纯 provenance（剥离与 S3 重复的 7 个 CAPEX/FOM/life 值）。
13. **[B5-01~05, AI-fingerprint]** 改一处 "Here we"；替换 L185 模板句；"sets the boundary" 三连换一处动词；拆 L83 多 list 长句；两处 "far above" 改数值。
14. **[B5-06~08/11/14]** 关键 "about/roughly" 改数值；L145 "factor of five" 追溯引用或软化；body 首用处加 "(VCC)"；删 L125 tilde。
15. **[A5-04~07]** 修 bib stale bst 注释、false "commented-out" 注释；cite-or-drop 10 条 unused entries。
16. **[A2-06/B6-4]** net-negative CO2/intensity 引用处带 export-credit + hourly-average-EF caveat。
17. **[B6, optional]** carbon crossover 加 "linear fit across all three solved points"。

### D. replace-or-move-figure
18. **[B2-02, HIGH]** Fig 5a：>$100 段改 dashed，加 "$100 = max solved" 竖线；保留披露文字。
19. **[B1-02/B2-03/A3-02, MED]** size-matching panel (c) arrow 与 L109 统一端点（首选图改 "140 → 49"@3.0×）。
20. **[B2 Fig2, MED-optional]** Fig 2(c) CO2 accounting 移 SI；2(b) 并入 Fig 5（整合 carbon）。
21. **[B2 Fig2(a), optional]** TAC stack 改 Case0→nuclear waterfall/bridge。

### E. rerun-analysis / repackage（无需重做研究，仅工程）
22. **[A3-01, HIGH]** 复现管线：把 `paper_figures.ipynb` + `make_composite_figures.py` + `make_nature_energy_selected_figures.py` 定为单一 documented pipeline；修 bundled `make_figures.ipynb`（或改 thin wrapper 产出两 composite）；**vendor `sci_figure_helpers`**（三脚本硬编码 `/home/honglin/.claude/skills/sci-figure/scripts`，未随仓库分发）；reconcile `README.md:133`（漏两 composite 脚本）。
23. **[A2-04/B1-03, LOW]** 发布前删除或重命名 `outputs/s8_case2_cost_audit.csv` 为 `*_LINEARIZED_costcurve.csv` + header；登记/排除于 `manifest.json`；订正旧 `PROVENANCE_AUDIT_2026-06-02.md:112` 错误断言。
24. **[B6-3, optional robustness rerun]** 可加一组 continuous COP de-rate 作 robustness check（非必需）。

### F. redesign-study
- **无。** 所有 HIGH/CRITICAL 项均可在一轮 revision 内以 A–E 类动作解决。

---

## 10. 审计方法与可信度说明

- **核验规模**：A1 ledger 逐条核验 **150+ 条 claim**，几乎全部对 `master_kpi_table.csv`（100×50）、四个 case summary、`value_decomp_case2.csv`、`config/*.yaml` 复现到 rounding；A4 逐行映射 Methods 方程到 `src/`+`config/` 并手算 baseline TAC 到分；8 张 figure PNG 全作为图像直读、每个 baked annotation 追溯源 CSV；10 张表全读 main.tex 并对 config 核值。
- **对抗式验证（refuted/订正）**：本报告结论均经一轮对抗式 re-verification，若干原始 finding 被**部分推翻或下调**，已如实标注：
  - A2-01/B3-08（waterfall）：手稿只发布 anchor+PUE 两处（residual 皆小），off-anchor 发散列从未出图入表，且 `value_decomposition.py:216-217` 证明 import/export 同价（"非对称定价"未激活）→ high 下调为 non-defect/low；
  - A2-04/B1-03（s8 audit）："master TAC non-linear" 被推翻（master 也线性，只不同斜率）；孤儿无引用 → 降为 repo-hygiene；
  - B1-01/A2-03/B2-05/B3-03（100 runs）：手稿从不称 "independent optimizations"，L234/L370/L747 已部分披露 → 降为透明度润色；unique 数订正为 76；
  - A5-02（Vercellino）：institution "NLR alias 错误" 被推翻（arXiv 自称即 NLR），仅作者名拼写为硬错误 → 降为 medium。
- **未获输入项（实事求是）**：prompt 称提供 "Two reviewer pre-mortems (JSON below)"，但该 JSON 未实际出现在输入中；§8 系基于已核证据的**推演**，已明确标记 unverified。被部分 finding 引用的 sibling artifact 路径偶有错指（如把 `make_figures.ipynb` 误称 `paper_figures.ipynb`、line number 偏 2-6 行），本报告已逐一以直接读取的 file:line 订正。
- **truthfulness 承诺**：每条 verdict 附 manuscript location → claimed value → data/code/source value → verdict 证据链；未能核验者一律标 "unverified/推演"；未杜撰任何数字、行号或缺陷。已知 spot-verified 正确的上下文数字（Case0 $78.1M、Case1/2 $192.2M/$194.6M、margins −146%/−149%、NOAK +25%/+22%、FOAK −372%/−375%、Case2−Case1 −$2.39M、PTC −$26.4M/−$25.8M）经本轮复核一致，未重新 flag。
