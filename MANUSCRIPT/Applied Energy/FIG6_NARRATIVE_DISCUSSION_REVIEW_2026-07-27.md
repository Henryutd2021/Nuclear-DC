# Applied Energy 稿件：Figure 6、核心叙事、Discussion 与吸收式冷机阈值审阅

日期：2026-07-27
审阅对象：`MANUSCRIPT/Applied Energy/main.tex` 与 `main.pdf`
审阅方式：只读检查稿件、PDF、Figure 6 源图、绘图代码、`master_kpi_table.csv` 和模型成本实现；未修改 `main.tex`、PDF 或任何正式图件。

## 总体结论

这篇文章当前并不缺结果，真正的问题是结果层级不够清楚。最值得保留和反复强化的主线只有四条：

1. 在 2023 ATB-Mid reactor CAPEX 下，Case 1 和 Case 2 都没有达到 grid parity。
2. Reactor CAPEX 是最主要的技术成本轴；在当前 Section 45Y 与 2023 市场条件下，平价区约从 \$5,000/kW$_e$ 开始，但该阈值明显依赖市场和出口价值。
3. Absorption cooling 的调度是合理的，却不是正的增量投资：它在高电价时运行并承担 38% 的年冷负荷，但基线下仍使 Case 2 比 Case 1 贵 \$9.2 million/yr。
4. Carbon pricing 是第二条、但更依赖记账约定的平价路径：Case 1 和 Case 2 分别约在 \$53 和 \$64/tCO$_2$ 达到 grid parity，前提是 merchant exports 按 ERCOT hourly average emission factor 获得排放抵扣。

Figure 6a 中的 53、64 和 165 基本正确；有问题的是把 53 与 64 的平均值画成“约 59 的 nuclear crossover”，以及由此产生的蓝色区域和最右侧区域文字。

当前稿没有直接给出“absorption-chiller CAPEX 降到多少时 Case 2 优于 Case 1”。在现有固定 160 MW$_c$ 容量、2023 ATB-Mid、PUE 1.35、WACC 6.7%、零碳价和 Section 45Y 口径下，这个阈值可由现有数据严格推出为约 **\$59.6/kW$_c$**，不需要新增小时级求解。

## 1. Figure 6a 数值与区域逻辑

### 1.1 四条曲线的来源

Panel a 使用 `outputs/master_kpi_table.csv` 中 G6 的三个已求解碳价点：0、50 和 100 USD/tCO$_2$。绘图代码使用 0 与 100 两端点构造直线，并把 100 以后的部分画成虚线外推。

令 $p$ 为 carbon price，TAC 单位为 M\$/yr，当前图中实际使用的端点直线为：

$$
\begin{aligned}
T_0(p)&=75.869050+0.362584674p,\\
T_1(p)&=113.370159-0.343631508p,\\
T_2(p)&=122.594196-0.366140679p,\\
T_3(p)&=55.576822+0.485855058p.
\end{aligned}
$$

对应的交点为：

| 交点 | 数值（USD/tCO$_2$） | 含义 |
|---|---:|---|
| Case 1 = Case 0 | 53.101 | SMR-only 达到 grid parity |
| Case 2 = Case 0 | 64.119 | SMR + absorption 达到 grid parity |
| Case 3 = Case 0 | 164.616 | NGCC 与 grid 相等；位于求解范围之外 |
| Case 1 = Case 3 | 69.674 | SMR-only 开始低于 NGCC |
| Case 2 = Case 3 | 78.659 | 两个 nuclear cases 此后都低于 NGCC |

正文把前两个值写成 53 和 64、把第三个写成约 165，数值上没有问题。

Case 2 虽然具有更负的净排放斜率，但它在零碳价时的 TAC 比 Case 1 高 \$9.224 million/yr，因此要到更高的碳价才达到 grid parity。

### 1.2 为什么“约 59”没有穿过任何交点

绘图代码没有求出一个新的物理或经济交点，而是直接计算：

$$
p_{\mathrm{mid}}
=\frac{53.101+64.119}{2}
=58.610
\rightarrow 59.
$$

这只是两个真实 crossover 的算术中点。它不会、也不应该穿过任何两条曲线的交点。

在 $p=58.610$ 时，各 case 的 TAC 为：

| Case | TAC（M\$/yr） |
|---|---:|
| Case 3, NGCC | 84.053 |
| Case 1, nuclear | 93.230 |
| Case 0, grid | 97.120 |
| Case 2, nuclear + absorption | 101.135 |

此时的排序是：

$$
C3<C1<C0<C2.
$$

也就是说，Case 1 已经比 grid 便宜，但 Case 2 仍然比 grid 贵。因此：

- “Nuclear ~59”不是一个有效 crossover；
- caption 即使披露了它是 53 和 64 的 midpoint，仍不应把它称为 singular “the nuclear crossover”；
- 53–64 恰好是一个有清楚经济意义的过渡区：**Case 1 已过平价，Case 2 尚未过平价**。当前图反而把这层信息压没了。

### 1.3 蓝色区域为何错误

当前蓝色区域从 58.610 开始，标签是 “Nuclear less than grid”。

这个起点无论按哪一种解释都不成立：

- 若意思是“至少一个 nuclear case 比 grid 便宜”，区域应从 53.101 开始；
- 若意思是“两个 nuclear cases 都比 grid 便宜”，区域应从 64.119 开始；
- 58.610 对两种解释都不正确。

此外：

- 53.101–58.610 区间中，Case 1 已经低于 grid，却没有被着色；
- 58.610–64.119 区间中，蓝色区域暗示两个 nuclear configurations 已低于 grid，但 Case 2 其实仍高于 grid。

因此这不是单纯的美学问题，而是 figure–caption 的逻辑不一致。

### 1.4 最右侧粉色区域是否有问题

需要区分两件事：

1. “Nuclear less than grid and NGCC” 在 $p>164.616$ 区域内是否为真？
2. 约 165 这条边界本身代表什么变化？

在 165 右侧，排序为：

$$
C1<C2<C0<C3.
$$

所以 “nuclear less than grid and NGCC” 在字面上确实为真。

但是，两个 nuclear cases 都低于 NGCC 的状态早在 Case 2 与 Case 3 于约 78.659 相交后就已经成立。约 165 处新发生的唯一变化是：

$$
\text{grid becomes cheaper than NGCC}.
$$

因此用户的直觉是正确的：**165 这条线真正表达的是 grid 与 NGCC 的排序反转，而不是 nuclear dominance 的开始。**

当前粉色起点与 caption 中 “NGCC is also more expensive than grid supply” 基本对应，但图内的 “Nuclear less than grid and NGCC” 没有解释这条边界的新增含义，容易让读者误以为 nuclear 相对 NGCC 的优势从 165 才开始。

建议将最右侧文字改为：

> Grid less than NGCC
> (linear extrapolation)

如果仍希望表达 combined ordering，可在 caption 中补一句：在该外推区间内，两种 nuclear configurations 仍低于二者；不要用这句话定义粉色区域。

### 1.5 完整分段排序

按当前图中采用的端点直线，TAC 从低到高的完整排序为：

| Carbon-price 区间（USD/tCO$_2$） | TAC 从低到高 |
|---|---|
| 0–53.101 | C3 < C0 < C1 < C2 |
| 53.101–64.119 | C3 < C1 < C0 < C2 |
| 64.119–69.674 | C3 < C1 < C2 < C0 |
| 69.674–78.659 | C1 < C3 < C2 < C0 |
| 78.659–164.616 | C1 < C2 < C3 < C0 |
| >164.616（图示至 250） | C1 < C2 < C0 < C3 |

这张表说明，若 Figure 6a 想表达完整的 case ranking，当前只标 59 和 165 远远不够；若它只想表达相对 grid 的 parity，则应只保留三个 case-versus-grid 交点，不要再给背景区域附加更强的多 case 排序含义。

### 1.6 Panel a 的其他问题

1. **53 和 64 是插值估计，不是直接求解点。**
   G6 只直接求解了 0、50 和 100。Caption 应明确 markers 是 solved cases，solid segments 是 interpolation。

2. **Case 2 不是严格线性。**
   端点直线在 $p=50$ 时给出 104.287 M\$/yr，实际求解值为 104.431 M\$/yr，相差 0.144 M\$/yr。按 50–100 两点局部插值，Case 2 crossover 为 64.260；三点拟合约为 64.185。都仍四舍五入为 64，因此正文整数结论不受影响，但图内实线最好直接连接三个实际点。

3. **外推区域视觉上仍过于确定。**
   100–250 全部不是直接求解结果。虚线已经比旧版诚实，但背景色仍和求解区同样连续。可对外推区加斜线、降低饱和度，或把横轴收缩到约 180。

4. **Case 2 的直接标签不完整。**
   `C2 absorption` 容易被读成独立吸收式制冷方案，建议改为 `C2 nuclear + absorption` 或 `C2 SMR + absorption`。

5. **两个绘图入口都保留了同一错误。**
   `notebooks/paper_figures.ipynb` 与较新的 `submission_audit/scripts/make_fig6b_rev.py` 都仍使用 53/64 的平均值和相同区域文字。只改一个入口会在日后重绘时回退。

### 1.7 Figure 6a 的推荐重画方式

最清晰的设计是把 y 轴改为相对 grid 的成本差：

$$
\Delta T_i(p)=T_i(p)-T_0(p).
$$

Case 0 变成水平零线，Case 1、Case 2 和 Case 3 分别在 53.1、64.1 和 164.6 穿过零线。这样完全不需要“约 59”或含糊的区域标签。

若保留绝对 TAC 图，最低限度应：

- 删除 `Nuclear ~59`；
- 分别在 53.1 和 64.1 画线并标注 `C1 = grid`、`C2 = grid`；
- 把 53.1–64.1 标成 `Only C1 < grid`；
- 从 64.1 起用蓝色表示 `Both nuclear cases < grid`；
- 从 165 起叠加粉色斜线，而不是用粉色替代蓝色；
- 将粉色文字改为 `Grid < NGCC (extrapolated)`；
- 不再使用 `Nuclear less than grid and NGCC` 定义 165 右侧。

可直接使用的 caption 核心文本为：

> (a) TAC as a function of carbon price. Markers denote solved cases at \$0, \$50 and \$100 tCO$_2^{-1}$; solid segments interpolate between solved points, and dashed segments are linear extrapolations beyond \$100 tCO$_2^{-1}$. Cases 1 and 2 reach parity with grid-only Case 0 at approximately \$53.1 and \$64.1 tCO$_2^{-1}$, respectively. Case 3 remains less expensive than Case 0 throughout the sampled range; their extrapolated crossover occurs at approximately \$164.6 tCO$_2^{-1}$, beyond which grid supply is less expensive than on-site NGCC. Carbon costs and merchant-export credits use the ERCOT hourly average emission factor.

## 2. 文章最核心的观点与推荐论证路线

### 2.1 四个 load-bearing conclusions

#### 结论 A：ATB-Mid 基线下，nuclear 不平价

在 2023 ATB-Mid 下，Case 1 和 Case 2 的 TAC 分别为 \$113.4 和 \$122.6 million/yr，对比 grid 的 \$75.9 million/yr；即使有 Section 45Y，仍分别贵 49% 和 62%。

这是文章的 baseline falsification：当前中档 reactor CAPEX 并不能支持“核电 + data center 天然有经济性”的笼统判断。

#### 结论 B：Reactor CAPEX 是主要技术成本轴，但阈值是 market-specific

在当前政策与 2023 市场下，约 \$5,000/kW$_e$ 是 Case 2 的 grid-parity 区域；absorption CAPEX 的完整文献区间只移动约 13 percentage points，而 reactor CAPEX 轴移动数百 points。

但是该 \$5,000/kW$_e$ 不能写成普适常数。2024 的低电价环境使 NOAK Case 2 仍比 grid 贵 34%。更稳妥的表述是：

> Reactor CAPEX is the dominant technology-cost axis, while market and export value determine where the parity boundary lies.

#### 结论 C：Absorption cooling 是“会被调度”，不是“创造净投资价值”

Absorber 会在高价小时运行并承担 38% 年冷负荷，说明优化结果有合理的调度机制；但它的资本成本、steam opportunity cost 和 forgone PTC 超过 avoided VCC electricity，使 Case 2 基线下仍比 Case 1 贵 \$9.2 million/yr。

这是文章最有概念价值的结论：**operational utilization 不等于 positive investment value。**

#### 结论 D：Carbon price 是 conditional second pathway

ATB-Mid 下，Case 1 和 Case 2 分别在约 \$53 和 \$64/tCO$_2$ 达到 grid parity，但这个结论依赖 merchant-export emission credit。它应被表述为一种 accounting-dependent policy pathway，而不是与 reactor cost learning 同样稳健的技术路径。

### 2.2 推荐把整篇文章组织成三个问题

1. **基线是否成立？**
   答案：ATB-Mid 下不成立；Case 2 还比 Case 1 更贵。

2. **为什么 absorption 会运行却不赚钱？**
   答案：高价小时的电力替代价值存在，但不足以覆盖 absorber CAPEX、lost turbine output 和 forgone PTC。

3. **什么条件真正改变结论？**
   答案：reactor CAPEX、market/export value 和 policy 改变 parity boundary；PUE、absorption CAPEX、size matching、financing 和 BESS 多数只改变距离或在特定交互下起作用。

结果部分可据此压成四个 subsection：

1. Baseline economics: ATB-Mid nuclear is not at parity
2. Absorption cooling: rational dispatch, negative incremental value
3. Competitiveness boundary: reactor capital and market value
4. Conditional policy pathway: carbon pricing under export crediting

### 2.3 当前叙事中的几处不一致

1. **Discussion 说 secondary factors “without moving the boundary”，但 market year 和 carbon price 明显会移动或穿过边界。**
   建议改成：这些因素改变边界的位置，但不改变 driver hierarchy。

2. **Conclusion 说 PTC 在 NOAK 下“brings both nuclear cases below grid cost”，与 Results 冲突。**
   Results 已给出无 PTC 时 NOAK 的 pre-credit margins 为 +32% 和 +22%。正确因果应是：两者在 2023 NOAK 下无 PTC 已低于 grid，PTC 只是扩大优势。

3. **Conclusion 把“load large enough”列为必须同时满足的条件，但稿件没有求出一个 minimum-load parity threshold。**
   Size sweep 只证明 load matching 有帮助但不充分。可改为 `adequate on-site utilization or remunerated export capability`，或补做真正的 load-size boundary。

4. **“109% cheaper”不宜进入普通语言。**
   Margin 大于 100% 意味着 net TAC 已为负，普通意义上的“便宜 109%”不可解释。应写 `grid-cost margin of +109%`，或直接报告 negative net TAC / net revenue。

5. **Abstract 把约 \$5,000/kW$_e$ 的 parity threshold 与 \$2,250/kW$_e$ 的 NOAK endpoint 放在同一句。**
   建议分开，或只保留 threshold，把 NOAK 多年份端点移出 abstract。

6. **Discussion 把 absorption 称为 “rather than a source of value” 过于绝对。**
   当前模型只证明它在 baseline 条件下没有带来净成本节约；PUE 1.50 与低 absorber CAPEX 的组合已经表明其增量价值可以转正。建议改为 `does not provide net cost savings under the baseline assumptions`。

7. **Limitations 声称局限性 “without altering the ordering of the configurations” 缺少证据。**
   负荷形状、边际排放因子、碳价传导和 reliability/backup cost 都可能改变配置排序，而不只是改变 margin。建议改为 `may shift the quantitative margins and, in some cases, the ordering`。

8. **Conclusion 说 absorption 可因 “operational reasons” 被选择，但模型没有量化这些额外收益。**
   若不补充 resilience、water、capacity relief 或其他 operational-value 指标，应删去这句话，或明确写成稿件范围之外的可能性，而不是本研究结论。

## 3. 可以压缩或移入 Supplementary Information 的内容

### 3.1 建议保留在主文

- Figure 1 和 case-definition table：读者必须理解四个 cases。
- Baseline TAC 与 Case 1/2 相对 grid 的差距。
- Absorption price-responsive dispatch 的机制。
- Case 2 minus Case 1 的净值和最主要成本机制。
- Reactor-capital boundary、约 \$5,000/kW$_e$ 的条件性阈值。
- \$53/\$64 carbon-price crossovers 与 export-credit caveat。
- Figure 6b 对 driver hierarchy 的总结，但最好同时显示 absolute TAC 与 normalized margin。

### 3.2 建议压缩或移入 SI

| 当前内容 | 建议 |
|---|---|
| Introduction 的 paper-roadmap 段落 | 删除 |
| Figure 2 input traces | 页面紧张时移 SI |
| Methods 中完整 equipment cost / lifetime / technical tables | 主文留一个 key-assumptions table，其余移 SI |
| 109-run scenario ledger | 移 SI，主文只列 major axes |
| Size-matching 的全部 export、intensity 和每个倍率数字 | 主文留一句“2× 接近平衡但仍不平价”，其余已有 SI |
| NLCS、EPBT、water secondary endpoints | 移 SI；除非 water trade-off 要成为核心贡献 |
| January/July 的全部局部数字与 26 MW turbine detail | 图注或 SI |
| Waterfall 六个分项逐项复述 | 主文只写 avoided electricity、combined offsets 和 net \$9.2 million |
| PUE 独立 subsection | 合并进 absorption subsection，详细点值留 SI |
| BESS 独立段落 | 移 SI；主文只在 global ranking 中体现 |
| Market-year 的全部 gas/LMP/percentage endpoint | 主文保留高价年与低价年的方向和一个反例 |
| Reactor CAPEX × market year 的完整数字矩阵 | 移 SI，主文留 threshold 与 market-specific caveat |
| WACC 的完整 endpoint 数字 | 压成一句，或移 SI |
| Discussion 中 PTC re-levelization 的六个数字 | 主文保留方向与“结论不变”，详细值移 SI |

一个现实的目标是主文减少约 1,500–2,000 words，而不删除任何证据，只改变证据所在层级。

### 3.3 Abstract / Highlights 应只保留的数字

Abstract 建议最多保留四组数字：

1. ATB-Mid baseline gap；
2. conditional \$5,000/kW$_e$ threshold；
3. Case 2 minus Case 1 的 \$9.2 million/yr；
4. \$53/\$64 carbon-price pathway。

2022/2024 的全部 NOAK endpoint、13-point absorber span 和多组 percentage margins 可移出 abstract。

如果把新增 absorber threshold 纳入稿件，候选 highlights 可写为：

- Reactor capital is the dominant technology-cost lever for SMR parity.
- Under 2023 prices and Section 45Y, parity begins near \$5,000/kW$_e$.
- Carbon pricing closes the mid-range gap at \$53–64/t under export crediting.
- Absorption supplies 38% of cooling but adds \$9.2M/yr at baseline.
- Case 2 beats Case 1 only below about \$60/kW$_c$ at baseline PUE.

这些句子均在 Applied Energy 的 85-character highlight 上限附近或以内；最终提交前应按纯文本字符再次检查。

## 4. Discussion 与 Conclusion：合并还是分开

### 4.1 判断

建议**继续分开**，但大幅去重。

Applied Energy 当前 Guide for Authors 允许 conclusion 独立成节，也允许作为 Discussion 或 Results and Discussion 的 subsection；因此格式上两种都可行。当前稿的主要问题不是多了一个标题，而是 Discussion 前三段重复 Results，Conclusion 又重复 Abstract、Results 和 Discussion。

继续分开的好处是：

- Discussion 可承担机制解释、与既有研究的关系、external validity 和 limitations；
- Conclusion 可作为 150–180 words 的干净 decision rule；
- 对 Applied Energy 读者而言，独立 Conclusion 更便于快速定位。

只有在严格页数压力下，才建议合并为 `Discussion and conclusions`；即使合并，也应保留最后一个明显的 concluding paragraph。

### 4.2 推荐字数与结构

当前 `texcount` 约为：

- Discussion：835 words；
- Conclusion：333 words；
- 合计：1,168 words。

建议目标：

- Discussion：约 500–550 words；
- Conclusion：约 160–180 words；
- 合计：约 680–730 words。

总量可减少约 38–42%。

推荐 Discussion 只保留四段：

1. **Primary interpretation**：fixed capital 与 market/export value 为什么主导，\$5,000 阈值为什么是条件性的。
2. **Absorption insight**：为什么“被调度”仍不等于“值得投资”，及其对 waste-heat literature 的修正。
3. **Policy and procurement**：cost-learning 路径与 carbon-price 路径的稳健性差异。
4. **Prioritized limitations**：只保留会实质移动边界的限制，包括 export-emission factor、carbon-price pass-through、单一 load/climate、reliability/backup 和 PTC levelization。

Conclusion 只需一段，并只做三件事：

1. 回答 2023 ATB-Mid baseline；
2. 给出 conditional capital boundary 与 carbon pathway；
3. 说明 absorption 不是 viability driver，并给出可迁移的 decision rule。

不要在 Conclusion 再完整列出 FOAK、NOAK、2022、2024、PUE、BESS、size 和全部百分比。

## 5. Case 2 何时因 absorption CAPEX 下降而优于 Case 1

### 5.1 当前稿有没有展示

没有直接展示。

当前稿提供了三类相关证据：

- Figure 4c / Results 给出基线 Case 2 minus Case 1 = +\$9.224 million/yr；
- PUE sweep 给出 Case 2 minus Case 1 随电制冷效率的变化；
- Figure 5d / G5 改变 absorption CAPEX，但输出指标是 Case 2 versus Case 0/grid，而不是 Case 2 versus Case 1。

因此读者能知道“基线下 absorption 不赚钱”，却看不到“需要便宜到什么程度才赚钱”。

### 5.2 基线阈值可由现有数据严格推出

在当前模型中：

- absorption nameplate 固定为 160 MW$_c$；
- absorption CAPEX 仅作为固定、dispatch-neutral 的 annualized term 进入 objective；
- 25-year CRF at 6.7% 为 0.08350436；
- Case 1 的 baseline TAC 为 113.370159 M\$/yr；
- Case 2 的 G5 TAC 与 CAPEX 完全线性。

G5 的 ATB-Mid 行为：

| Absorption CAPEX（USD/kW$_c$） | Case 2 TAC（M\$/yr） |
|---:|---:|
| 450 | 118.585986 |
| 600 | 120.590091 |
| 750 | 122.594196 |
| 900 | 124.598300 |
| 1,200 | 128.606510 |

因此：

$$
T_2(C_a)
=112.573673+0.013360697C_a
\quad \text{M\$/yr},
$$

其中 $C_a$ 的单位为 USD/kW$_c$。

令 $T_2(C_a)=T_1$：

$$
C_a^*
=750-\frac{9{,}224{,}036}
{160{,}000\times0.08350436}
=59.614\ \mathrm{USD\,kW_c^{-1}}.
$$

所以在这组基线假设下：

- 当 absorption CAPEX **低于约 \$59.6/kW$_c$** 时，Case 2 才开始优于 Case 1；
- 该阈值比 \$750 baseline 低 92.1%；
- 比 G5 的 \$450 Bare-Low 下限还低 86.8%；
- 即使 CAPEX 降到 \$450，Case 2 仍比 Case 1 贵约 \$5.216 million/yr；
- 即使 CAPEX 为零，Case 2 也只比 Case 1 便宜约 \$0.796 million/yr。

这说明基线问题不是简单的“设备稍微便宜一点”即可解决；CAPEX、fixed O&M、steam opportunity cost 和 forgone PTC 共同决定增量净值。

### 5.3 这个阈值具有多大意义

意义很大，因为它把当前较模糊的结论：

> absorption capital is not the viability driver

转化为可直接用于采购判断的结论：

> 在高效 VCC 的 2023 基线下，即使 absorber 降到现有文献最低成本的约七分之一，Case 2 才刚刚优于 Case 1。

它也补齐了 Introduction 提出的 `when absorption cooling earns its capital`，而当前 G5 实际只回答 Case 2 何时优于 grid。

但是必须明确，这个 \$59.6/kW$_c$ 是：

- fixed 160 MW$_c$ nameplate；
- baseline PUE 1.35；
- 2023 prices；
- WACC 6.7%；
- zero carbon price；
- Section 45Y；
- fixed dispatch physics；

下的条件性阈值，不能写成技术的普适 break-even cost。

### 5.4 现有 PUE 数据已经揭示一个更有价值的交互

因为 CAPEX 轴是线性的，可以把已有 PUE 求解结果解析地平移到其他 CAPEX，无需为每个 CAPEX 重跑：

| Full-load PUE | 在 \$750/kW$_c$ 时 Case 2 − Case 1（M\$/yr） | Implied break-even CAPEX（USD/kW$_c$） |
|---:|---:|---:|
| 1.10 | +13.221 | −239.5 |
| 1.30 | +11.035 | −75.9 |
| 1.35 baseline | +9.224 | 59.6 |
| 1.50 | +2.353 | 573.9 |

负阈值意味着：在 PUE 1.10 或 1.30 下，即使 absorber 免费，Case 2 也仍不能优于 Case 1，因为 fixed O&M 和 operating opportunity costs 已超过节省。

在 PUE 1.50 时，threshold 上升到约 \$574/kW$_c$，落入 \$450–1,200 的 tested literature range。这个结果支持一个比“absorption 总是不赚钱”更准确的结论：

> Absorption is uneconomic for the efficient baseline campus, but a low-cost absorber can become incrementally valuable when the competing electric-cooling system is sufficiently inefficient.

例如，在 PUE 1.50、absorber CAPEX 为 \$450/kW$_c$ 时，解析平移给出 Case 2 比 Case 1 约便宜 \$1.65 million/yr。这个结论仍应标为 model-implied：在 baseline \$59.6/kW$_c$ 阈值附近，当前 \$20/kW$_c$-yr fixed O\&M 已相当于设备 CAPEX 的约 34%/yr，说明该阈值远离现有成本证据范围，外推时不能只讨论 CAPEX 而忽略 O\&M 假设。

### 5.5 是否需要新增实验

#### 不需要新增求解的部分

若目标只是报告 baseline \$59.6/kW$_c$，不需要新增 Gurobi run。现有五个 G5 点已经证明 CAPEX 关系在浮点精度内完全线性，模型代码也表明 CAPEX 是固定加项。

若目标是展示已测试 PUE 点下的 CAPEX thresholds，也不需要新增二维 grid。可以用已有四个 PUE 结果加解析 CAPEX 平移。

#### 真正值得新增的实验

如果要把 `when does absorption pay?` 提升为文章的一项主要贡献，最值得做的不是再扫更多纯 CAPEX，而是：

1. **Endogenous absorption sizing / install decision**
   当前 Case 2 强制安装 160 MW$_c$ absorber 和完整 backup VCC。应允许 absorber size 在 0–160 MW$_c$ 内优化，或允许不安装。这样可以回答“小型 absorber 是否只捕捉最有价值的高价小时并在当前 \$750/kW$_c$ 下盈利”。这是比固定大机组的 CAPEX threshold 更真实的采购问题。

2. **Denser PUE operating sweep, CAPEX axis analytically reconstructed**
   如果需要平滑的 PUE–CAPEX zero contour，只需用 Gurobi 加密 PUE 轴，例如 1.30–1.65 每 0.05 一点；不需要为每个 CAPEX 重复小时求解。

3. **可选的 extraction-penalty interaction**
   若 absorption technology/design 是主要卖点，可进一步做 $\alpha_w$–CAPEX 或 PUE–$\alpha_w$ 边界；但不建议同时把所有交互塞回主文。

### 5.6 推荐展示方式

最简方案是在 Results 或 Discussion 增加一句：

> At the baseline PUE and fixed 160 MW$_c$ absorber size, Case 2 would undercut Case 1 only below an absorption CAPEX of approximately \$60 kW$_c^{-1}$, far below the tested \$450–1,200 kW$_c^{-1}$ range.

更完整但仍简洁的方案是在 Supplementary Figure 中画：

- x-axis：absorption CAPEX；
- y-axis：$\Delta TAC=TAC_2-TAC_1$；
- 四条线：PUE 1.10、1.30、1.35、1.50；
- horizontal zero line；
- shaded literature range \$450–1,200/kW$_c$；
- 标出 baseline threshold \$60 和 PUE 1.50 threshold \$574。

如果 absorption cooling 是文章的核心 novelty，可将这一小图作为 Figure 4c 的 inset，或用它替换部分重复的 PUE prose；不建议再增加一张大型主文 atlas。

### 5.7 单位命名需要统一

稿件将 absorption CAPEX 报告为 USD/kW$_c$，但代码和 CSV 字段名仍是 `absorption_capex_usd_per_kWth`，容量字段也叫 `absorption_capacity_MWth`。模型实际把它当作 cooling nameplate 使用。建议在下一轮改稿时统一成 kW$_c$/MW$_c$，或至少在 provenance note 中解释，避免读者误解为 generator heat-input basis。

## 6. 额外发现的两个提交前问题

### 6.1 `main.tex` 与 `main.pdf` 不是同一完整编译状态

文件时间显示：

- `main.pdf`：2026-07-27 17:31；
- `main.tex`：2026-07-27 17:33。

所提供 PDF 中大量 citation 显示为 `[?]`。用当前 source 在独立 build/output 目录执行完整 `latexmk` 后，citations 可以解析，生成 33 个 physical pages；所提供 PDF 为 31 pages。

因此后续正式审阅或提交前应重新执行完整 BibTeX/LaTeX build，并确认交付 PDF 与 source 同步。

### 6.2 Gurobi 句后的 `%` 注释掉了剩余内容

`main.tex` 当前写成：

```tex
... solved with Gurobi 13.0.%, using the barrier method ...
```

LaTeX 从 `%` 起注释掉该源文件行的其余内容。因此 solver method、optimality-gap tolerance、run count 和 fresh re-solve gap 均没有出现在 PDF 中。

应删除这个 `%`，或在它前面真正换行并确认想保留的文字。

## 7. 优先级建议

### Priority 1：必须修

1. 删除 Figure 6a 的 `Nuclear ~59`，分别显示 53 与 64。
2. 修正蓝色区域起点和语义。
3. 将 165 右侧文字改为 `Grid < NGCC (extrapolated)`。
4. 同步修改两个绘图入口，避免重绘回退。
5. 重新完整编译 PDF，解决 `[?]` citations。
6. 删除 `Gurobi 13.0.%` 中误用的 `%`。

### Priority 2：强烈建议

1. 将全文主线压成四个 load-bearing conclusions。
2. Discussion 与 Conclusion 保留分开，但合计压缩约 40%。
3. 修正 PTC 在 NOAK 下的因果表述。
4. 删除没有求解支撑的 “load large enough must coincide”。
5. 避免普通语言中的 “109% cheaper”。
6. 在主文增加 baseline absorption break-even CAPEX 约 \$60/kW$_c$ 的一句话。

### Priority 3：可选增强

1. 用现有 PUE 数据制作 $\Delta TAC_{2-1}$ versus absorber CAPEX 小图。
2. 若要真正强化 absorption contribution，再做 endogenous sizing / install decision。
3. 把 input figure、scenario ledger、BESS、secondary endpoints 和大部分逐点 sensitivity 数字移入 SI。

## 8. 主要证据位置

- `MANUSCRIPT/Applied Energy/main.tex`：Figure 6 results/caption 位于约 lines 653–669；Discussion/Conclusion 位于约 lines 673–698。
- `notebooks/paper_figures.ipynb`：约 lines 1935–1990 构造四条曲线、53/64 平均值和背景区域。
- `submission_audit/scripts/make_fig6b_rev.py`：较新绘图入口仍复用了同一 midpoint/region 逻辑。
- `outputs/master_kpi_table.csv`：G6 carbon-price rows 和 G5 ATB-Mid absorption-CAPEX rows。
- `src/milp/builder.py`：absorption CAPEX annualization 位于约 lines 463–473。
- `config/plant_case2.yaml`：160 MW$_c$ fixed capacity、\$750/kW$_c$ baseline、25-year life 和 fixed O&M。
- Applied Energy Guide for Authors：Discussion 应解释意义而不重复结果；Conclusion 可独立，也可作为 Discussion/Results and Discussion 的 subsection。
  <https://www.sciencedirect.com/journal/applied-energy/publish/guide-for-authors>
