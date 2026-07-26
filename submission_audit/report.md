# NUCLEAR-DC 补算与回填审计报告（submission_audit）

- 日期：2026-07-26；仓库 HEAD：`485a072e6993`（工作树在 `src/ config/ data/ scripts/` 下干净）
- 求解环境：Pyomo 6.9 + Gurobi 13.0.2 学术许可（有效期至 2026-12-16），Method=2（barrier）、Seed=42、MIPGap=1e-4、每解 4 线程 × 16 并行 worker——与产出 100-run 归档网格的设置完全一致
- 本次新增求解共 85 个：门禁 4 + B1 9 + B2/G9 72，全部落在 `submission_audit/` 下，**未覆盖任何已有输出**
- 稿件说明：`main_applied_energy_v5.tex` **不在本机**（仓库与家目录全盘检索均无）。本地两个版本（`MANUSCRIPT/Applied Energy/main.tex` 与未跟踪的 `Overleaf_upload_package_2026-06-26/` 快照，两者内容一致）都不含任务书第 11 节的三组 v5 专属锚点句（B1 外推句、45Y 摊销句、结论"about parity"句），说明 v5 是打包之后在改稿端继续演化的版本。按任务书 §0.1，走"只交数字"分支，**第 11 节回填未执行**；所有回填所需实解值都在 `results.json` 里。

---

## 1. 仓库初识

**目录结构（深度 2）**

```
Nuclear-DC/
├── config/            base.yaml + plant_case{0..3}.yaml + capex_grid_s5.yaml（costs.yaml 已弃用）
├── data/              ercot/ weather/ environmental/ economics/ reactor/ equipment/ perf/ workload/ _raw/
├── scripts/           run_all_analyses.py（100-run 网格驱动）、run_willans_sweep.py
├── src/               config.py data.py finance.py kpi.py performance.py
│   ├── cases/         case0.py(闭式) case1.py case2.py case3.py(闭式)
│   ├── milp/          builder.py(Pyomo 模型) solve.py(Gurobi 封装) result.py
│   └── results/       value_decomposition.py（S4 瀑布分解）
├── outputs/           main_baseline/ s1_pue/ … s8_size_matching/ + master_kpi_table.csv + manifest.json
└── MANUSCRIPT/        Applied Energy/main.tex（+figures/ +make_figures.ipynb）、Nature Energy/ …
```

**求解入口与复现命令**

- 入口：`scripts/run_all_analyses.py`，无 CLI 参数；并行度由环境变量控制（`NDC_WORKERS`，默认 16；`NDC_THREADS_PER_SOLVE`，默认 4，二者乘积钳制在 64 物理核内）。
- 完整复现命令：`NDC_WORKERS=16 NDC_THREADS_PER_SOLVE=4 .venv/bin/python scripts/run_all_analyses.py`
- 求解器设置在 `config/base.yaml`（gurobi / mip_gap 1e-4 / threads / method 2 / seed 42）；`src/milp/solve.py` 把这些逐项写进 Gurobi 参数。

**场景定义与 Table 5 的 G0–G8 映射**（`build_run_grid()`，scripts/run_all_analyses.py:551-710）

| 稿件组 | 代码组（outputs/ 子目录） | run 数 | 备注 |
|---|---|---|---|
| G0 | `main_baseline` | 4 | 2023、PUE 1.35、ATB-Mid、WACC 6.7% |
| G1 | `s1_pue` | 6 | 经 VCC COP 换算的等效 PUE {1.10,1.30,1.50} |
| G2 | `s2_price` | 12 | 市场年 {2022,2023,2024} |
| G3 | `s3_battery` | 8 | BESS on/off（Case0/3 为对照行） |
| G4 | `s4_capex` | 6 | FOAK 14,700 / ATB_Mid 7,615 / NOAK 2,250 $/kWe |
| G5 | `s5_feasibility_2d` | 25 | SMR {2250,5000,7615,11000,14700} × 吸收式 {450,600,750,900,1200} |
| G6 | `s6_carbon_price` | 12 | $0/50/100 per tCO2 |
| G7 | `s7_wacc` | 3 | 5% / 6.7% / 10%（仅 Case 2） |
| G8 | `s8_size_matching` | 24 | 0.5–3.0× IT 负荷 |

**关键参数位置**

- 反应堆资本：`config/plant_case{1,2}.yaml` 中 `reactor.capex_usd_per_kWe`（基线 7,615）；G4 三档由 `data/reactor/bwrx300_economic.yaml` 的 `scenarios` 提供，经 `src/config.py:with_reactor_capex` 注入；G5 成对覆盖走 `with_capex_pair`。
- 市场年：`load_time_series(year=…)`（src/data.py）按年拼路径 `data/ercot/{year}_dam_lmp_houston.csv`、`data/weather/houston_ambient_{year}.csv`、`data/environmental/ercot_carbon_intensity_hourly_{year}.csv`。
- 45Y 抵免：参数在 `data/economics/financial_parameters.yaml`（$30/MWh、10 年、`nuclear_ptc_enabled: true`）；在 `src/milp/builder.py:552-558` 经 `finance.levelized_ptc_usd_per_mwh(30, WACC, 10, project_lifetime_years=20)` = **19.7002 $/MWh_e**，按 `P_turb_net` 计入目标函数（负成本）。`project_lifetime_years` 全库只有此处与 `with_wacc`（B2 不涉及）两个消费点，`capital_recovery_factor` 仅作元数据——这正是 B2 的干净杠杆点。

**输出格式**：每 run 写 `outputs/<group>/<run_id>/summary.json`（标量 KPI + 元数据）与 `dispatch.csv.gz`（8760 行时序）；汇总 `outputs/master_kpi_table.csv`（100 行、未变圆）与 `manifest.json`。

**Gurobi 状态与耗时**：许可有效（academic，2026-12-16 到期），冒烟测试通过。单 run 典型耗时：Case 0/3 闭式 <0.1 s；Case 1 ≈ 9 s；Case 2 ≈ 15 s（含建模与写盘）。归档 100-run 网格总求解 952.4 s（16×4 并行，墙钟约 1–2 分钟）。

**归档产物的代码世代**：`outputs/manifest.json` 时间戳 2026-06-10T00:59Z，对应提交 225d301 时刻；其后 53fa33b（代码加固）、5b37dd5（打包自足化）只动了披露/健壮性层。门禁测试（下节）证明当前 HEAD 对归档值**逐位复现**，代码世代差异无数值影响。

---

## 2. 门禁测试（基线复现）——判定：通过（带一条注记）

命令：`.venv/bin/python submission_audit/scripts/run_gate.py`（把 `run_all_analyses` 的输出根重定向到 `submission_audit/runs_gate/`，其余全部复用生产代码）。

| 项 | 稿件值 | 实解值 | 偏差 |
|---|---|---|---|
| Case 0 TAC | 75.9 | 75.86905 M$ | 0.041% |
| Case 1 TAC | 113.4 | 113.37016 M$ | 0.026% |
| Case 2 TAC | 122.6 | 122.59420 M$ | 0.005% |
| Case 3 TAC | 55.6 | 55.57682 M$ | 0.042% |
| 45Y（C1/C2） | 42.9 / 41.8 | 42.86566 / 41.79097 M$ | 0.080% / 0.022% |
| 吸收式年供冷 | 352 GWh_c（占 38%） | 351.544 GWh_c（38.13%） | 0.130% / 0.354% |
| 运行小时 | 约 5,300 | **5,341（>0 阈值）/ 5,299（>1 MW_c 阈值）** | 0.77% / 0.02% |

- 连续量全部远低于 0.5% 门槛；与归档 master 表逐项比对，**TAC 相对差 0 至 1.2e-16（机器精度）**，Case 2 的 dispatch 与归档文件逐位相同（max diff = 0.0）。MIP gap 实测 1e-14–1e-13。
- **唯一超 0.5% 的是"运行小时"**：这是一个阈值敏感的计数量，稿件本身写的是"roughly 5,300"（百位近似）。同一份逐位一致的 dispatch，按 >0 计 5,341 h（对 5,300 偏 0.77%），按 >1 MW_c 计 5,299 h（偏 0.02%）；5,341 四舍五入到百位也是 5,300。**判定为舍入/口径粒度问题而非模型漂移**——证据是所有连续量的逐位复现。若希望严格化，建议稿件保留 "roughly 5,300"（或改为 "about 5,340"），并不需要重跑。
- 台账：`audit/ledger_full.csv`（100 行全部未变圆值 + G0–G8 标注 + 每行 `output_file` 溯源 + 生效反应堆资本列）。交叉核验 `audit/ledger_crosscheck.json`：master 表 ↔ 各 run summary.json 在 16 个字段上**零不一致**，margin 与 TAC 自洽零误差。

---

## 3. 任务 B1 —— 资本 × 市场年交互（8+1 个实解）

命令：`.venv/bin/python submission_audit/scripts/run_b1.py`；输出 `submission_audit/runs_b1/`（9 run，墙钟 15.3 s）。$5,000 档通过 `CUSTOM:5000` 场景注入（只改 `reactor.capex_usd_per_kWe`，其余与基线完全一致）；额外补了 1 个锚点 run（Case 1 @$5,000 @2023，归档网格里不存在），使可分性检验能覆盖全部 8 格。

| Case | 年 | 资本 $/kWe | TAC (M$/yr) | Case 0 (M$/yr) | 边际 | 净出口 TWh | 45Y M$ |
|---|---|---|---|---|---|---|---|
| 1 | 2022 | 2,250 | **−7.939** | 85.125 | **+109.3%** | 1.095 | 42.87 |
| 1 | 2022 | 5,000 | 45.825 | 85.125 | +46.2% | 1.095 | 42.87 |
| 1 | 2024 | 2,250 | 36.623 | 36.456 | **−0.46%** | 1.093 | 42.87 |
| 1 | 2024 | 5,000 | 90.388 | 36.456 | −147.9% | 1.093 | 42.87 |
| 2 | 2022 | 2,250 | 1.295 | 85.125 | +98.5% | 1.160 | 40.82 |
| 2 | 2022 | 5,000 | 55.060 | 85.125 | +35.3% | 1.160 | 40.82 |
| 2 | 2024 | 2,250 | 48.993 | 36.456 | **−34.4%** | 1.128 | 42.02 |
| 2 | 2024 | 5,000 | 102.758 | 36.456 | −181.9% | 1.128 | 42.02 |

- 年际差（ATB-Mid，来自未变圆台账）：C1 2023→2024 = **+28.143** M$、C2 = **+31.289** M$（稿件"约 \$28/\$31M"成立）；2023→2022 = −16.419 / −16.409 M$。
- **可分性检验**：predicted = TAC(资本,2023) + [TAC(ATB-Mid,年) − TAC(ATB-Mid,2023)]，8 格全部与实解一致，**最大偏差 1.5e-14 M$（≈1.5e-8 美元，纯浮点噪声）**。资本只以调度中性的常数进入目标函数，可分性精确成立；NOAK-2024-C1：predicted 36.6229 = solved 36.6229。
- 结论对 v5 外推句的校验：NOAK 在 2024 年 C1 = −0.46%（"approximately grid parity" ✓）、C2 = −34.4%（"about 34% above grid cost" ✓）；$5,000 档 2024 年为 −147.9% / −181.9%（外推句里的 `<LM_C1_2024>/<LM_C2_2024>` 占位符所需实解值）。
- 顺带产出：Case 1 @$5,000 @2023 锚点 TAC = 62.245 M$（边际 **+17.96%**，正）。
- 关于气象/碳配对：B1 各年 run 使用该年自己的湿球与碳强度序列（见 C5），与任务书要求一致。

## 4. 任务 B2 —— 45Y 摊销窗口敏感性（G9 组，72 个实解）

命令：`.venv/bin/python submission_audit/scripts/run_b2.py`；输出 `submission_audit/runs_b2/`（墙钟 70 s）。实现：`financial.project_lifetime_years` 20→40（仅核 case），令 `c_45Y = 30·A(6.7%,10)/A(6.7%,40)` = **15.4712 $/MWh_e**（从 G9 Case 1 dispatch 反推的实际抵免率 = 15.4712，机制端到端验证）。因抵免在目标函数内，全部 **70 个核 run 重解 +2 个补充资本点（$3,500、$4,500）**，未覆盖基线。

- **基线边际**（vs 未变圆 Case 0 = 75.869 M$）：C1 −61.56%（较基线 **−12.13 pp**）、C2 −73.36%（**−11.78 pp**）→ v5 的"about twelve percentage points"由实解证实。
- **Case 2 资本扫描（2023，吸收式 $750）**：

| 资本 $/kWe | 2,250 | 3,500 | 4,500 | 5,000 | 7,615 | 11,000 | 14,700 |
|---|---|---|---|---|---|---|---|
| TAC M$ | 26.640 | 51.079 | 70.629 | 80.405 | 131.530 | 197.709 | 270.047 |
| 边际 | +64.9% | +32.7% | **+6.9%** | **−6.0%** | −73.4% | −160.6% | −255.9% |

- **平价阈值（线性内插）：Case 2 = $4,768/kWe**（介于 4,500 与 5,000 之间）；Case 1（S4 锚点内插，网格较粗）≈ $5,226/kWe。⚠️ v5 现文的"moving the parity threshold from roughly \$5,000 to roughly \$4,500"偏激进：实解是 **≈$4,800**（基线 PTC 下的对应内插值约 $5,225，即"从约 $5,200 移到约 $4,800"，位移约 −$450）。建议按实解改写。
- **碳价交叉点（2023 ATB-Mid，G9）**：C1 = **$66.1**、C2 = **$76.2** /tCO2（均仍在 $0–100 求解范围内；基线 PTC 下为 $53.1/$64.2）。
- G7 注意事项：G9 下 `with_wacc` 会按 40 年窗口重算 `crf_effective` 元数据字段——该字段不进任何 TAC 项，仅出现在 summary 元数据里，已核实无数值影响。

## 5. 任务 B3 —— 图 6b 重绘（pp + ΔTAC 双标尺）

- 数据（Case 2 各轴两端未变圆 TAC，全部取自归档台账）：

| 轴（按 pp 排序，与原图一致） | TAC 低端 M$ | TAC 高端 M$ | ΔTAC M$ | pp 跨度 |
|---|---|---|---|---|
| Reactor capital | 17.704 | 261.112 | **243.41** | 320.8 |
| Market year | 106.185 | 153.883 | **47.70** | 297.4 |
| WACC | 93.977 | 184.184 | 90.21 | 118.6 |
| Carbon price | 85.980 | 122.594 | 36.61 | 84.9 |
| Data-center size | 80.043 | 292.798 | 212.75† | 82.0 |
| Absorber capital | 118.518 | 128.541 | 10.02 | 13.2 |
| PUE | 114.362 | 123.281 | 8.92 | 11.8 |
| BESS on/off | 122.594 | 123.356 | 0.76 | 1.0 |

- 任务书的判断被量化证实：pp 标尺下"资本 321 pp vs 市场年 297 pp"看似同级，ΔTAC 标尺下是 **$243M vs $48M，相差约 5 倍**。
- 重绘：`submission_audit/figures/fig_policy_sensitivity_summary_rev.{pdf,svg,png}`（脚本 `submission_audit/scripts/make_fig6b_rev.py`）。panel (b) 在每根 pp 横条下加薄荷青 ΔTAC 横条（顶轴 M\$/yr 标尺），**轴排序不变**；Data-center size 的 ΔTAC 条以斜纹+†标记，并在面板内注明"该轴缩放系统本身，绝对跨度不可与固定系统轴直接比较"（图注文字见 `results.json` 的 `B3.size_axis_caveat`，与任务书回填 4 的模板句一致）。panel (a) 按**已发布版**语义绘制（solved-range 竖线、0–100 实线/以外虚线）——注意：仓库 `make_figures.ipynb` cell 15 落后于已发布 PDF（见 §10 备注）。
- 质检：sci-figure QA（调色板 99% 合规、饱和度分布正常；留白 warn 为 tornado 图型固有）+ 三色盲模拟（`*_deuter/protan/tritan.png`）通过；未触碰 `MANUSCRIPT/Applied Energy/figures/`。

## 6. 任务 C5 —— 气象年 / 碳强度年配对审计

- **结论：逐年共采样（per-year）**。证据：`src/data.py:116-148` 按 `year` 拼装 `houston_ambient_{year}.csv`、`{year}_dam_lmp_houston.csv`、`ercot_carbon_intensity_hourly_{year}.csv` 三条路径，三个年份的文件都在且被加载；`scripts/run_all_analyses.py:468` 对每个 run 传 `spec.year`。价格、天气、碳强度是同年样本；IT 负荷是 2018 实测迹线，按各市场年做整日循环平移对齐星期相位（`src/data.py:43-60`）。
- **结晶门（T_wb + 5 K > 34 °C，即 T_wb > 29 °C）触发小时数：2022 = 0，2023 = 0，2024 = 0**。湿球峰值：2022 = 27.10 °C、2023 = 28.06 °C、2024 = 28.12 °C，全部低于 29 °C 门限（含扣除大修窗口后同样为 0）。
- ⚠️ 与任务书预期不符之处：任务书为"逐年配对"准备的插入句假设 2022/2024 有非零触发小时（"engages in <N2022> hours of 2022 and <N2024> hours of 2024"）。实际三年都是 0，且 2023 甚至不是湿球最高年（2024 峰值略高）。**建议改稿端把该句改写为**："Each market year is paired with its own wet-bulb and grid carbon-intensity records; the crystallization gate never engages in any of the three weather years (annual wet-bulb peaks of 27.1, 28.1 and 28.1 °C in 2022–2024, all below the 29 °C gate)."（含义更强：2022 年稀缺电价与吸收式降载的耦合担忧不成立，因为门根本没关过。）
- 结果文件：`submission_audit/audit/C5_results.json`（含分月分布，全为空）。

## 7. 任务 C6 —— 次级指标方法学（Supplementary Note 7）

- 交付：`C6_supplementary_note.tex`（Supplementary Note 7: Secondary endpoint definitions，含 NLCS/LCOC/EPBT/三层水的公式各一条 + 因子表 `tab:endpoint_factors`）与 `C6_sources.md`（逐因子出处 + 4 条新增 BibTeX：`lenzen2008nuclear / macknick2012water / boulay2018aware / wri2023aqueduct`；`atb2024nuclear`、`li2026nuclearH2` 复用现有键）。
- 任务书追问的两个口径问题已在 note 正文明确：①间接用水**因子按每 MWh 发电（Macknick 消耗量口径），分母按每 MWh IT 交付**，核电按全部净出力计（含 ~1.2 TWh/yr 出口，不做出口抵扣，偏保守）——这就是 6,807 L/MWh_e 的来历；②稀缺加权用的是 **AWARE 式世界当量刻度**，因子 0.65 为 WRI Aqueduct 基线水压力与 AWARE 的保守中点（世界均值=1.0）。吸收式因子 0.183 = 0.10×(1+1/1.2) 的推导也写入正文。
- 编译验证：把 note 插入仓库稿件副本 + 追加 4 条 BibTeX，pdflatex+bibtex 编译 **0 error、0 未解析引用**，因子表自动编号为 S6（在 S5 之后），版式目检正常。
- 不确定处（如实说明）：`src/kpi.py` 注释中核电嵌入能另提及 "IAEA 2018 INPRO update"，具体文号无法从仓库内证实，note 里只引 Lenzen 2008（可证实），IAEA 一条留给作者确认后再决定是否加引；Aqueduct 4.0 技术说明的 DOI 建议定稿时在 WRI 页面复核（BibTeX 里暂用 URL）。

## 8. 任务 M5 —— 瀑布图标签核对

- `fig_operation_value.pdf` panel (c) 中该分项标签印的是 **−7.5**。
- 未变圆真值（`outputs/figures/value_decomp_case2.csv`，main_baseline 行 `turbine_gen_lost_usd_per_yr`）= **−7,545,347.12 $/yr = −7.5453 M$/yr**。
- 判定：一位小数正确舍入是 **7.5**；表 S4 的 −7.55 是两位小数下的正确值。**v5 把 §3.2 从 \$7.5M 改成 \$7.6M 是对 −7.55 的二次舍入错误，应改回 \$7.5M；图无需重新生成**（重画只会得到同一个 −7.5）。
- `figure_regenerated: false`。

## 9. 任务 F —— 全稿数字通校（189 项）

命令：`.venv/bin/python submission_audit/scripts/run_f_audit.py`；明细 `audit/f_audit_table.csv`，汇总 `audit/F_results.json`。**189 项核对：182 项印刷值与未变圆真值在其印刷精度下一致**。

**四处"已知不一致"的定性（重要——其中三处印刷值本来就是对的）：**

| 位置 | 稿件印 | 未变圆真值 | 判定 |
|---|---|---|---|
| SI 表 S4，PUE 1.50 列和 | −2.35 | −2.353269 | **保留 −2.35**（各分项独立舍入后求和才得 −2.36；加"Components are rounded independently"注即可） |
| SI 表 S1，2.5× 年缺口 | 60.6 | **60.574**（250.247028 − 189.672625） | **保留 60.6**（"250.2−189.7=60.5"是用已舍入值做减法的假象） |
| §3.2 正文 Willans 分项 | \$7.6M（v5；原 \$7.5M） | −7.545347 | **改回 \$7.5M**（唯一需要改数字的一处） |
| SI 表 S5，2024 NGCC 边际 | −46.8% | **−46.753%**（1 − 53.49974/36.45567） | **保留 −46.8**（"1−53.5/36.5=−46.6"同为舍入值算术假象；加"Margins are computed from unrounded totals"注） |

**新发现（2 处，均为小项）：**

1. §2.1 IT 负荷 mean-to-peak "0.67"：真值 94.687/142.396 = **0.6649 → 应印 0.66**（0.67 来自 94.7/142.4 的舍入值相除）。
2. §2.1 调度实现 PUE "near 1.31"（VCC 各 case）：真值 1.3048（C0）/1.3049（C1）/1.3048（C3）→ **应为 "near 1.30"**；Case 2 的 "about 1.19" 正确（1.1937）。

**口径依赖项（记录在案、无需改动）：**

- §3.1 "roughly 42% of hours"低于 NGCC 运行成本：对固定 ~\$21/MWh 阈值成立（42.7%）；若按逐时燃料成本比较则为 40.5%。现文与其相邻句（"running cost of about \$21"）口径自洽，保留。
- §3.2 七月周"just under two thirds"：真值 63.3%，散文表述可接受（一月周"about a quarter" = 24.8% ✓）。
- §2.2 "全部 70 个 MILP 到 1e-4"：归档 summary 早于 gap 记录字段（53fa33b 加入），以本次 83 个新解为证：最大实测 gap 4.35e-05 < 1e-4，且新解对归档 TAC 逐位复现——命题成立。
- SI Note 3 的 α_w 扫描数值（−3.0…−11.1 M$、92%→16%）不在 100-run 台账内（当时为 SI 临时求解），本轮未复核；如需可另行重解。

其余亮点抽样（全部通过）：NGCC 外推交叉 \$164.6→"~\$165" ✓；碳价斜率 0.363/−0.344/−0.366/+0.490 → "0.36/0.34–0.37/0.49" ✓；出口摆幅 C1 274 pp、C2 297 pp → "some 270–300" ✓；NOAK 预抵免边际 +32.3/+21.6 → "+32/+22" ✓；S1/S2/S3/S5 全表逐格通过。

---

## 10. 交付清单与备注

```
submission_audit/
├── report.md                          本报告
├── results.json                       全部任务的结构化结果（每个数字带 output_file 溯源）
├── C6_supplementary_note.tex          SI Note 7（即插即用）
├── C6_sources.md                      因子出处 + 新增 BibTeX
├── audit/
│   ├── ledger_full.csv                100-run 未变圆台账（G0–G8 标注 + 溯源列）
│   ├── ledger_crosscheck.json         master↔summary 交叉核验（零不一致）
│   ├── f_audit_table.csv / F_results.json   189 项全稿数字核对
│   ├── B3_results.json / C5_results.json
├── runs_gate/                         门禁 4 run（gate_check.json + 完整 artifacts）
├── runs_b1/                           B1 9 run + B1_results.json
├── runs_b2/                           B2/G9 72 run + B2_results.json + g9_rows.csv
├── figures/                           fig_policy_sensitivity_summary_rev.{pdf,svg,png} + 色盲模拟
└── scripts/                           全部审计脚本（可复跑）
```

**与任务书预期不符 / 需要改稿端注意的汇总：**

1. `main_applied_energy_v5.tex` 不在本机 → 第 11 节回填未做；回填 1–5、7 所需的全部实解值都在 `results.json`（B1 四个 2024 边际、B2 的 −12.1/−11.8 pp 与 \$4,768 平价、C5 的 0/0/0、F 的取舍建议）。
2. 门禁"运行小时"一项按 0.5% 字面标准超限（0.77%），定性为计数口径/百位近似问题，连续量逐位复现，未按失败处理（理由见 §2）。
3. v5 回填 3 的现成文案（"about twelve percentage points"→实解 −12.1/−11.8 pp ✓，但 "\$4,500" → 实解 **\$4,768**）与回填 5 的模板句（2022/2024 触发小时 → 实为 0/0）需按实解修正。
4. 四处"已知不一致"中三处应**保留原印刷值**（S4 −2.35、S1 60.6、S5 −46.8），只有 §3.2 的 7.6 要改回 7.5——修复方向与任务书表格中的暗示相反，请改稿端注意。
5. 仓库 `make_figures.ipynb` cell 15 落后于已发布的 fig_policy_sensitivity_summary.pdf（缺 solved-range 竖线与虚线外推段）；若日后从 notebook 重生成图 6 会回退面板 (a)。本次重绘脚本已按已发布版语义实现，可整段移植回 notebook。
6. 两处新发现的小数字（0.67→0.66、1.31→1.30）建议随回填 7 一并修正。

**任务书 §12 验收自检**：门禁复现 ✔（带 §2 注记）｜B1 全部 run 达 1e-4 容差（实测 gap ≤4.3e-5，多数 1e-13 量级）✔｜可分性偏差 1.5e-14 M$ < 0.1 M$ ✔｜B2 为独立 G9 组、未覆盖基线 ✔｜图 6b 已重绘且尺寸轴已注记 ✔｜C5 结论带文件与行号证据 ✔｜C6 每个因子有可引用出处（两处不确定已如实标注）✔｜results.json 各数字带 output_file/source 溯源 ✔｜稿件未改动（v5 不在本机），编译/Highlights 检查项不适用；C6 note 已另行完成插入编译验证 ✔
