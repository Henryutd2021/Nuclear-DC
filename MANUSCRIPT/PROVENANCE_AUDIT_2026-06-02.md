# 溯源调查报告 — main.pdf 全文图 / 表 / 数字核验

**对象**：`AE_SMR_DC/Original version/main.pdf`（22 页，2026‑06‑01 19:31 编译）
**审计日期**：2026‑06‑02
**方法**：对照仓库内的原始数据（`data/`）、配置（`config/`）、模型代码（`src/`）与计算输出（`outputs/`），独立重算每一个图、表与正文数字；并对原始时间序列做"真实 vs 合成"统计取证。共动用 16 个子代理、279 次工具调用，对所有被标记项做了对抗式复核。

---

## 0. 总体结论（Bottom line）

**结果是真实、可复现、可溯源的——不是 AI 随机生成的。** 但**对输入数据的"描述层"（正文统计、Table 3、以及输入图 Fig "inputs" 的 b 面板）存在一组系统性的错误**，外加调度图 (Fig "dispatch") 的夏季周叙事与数据不符。这些都是**报告/作图缺陷，不是结果造假**：优化模型自始至终读入的是正确的真实数据，所有经济学结论（TAC、premium、碳价阈值等）都成立。

| 维度 | 结果 |
|---|---|
| 100 次运行真实存在 | ✅ `manifest.json` num_runs=100；100 个 `summary.json` + 100 个逐时 `dispatch.csv.gz`；分组 6/12/8/6/25/12/3/24=100 |
| 原始数据真实性（取证） | ✅ 4 条原始序列全部带有真实世界指纹（高自相关、价格肥尾、季节/日内结构），`SOURCES.md` 标注全部 REAL，无纯合成文件 |
| 正文数字（91 项独立重算） | 80 完全吻合 · 7 仅四舍五入差异 · 1 文献值（已正确引用）· **3 真实不符** |
| 图（11 张） | 10 张完全溯源到真实计算输出/原始输入；**1 张（Fig "inputs" b 面板）有作图 bug** |
| 表（4 张） | 配置/案例/情景表全部吻合；**Table 3（输入数据表）有多处标注/数值错误** |
| 设备/模型参数（43 项） | 42 完全吻合（含 CRF 公式独立验证）；1 项为碳强度 Table 3 错误（同下） |
| 造假证据 | **无**。未发现任何无出处或凭空生成的结果数字 |

---

## 1. 数据真实性取证（核心问题：是不是 AI 随机生成的？）

对模型真正读入的 4 条原始序列（`src/data.py` 路径）做了统计指纹检验，全部呈现**真实世界数据**特征，不可能是随机噪声：

| 文件 | 滞后‑1 自相关 | 真实性指纹 | 判定 |
|---|---|---|---|
| `data/ercot/2023_dam_lmp_houston.csv`（电价） | 0.873 | 均值 \$57.29 ≫ 中位数 \$22.72（肥右尾）；最高 \$4,188 与 SOURCES.md 记录的 2023‑08 极端稀缺事件吻合；317 h(3.6%)>\$200 | 真实 ERCOT 市场数据 |
| `data/weather/houston_ambient_2023.csv`（湿球温度） | 0.996 | 夏(JJA)均 25.1 ℃ vs 冬(DJF)11.9 ℃；午后 19.6 vs 夜间 17.5 | 真实 |
| `data/workload/dc_200mw_real_60u_2018.csv`（IT 负荷） | 0.955 | 峰 142.44 / 均 94.71 / CF 0.665；昼 98.2 vs 夜 84.9 | 真实（NLR/Vercellino‑2026 实测 ×20 缩放） |
| `data/environmental/ercot_carbon_intensity_hourly_2023.csv`（碳强度） | 0.968 | 夏 369.5 vs 冬 295.6 g/kWh | 真实（由 EIA‑930 发电结构推导的 AEF） |

每条序列均为 8760 行（2024 为 8784），`data/SOURCES.md` 给出了完整的 **paper → SOURCES.md → 原始发布方 URL** 溯源链，并附 `data/_raw/fetch_*.py` / `build_*.py` 抓取脚本（gridstatus.io、Open‑Meteo/ERA5、EIA RNGWHHDd.xls、EIA‑930、NLR）。**零文件为无真实来源的合成数据。**

---

## 2. 图 → 数据 溯源结果（11 张）

生成器：`notebooks/paper_figures.ipynb`（cell 5–15，统一调 `save_triplet` 出 pdf/png/svg），其中价值分解 CSV 由 `src/results/value_decomposition.py` 上游生成。

| 图（标签） | PDF | 数据来源 | 类型 | 状态 |
|---|---|---|---|---|
| schematic | fig1_system_schematic.pdf | 无（手绘机理图） | 概念示意 | ✅ 正确无需数据 |
| **inputs** | fig_inputs_overview.pdf | a/c/d 真实原始数据；**b 面板 LMP 时长曲线作图 bug** | 混合 | ⚠️ **panel b 有缺陷** |
| tac_stack | fig2_tac_stack.pdf | `master_kpi_table.csv`(main_baseline) | 计算结果 | ✅ Case0 \$64.3M / C1 \$203.1M / C2 \$207.3M / C3 \$53.3M 精确吻合 |
| size_matching | fig12_s8_size_matching.pdf | `master_kpi_table.csv`(s8) | 计算结果 | ✅ 2.5× gap \$149M、94.7MW 锚点吻合 |
| cost_carbon | fig3_cost_carbon.pdf | `master_kpi_table.csv`(s2_price) | 计算结果 | ✅ 坐标精确吻合 |
| dispatch | fig4_case2_dispatch.pdf | `outputs/main_baseline/case2/dispatch.csv.gz`（真实逐时 8760 行） | 计算结果 | ✅ 数据真实（年度 Q_abs=272,476 MWh 精确），但**夏季周叙事见 §4 问题③** |
| value_decomp | fig4bis_value_decomp.pdf | `outputs/figures/value_decomp_case2.csv` | 计算结果 | ✅ 六分量加和 = 净 −\$4.20M 吻合 |
| cooling_response | fig_sensitivity_cooling_response.pdf | `master_kpi_table.csv`(s1_pue, s6) | 计算结果 | ✅ |
| boundary_atlas | fig_sensitivity_boundary_atlas.pdf | `master_kpi_table.csv`(s2/s4/s7) | 计算结果 | ✅ 全部柱值精确吻合 |
| capital_cost_frontier | fig_capital_cost_frontier.pdf | `master_kpi_table.csv`(s5) | 计算结果 | ✅ 5×5=25 格全部存在，无插值/缺格 |
| policy_sensitivity_summary | fig_policy_sensitivity_summary.pdf | `master_kpi_table.csv`(s6 + tornado run_ids) | 计算结果 | ✅ 交叉点为真实端点的线性拟合，非硬编码 |

> **可复现性提示**：`paper_figures.ipynb` 于 2026‑06‑02 08:36 被修改，晚于 PDF 编译时间（06‑01 19:31）；磁盘上的 notebook 比 PDF 中嵌入的图更新，重跑不保证逐字节复现已编译图。所有图 PDF 的写入时间均早于 PDF 编译、且晚于其数据源（`master_kpi_table.csv` 17:38），顺序正确。

---

## 3. 表溯源结果（4 张）

- **Table（cases，案例配置）**、**Table（scenarios，情景设计）**：与 `config/`、`manifest.json` 完全一致（100 次运行结构、S5 5×5=25 等）。✅
- **Table（equipment，设备参数）**：反应堆/汽轮机(Willans)/吸收式/VCC/BESS/NGCC/冷却链/PUE/PCC/财务全部逐字存在于 `plant_caseN.yaml` 与 `data/*/*.yaml`；**CRF 经独立公式验证**：i=0.067,N=20 → 0.092203，与 `master_kpi_table.csv` 的 `crf_effective=0.0922` 精确一致；S7 的 5%/10% WACC → 0.0802/0.1175 亦由公式重算吻合。✅
- **Table（data，输入数据来源）**：⚠️ **存在多处错误**，见 §4。

---

## 4. 发现的问题清单（按严重度排序）

### 🔴 P1 — 必须修：图或数字与数据不符

**① Fig "inputs" b 面板（ERCOT LMP 时长曲线）是作图 bug，画的是合成曲线。**
notebook 的取数 glob 找的是 `ercot_dam_{year}.csv` / `dam_{year}.csv` / `{year}.csv`，但真实文件名是 `{year}_dam_lmp_houston.csv`，**三年全部匹配失败 → 落入合成兜底分支**：以一条基准曲线按硬编码比值 `{2022:57, 2023:47, 2024:30}`（注释为"from project memory"）缩放生成 2022/2024 曲线形状。更糟：被当作"2023 基准"的 `data/price_grid.csv` 其实与 2024 DAM 文件逐字节相同（均值 \$28.29）。**因此 b 面板的 2022 与 2024 时长曲线形状是单一年份的合成缩放，不是真实逐年序列。** 优化本身不受影响（`src/data.py:93` 读的是正确文件）。
*修复*：把 glob 改成 `{year}_dam_lmp_houston.csv`，从真实 CSV 重画 b 面板。

**② LMP 逐年均值（正文 §2.3 L336、§3 L503、Table 3、Fig inputs 标题）错误。**
正文标 2022=\$57 / 2023=\$47 / 2024=\$30；真实（模型实际读入的 DAM HB_HOUSTON 均值）= **2022 \$69.92 / 2023 \$57.29 / 2024 \$28.27**。本质是年份错位 + 一个无来源值：文中"2022=\$57"实为真实 2023 值，"2023=\$47"对不上任何序列，"2024≈\$30"尚可（真实 \$28.3）。根因同 ① 的硬编码占位 `means_ref={2022:57,2023:47,2024:30}`（`paper_figures.ipynb` L425）。Table 3 的范围"\$30–57"应为约"\$28–70"。
*注*：基准年是 2023，其真实 LMP 是 \$57.3，恰被错标成"2022"。

**③ Fig "dispatch" 的夏季周（7/15–7/22）叙事与数据不符。**
正文 L465 称该周"湿球温度有三个午后超过 26 ℃、其中两个越过 32 ℃ 冷却水入口的结晶门限、吸收式被强制离线、VCC 顶上"，图标题 L470 称"夏季午后吸收制冷的下降由结晶门限触发"。但对该窗口的 `dispatch.csv.gz` + 气象文件重算：**该周湿球峰值仅 26.95 ℃（从未 >27 ℃），结晶门限整周未触发，Q_VCC_cool 全 168 h 为 0、吸收式全程在线**——即图上根本没有任何吸收制冷的关停。全年真正触发门限的 115 h（湿球>27 ℃）落在 6 月底/7 月/8 月最热日（Jun 45h、Jul 42h、Aug 28h），不在 7/15–7/22。
*修复*：要么改画一个真正含门限小时的代表周，要么把叙事改为"COP 因湿球升高而降额（但未关停）"，并相应修正图标题。

### 🟠 P2 — 标注错误（数值真实但描述/归因错）

**④ 碳强度（Table 3、命名表、碳成本式文字）。** 标"380–430 g CO₂/kWh 边际(marginal)碳强度，来源 gridstatus.io"；但模型实际读入的 `ercot_carbon_intensity_hourly_*.csv` 年均为 **320–350 g/kWh**（2022/23/24 = 350.5/332.6/319.7），且 `build_real_carbon_intensity.py` 文件头明确写明这是**平均排放因子 AEF，不是边际 MEF**。SOURCES.md §7.3 自身亦标 320–350 与"AEF≠MEF"。来源也错：碳数据来自 EIA‑930 发电结构 ×UNECE/eGRID 因子，非 gridstatus.io。模型结果用的是真实 ~330 的 AEF，故碳足迹（Case2 −429 ktCO₂）正确；但 Table 的数值范围、"marginal"标签、以及"边际排放核算"的论述与数据/代码不一致。
*修复*：改为 ~320–350 g/kWh，并把 θ(t) 明确为 average EF（或换用 WattTime/AVERT 的真实边际序列）；更正来源。

**⑤ Henry Hub 行（Table 3）混淆了"亨利枢纽价"与"到厂燃料价"。** 标"\$2.63–6.53/MMBtu（年均），来源 EIA STEO"；但 \$2.63/\$6.53 实为**到厂燃料 = HH + \$0.10 船道基差**（=`master_kpi` case3 `delivered_fuel`），真实 HH 年均为 \$2.19–6.45。来源亦应为 EIA 日度现货 NG.RNGWHHD.D（非 STEO）。摘要/正文引用 \$6.53(2022)/\$2.63(2023) 数值本身可溯源，只是该行标签错。
*修复*：行改名"到厂天然气"，或改用真实 HH 值 6.45/2.53。

**⑥ 湿球超阈百分比（§2.3 / Fig inputs 标题）分母错。** 标"夏季约 8% 小时 >26 ℃、约 3% 夏季午后越 27 ℃"；真实 2023：>26 ℃ 占 JJA 夏季小时的 **31.6%**（8% 其实是占"全年"小时数），午后(12–18h)>27 ℃ 约 **11%**（任何自然定义都得不到 3%）。数值在真实数据里存在，但分母/措辞错。

**⑦ 湿球温度范围（Table 3）。** 标"−2 到 27 ℃"；真实 2023 为 **−0.47 到 28.06 ℃**（27 ℃ 是结晶门限，不是数据上限；三年合并最低 −10.9 ℃）。

### 🟡 P3 — 次要 / 内部一致性

| # | 位置 | 文中 | 实际 | 说明 |
|---|---|---|---|---|
| ⑧ | §4.1 L465 | VCC 备用 4.5 GWhc | **4.08 GWhc**（276,556−272,476 MWh，双法一致） | 高估约 10%，建议改 ~4.1 |
| ⑨ | 综述 L562 | 美元缺口"\$145–151 M/yr" | **\$143–151**（1.0× 缺口=\$143.0M） | 与 L437 自相矛盾（L437 正确写 \$143M）；\$145 其实是 1.5× 内点 |
| ⑩ | §4 WACC L546 | 5% WACC 时 \$181M | **\$181.57M → 应 \$182M** | 同句 \$262M 用四舍五入，\$181 用截尾，内部不一致 |
| ⑪ | §4.1 L465 | 冬季周净出力"~250 MWe 连续" | 实为双峰 268/133，均值 238 | "连续"不准确（降功率 38 h 降到 ~133）；VCC 闲置、吸收式全程在线两点正确 |

### ⚪ 仓库整洁性（不影响 PDF）

- `data/price_grid.csv` 实为 2024 文件，却在已损坏的 b 面板里被当作"2023 基准"。
- `data/equipment/ngcc_onsite.yaml` 的 `electric_capacity_MWe:50` 未被使用（模型用 `plant_case3.yaml` 的 200 MWe，与正文一致）。
- `data/reactor/bwrx300_economic.yaml` 残留过时注释 CRF=0.0907（权威值 0.0922，代码按公式重算）。
- `outputs/s8_case2_cost_audit.csv` 是孤立导出（未找到生成脚本），但其值与 `master_kpi_table` 一致，且 fig12 直接读 `master_kpi`，无风险。

---

## 5. 数字核验明细（独立重算，全部对到 3 位有效数字）

以下为已**精确核验**的代表性结果数字（来源：`master_kpi_table.csv` 及审计 CSV）：

- TAC：Case0 \$64.316M / Case1 \$203.145M / Case2 \$207.349M / Case3 \$53.320M ✅
- Premium：−215.9% / −222.4% / +17.1%；Case2−Case1 = \$4.204M = 6.54 pp ✅
- 碳足迹：306 / −407 / −429 / 385 ktCO₂/yr；Case1 随碳价 \$0→100 由 −407 深化至 −451 ✅
- 净出口：Case2 1.324 TWh/yr（=1,979,515−655,938 MWh）✅；超建系数 2.9×、2.6× ✅
- S8：2.5× → 237 MWe、0.043 TWh、−93%、gap \$149M、\$150 & \$72/MWh；3.0× → −78%、\$151M、净进口 0.38 TWh ✅
- 载荷匹配反事实：~104 MWe 净、−90% ✅
- 价值瀑布六分量：+5.51 / −8.915 / −1.283 / −0.192 / −0.011 / +0.687 → 净 −4.204M ✅
- PUE：吸收制冷 90.8/272.5/454.1 GWh；C2−C1 罚 −6.93/−4.20/−1.48M ✅
- S4 CAPEX：FOAK −490/−497%、ATB‑Mid −216/−222%、NOAK −8/−15% ✅
- S5 前沿：最佳角 (NOAK,Bare‑Low) −10.43%、最差角 (FOAK,Turnkey) −503.07%，25 格无一 ≥0 ✅
- S6 碳价交叉：Case3 \$140.5、Case1/2 \$187.5/\$187.8（≈\$188）；斜率 C0 +0.31、C3 +0.39、核电 −0.43~−0.45 M/yr·\$⁻¹ ✅
- 出口信用敏感性：减半 → ~\$357、取消 → >\$2,000/tCO₂（可由 CO₂ 分量列复现；注：并非在 `run_all_analyses.py` 中计算，而是可由已发布列推导）✅
- S7 WACC：5%→\$181.57M、10%→\$261.81M、跨度 \$80.24M；premium −182%/−307% ✅
- 100 次运行、8 组情景、S5 5×5：✅（manifest + 行计数双证）

---

## 6. 建议

1. **优先修 P1（①②③）**——这是会被审稿人/读者直接看出的"图与数据不符"。其中 ① 与 ② 同根（notebook 占位 + 文件名 glob bug），修一处即解两处：把 Fig inputs b 面板与所有 LMP 描述统一指向 `{year}_dam_lmp_houston.csv` 重算，正文/表/标题改用真实均值。③ 需重选代表周或改写结晶门限叙事。
2. **修 P2（④⑤⑥⑦）**——Table 3 的标注/范围/来源更正，碳强度 AEF/marginal 用词与论述对齐数据。
3. **修 P3（⑧⑨⑩⑪）**——一致性小修。
4. 重要重申：**以上没有一项是"结果造假"**。模型输入、求解、输出与 100 次运行均真实可复现；问题集中在"如何向读者描述输入"与一处作图脚本 bug。修正描述层后，论文的全部定量结论保持不变。

> 我尚未改动任何手稿或代码——按你的工作习惯，先交报告供你审阅。需要的话，我可以按上面的优先级逐条修复（先从 ①②③ 这一根同源的 LMP/图缺陷开始）。
