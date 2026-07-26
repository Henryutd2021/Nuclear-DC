# C6 — 次级指标方法学与因子出处清单

配套交付物：`C6_supplementary_note.tex`（Supplementary Note 7: Secondary endpoint definitions）。
本清单逐项给出每个公式/因子在代码中的实现位置与可引用出处，并标注新增 BibTeX 条目。

## 1. 指标 → 代码实现 → 公式

| 指标 | 实现位置 | 公式（与 Note 7 编号对应） | 分母/边界要点 |
|---|---|---|---|
| NLCS | `scripts/run_all_analyses.py:150-151`（`lcoe_usd_per_mwh_e = tac / it_energy_annual_MWh`） | NLCS_c = TAC_c / E_IT | E_IT = Σ P_IT(t)Δt = 829,667.48 MWh_e/yr（各 case 相同）；分子含冷却资本、碳价、45Y、出口净额 → 不是发电 LCOE |
| LCOC | `src/kpi.py:82-121` 与 `scripts/run_all_analyses.py:180-191` | (CRF·CAPEX_v + FOM_v + VOM_v + Σ π_g P_v Δt) / Σ Q_v Δt | 只对 Case 0 报告：Cases 1–3 的共享发电成本无法非任意地在 IT/冷却间分摊（代码 docstring 明确此理由）；Q = 921,852.76 MWh_c/yr |
| EPBT | `src/kpi.py:142-162`（`EMBODIED_ENERGY_MWH_PER_KWE`） | EPBT = e_k·S_k / E_gen | e_rx=4.5、e_ng=1.0 MWh_e-eq/kWe；S_k = 270 MWe（核）/200 MWe（NGCC）；分母 = 全部净发电（核含出口，非 IT 份额）；Case 0 无定义 |
| 直接场址用水 | `src/kpi.py:181-236`（`water_footprint_l_per_mwh`） | W_dir = (0.10·Q_v + 0.183·Q_a)·1000 / E_IT | 消耗量口径（withdrawal−return）；分母 MWh_e,IT |
| 间接发电用水 | 同上 | W_ind = (2.54·P_tn + 0.78·P_ng + 1.42·P_g+)·1000 / E_IT | **因子按"每 MWh 发电"，分母按"每 MWh IT 交付"**；核电按全部净出力计（含 ~1.2 TWh/yr 商业出口，不做出口抵扣）→ 对核方案偏保守，这正是 Case 1 = 6,918 vs Case 0 = 1,964 L/MWh_e 的原因 |
| 稀缺加权用水 | 同上 + `AQUEDUCT_SCARCITY_FACTOR_ERCOT_SOUTH = 0.65` | W_sc = 0.65 × W_tot/1000（m³ world-eq） | AWARE 式世界当量刻度（世界均值=1.0）；0.65 为 Aqueduct 基线水压力与 AWARE 的保守中点（ERCOT South/Houston） |

备注（S4 表 memo 行）：水外部性单价 0.50 $/m³ 来自 `src/results/value_decomposition.py:41-45`
（Macknick 2012 + 得州工业水价 TWDB 2024 中点，作者估计），仅作 memo，不进 TAC。

## 2. 因子 → 出处

| 因子 | 数值 | 出处 | 备注 |
|---|---|---|---|
| e_rx（核电嵌入能） | 4.5 MWh_e-eq/kWe | Lenzen 2008（轻水堆中点，Table 5） | 代码注释另提及 "IAEA 2018 INPRO update"，具体文号建议作者确认后再决定是否加引 |
| e_ng（NGCC 嵌入能） | 1.0 MWh_e-eq/kWe | 代码注释记为 NLR ATB 2024 LCI screening value → 正文引 ATB 2024（已有键 `atb2024nuclear`） | 屏查值 |
| w_rx（核电塔冷耗水） | 2.54 L/kWh_e | Macknick et al. 2012（recirculating tower 中位数；`data/environmental/water_intensity_macknick.yaml` 记录 2,546 L/MWh） | |
| w_ng（NGCC 塔冷耗水） | 0.78 L/kWh_e | Macknick et al. 2012 中位数 | yaml 里另有 754 L/MWh 一档；实现取 0.78 L/kWh |
| w_g（ERCOT 混合电） | 1.42 L/kWh_e | Macknick 2012 因子按 ERCOT 电源结构加权 | |
| w_v（VCC 场址耗水） | 0.10 L/kWh_c | 作者估计（Macknick 只覆盖发电侧） | 注明 authors' estimate |
| w_a（吸收式场址耗水） | 0.183 L/kWh_c | = 0.10 × (1 + 1/COP_a)，COP_a≈1.2（Houston 年均） | 推导写入 Note 7 正文 |
| f_sc（流域稀缺因子） | 0.65（世界均值 1.0） | WRI Aqueduct 4.0（基线水压力）与 AWARE（Boulay et al. 2018）的保守中点 | |
| 水价（memo） | 0.50 $/m³ | TWDB 2024 得州工业水价中点（作者估计） | 不进 TAC |

## 3. 新增 BibTeX（references.bib 中尚不存在）

已核对现有 `references.bib`（43 条）：`atb2024nuclear`、`li2026nuclearH2` 已在，直接复用；
以下四条为新增。DOI 均为正式出版物 DOI；Aqueduct 技术说明以 URL 为准（其 DOI 请在
最终定稿时于 WRI 页面核对一次）。

```bibtex
@article{lenzen2008nuclear,
  title   = {Life cycle energy and greenhouse gas emissions of nuclear energy: A review},
  author  = {Lenzen, Manfred},
  journal = {Energy Conversion and Management},
  volume  = {49},
  number  = {8},
  pages   = {2178--2199},
  year    = {2008},
  doi     = {10.1016/j.enconman.2008.01.033}
}

@article{macknick2012water,
  title   = {Operational water consumption and withdrawal factors for electricity generating technologies: a review of existing literature},
  author  = {Macknick, Jordan and Newmark, Robin and Heath, Garvin and Hallett, K. C.},
  journal = {Environmental Research Letters},
  volume  = {7},
  number  = {4},
  pages   = {045802},
  year    = {2012},
  doi     = {10.1088/1748-9326/7/4/045802}
}

@article{boulay2018aware,
  title   = {The WULCA consensus characterization model for water scarcity footprints: assessing impacts of water consumption based on available water remaining ({AWARE})},
  author  = {Boulay, Anne-Marie and Bare, Jane and Benini, Lorenzo and Berger, Markus and Lathuilli{\`e}re, Michael J. and Manzardo, Alessandro and Margni, Manuele and Motoshita, Masaharu and N{\'u}{\~n}ez, Montserrat and Pastor, Amandine Valerie and Ridoutt, Bradley and Oki, Taikan and Worbe, Sebastien and Pfister, Stephan},
  journal = {The International Journal of Life Cycle Assessment},
  volume  = {23},
  number  = {2},
  pages   = {368--378},
  year    = {2018},
  doi     = {10.1007/s11367-017-1333-8}
}

@techreport{wri2023aqueduct,
  title       = {Aqueduct 4.0: Updated decision-relevant global water risk indicators},
  author      = {Kuzma, Samantha and Bierkens, Marc F. P. and Lakshman, Shivani and Luo, Tianyi and Saccoccia, Liz and Sutanudjaja, Edwin H. and {Van Beek}, Rens},
  institution = {World Resources Institute},
  type        = {Technical Note},
  address     = {Washington, DC},
  year        = {2023},
  url         = {https://www.wri.org/research/aqueduct-40-updated-decision-relevant-global-water-risk-indicators}
}
```

## 4. 插入方式（供改稿端参考）

1. 将 `C6_supplementary_note.tex` 的正文部分插入 SI（按任务书第 11 节的位置约定），
   目录行：`\sitocline{Supplementary Note 7: Secondary endpoint definitions}{note:endpoints}`；
   SI 首段的 note 计数相应 +1。
2. 上述 4 条 BibTeX 追加进 `references.bib` 后重跑 `bibtex`。
3. 该 note 新增 1 个编号表（`tab:endpoint_factors`），置于 SI 末尾时自动顺延为下一个 S 表号，
   不影响既有 S1–S5 编号。
4. 本仓库内已用当前 main.tex 做过插入编译验证（pdflatex+bibtex 零 error、零未解析引用），
   见 report.md §C6。
