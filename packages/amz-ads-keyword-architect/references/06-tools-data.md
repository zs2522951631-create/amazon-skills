# 工具映射与数据源

## 分工铁律

**Sorftime = 找词 + 评论正文 + 实时抓取**（强在获取）；**SIF = ABA 需求/竞争/竞品广告架构反查**（强在分析）。两者互补，找词用 Sorftime，分析词用 SIF。

---

## 工具映射表

| 环节 | 主用 | 备用 |
|---|---|---|
| 竞品画像/同类校验 | Sorftime `ProductRequest`/`ProductSearch` | SIF `market_get_asin_keyword_signals` |
| 竞品反查词 | Sorftime `ASINRequestKeywordv2` | — |
| 核心词拓展 | Sorftime `KeywordExtends`/`KeywordRequest` | — |
| **词根趋势** ⭐ | SIF `market_get_keyword_root_trend` | — |
| 搜索需求量化 | SIF `market_get_keyword_demand` | 卖家精灵 |
| 竞争度量化 | SIF `market_get_keyword_competition` | 卖家精灵 CPC |
| 词历史/季节性 | SIF `market_get_keyword_history`（含 top3 点击/转化集中度）| 选品指南针 |
| 词根市场盘子/长尾分散度 ⭐ | SIF `market_get_keyword_root_trend`（`coverage_ratio`）| — |
| 需求生命周期/时机 | SIF `market_get_keyword_demand`（trend/momentum/weeks_to_peak）| 选品指南针 |
| 竞品反查流量词（带健康度）| SIF `market_get_asin_keyword_signals` | Sorftime `ASINRequestKeywordv2` |
| 收录监控（变体词覆盖）| SIF `ops_get_listing_keyword_distribution` | — |
| **竞品广告架构反查** ⭐ | SIF `ads_get_asin_ad_structure` + `ads_get_ad_group_keyword_breakdown`（学竞品 ad group 分词）| — |
| 评论 VOC | Sorftime `ProductReviewsQuery` / `rufus-research` / `review-summarizer` | — |
| 分类/评分框架 | 本 skill `references/03-classification.md` + `references/06-tools-data.md`（自包含）| — |
| Excel 交付 | 本 skill `scripts/build_kw_architecture.py` | `xlsx` skill |
| 报告输出 | 单文件 HTML 报告模板 | — |

### 关键工具说明

- **`market_get_keyword_history`**：精确词搜了多少、排第几、谁拿走流量；关键字段 `volumes`/`ranks`/`top3_click_shares`/`top3_conversion_shares`（7年，1-10词对比）。
- **`market_get_keyword_root_trend`**：词根下整个市场多大、需求集中还是散在长尾；关键字段 `ext_search_volumes`（词根综合量）/`coverage_ratio`（>0.8 集中精确词；<0.4 散在长尾须系统铺长尾）。
- **`market_get_keyword_demand`**：在涨还是跌、现在该进还是等；关键字段 `trend.direction`/`momentum`/`seasonality.peak_months`/`weeks_to_peak`/`action`。
- **`market_get_keyword_competition`**：直接给①可进入性/可沉淀性/可持续性三维评估 ②`competition_position`（dominant/defending/advancing/stalled/opportunity/blocked/displaced）③差异化 angle + 替代路径。
- **`market_get_asin_keyword_signals`**：竞品反查流量词（带健康度），辅助确认竞品是否真在该词上布局（佐证相关）。
- **`ads_get_asin_ad_structure`**：看竞品 SP/SB/SBV campaign 规模与类型分布。
- **`ads_get_ad_group_keyword_breakdown`**：看竞品每个 ad group 怎么分词、组内流量占比，作为设计自己 ad group 主题的实证锚点。
- **`ops_get_listing_keyword_distribution`**：收录监控，变体词覆盖情况。
- **Sorftime `ProductRequest`**：抓**本品/竞品 Listing 与规格**——标题、品牌、类目、`Property`（规格 spec：功率/供电方式/尺寸/光谱/调光/安装方式/材质/认证等）、`Description`（含五点 bullets）、`VariationASIN` + `Attribute`（变体）、`Feature`（买家维度评分）、星级分布。**本品 spec / 必含 / 必排属性默认用本工具自抓填充 Step 0 锚点，不需用户手填**；A+ 图片内文案才需 OCR/手动补。竞品同款用它做同类校验。
- **Sorftime `ASINRequestKeywordv2`**：竞品反查词，量大（单 ASIN 常 300–1000+ 词），须控量，见下「大词池反查控量」；并按反查 ASIN 同类占比过滤噪声。
- **Sorftime `KeywordExtends`**：核心词拓展。
- **Sorftime `ProductReviewsQuery`**：拉评论正文（已收录免费/实时耗积分），VOC 首选；返回 `Content`/`Star`/`Title`/`AsinProperty`（变体）/`ItemIndex`（如 5/746 表总量）；评论语言属于「需求语言」非「搜索语言」，须映射成标准搜索表达再入词池。**注意按变体区分**：返回的评论可能来自不同 `Asin`（变体），描述的功能（如带遥控的变体）不一定是本 ASIN 的属性，回填 VOC/边界时以本 ASIN 的 `Property` 为准。

---

## 大词池反查控量（竞品反查词数据量大时）

单个竞品反查常返回 300–1000+ 词（`market_get_asin_keyword_signals` 的 `total_keywords_in_period` 可达千级），全量深拉会爆上下文。按以下顺序控量，**不要无脑全量拉**：

1. **先用 `topN` 卡上限**：`market_get_asin_keyword_signals` 的 `topN` 默认 50、最大 300。本品 / 1 个主竞品深拉（topN 60–80 取全指标），其余竞品浅拉（topN 20）只取头部词。
2. **按 `traffic_share` 截断**：排到 ~50 名后每词贡献通常 <0.5%，长尾靠 `market_get_keyword_root_trend` 的词根综合量补，不必逐个深挖。
3. **用工具自带的分层返回**：先看 `primary_signals`（declining/gaining/rank_gaps 各 top3，已是高价值词）+ `secondary_signals`（只给词名 + `hint`、不含全量指标，廉价拿词名）；**只对进入候选的词再补** `market_get_keyword_demand` / `market_get_keyword_competition`。
4. **多竞品先并集去重词名，再筛**：合并各竞品词名去重后，只对高 `traffic_share` / `keyword_health=at_risk` / 与本品锚点相关的词补深度指标。
5. **按 `keyword_health` 过滤**：`core` / `volatile` / `at_risk` 优先看；`standard` 长尾批量归簇即可。

> 原则：**词名要广（并集去重），深拉要窄（只对候选词补指标）**。不要为「数据完整」把每个竞品都 topN=300 全拉。

| 情况 | 处理方式 |
|---|---|
| 用户提供 ABA / 选品指南针导出 | 直接读取，以 ABA 为锚（权威，带 SFR + top3 点击/转化份额） |
| 用户未提供 | 用 SIF `market_get_keyword_history`/`market_get_keyword_demand` + Sorftime `ASINRequestKeywordv2` 补；标注来源为「SIF/Sorftime 近似」 |

**缺口说明**：ABA 数据 + 选品指南针（商机探测器）是后台/卖家精灵导出，**无直接 MCP**，需手动提供或用 SIF/Sorftime/卖家精灵近似替代。VOC 实时采集（Sorftime `ProductReviewsQuery` 实时版）可能耗积分，跑前确认。

---

## 站点 domain 映射表

| 站点 | Sorftime domain 值 | 备注 |
|---|---|---|
| US（美国）| 1 | 默认站点 |
| UK（英国）| 2 | EU5 之一 |
| DE（德国）| 3 | EU5 之一，词根拆解需德语处理 |
| FR（法国）| 4 | EU5 之一，词根拆解需法语处理 |
| CA（加拿大）| 7 | 北美补充 |
| IT（意大利）| 8 | EU5 之一，词根拆解需意语处理 |
| ES（西班牙）| 9 | EU5 之一，词根拆解需西语处理 |

EU5 = UK / DE / FR / IT / ES，注意语言差异，词根拆解需按站点语言处理（v1 先英语 + 占位，DE/FR/IT/ES 标「待补语言包」）。

---

## 评分骨架（自包含）

### 100 分制

| 维度 | 分值 | 判断方式 |
|---|---:|---|
| 相关性 | 30 | 搜索该词的用户是否会购买本产品（主指标：反查 ASIN 同类占比 ≥70%/30-70%/<30%） |
| 搜索需求 | 20 | 搜索量、SFR、趋势；缺失则待补充 |
| 转化意图 | 20 | 是否包含明确属性、场景、痛点、型号、购买意图 |
| 竞争可攻性 | 15 | 竞品强度、排名难度、广告成本；缺失则待补充 |
| Listing 适配度 | 10 | 是否自然适合 Title、Bullets、A+、Backend ST |
| 广告可测性 | 5 | 是否适合用广告低成本验证 |

### Fallback：无数据或部分数据时

| 数据情况 | 评分方式 | 总分制 | 标注 |
|---|---|---|---|
| 完全无数据（只有关键词文本）| 只评相关性 30 + 转化意图 20 + Listing 适配度 10 + 广告可测性 5 | **65 分制** | `(语义评分,待数据验证)` |
| 部分数据（部分指标缺失）| 已有维度照算，缺失维度按该维度满分的 **60% 基础分**计算 | 100 分制 | `(部分待验证)` |
| 完整数据 | 正常评分 | 100 分制 | 无需特殊标注 |

### 分层标准

以 100 分制为基准，语义评分按等比例换算：

| 分层 | 100 分制 | 65 分制等比换算 | 含义 |
|---|---|---|---|
| 核心优先词 | 80-100 | 52-65 | 核心布局 |
| 重点测试词 | 60-79 | 39-51 | 优先测试 |
| 长尾覆盖词 | 40-59 | 26-38 | 长尾覆盖或 A+ 补充 |
| 观察词 | 20-39 | 13-25 | 暂不投放，持续观察 |
| 否定/排除 | 0-19 | 0-12 | 否定候选 |

> **铁律**：数值类指标（词频/SFR/CPC/份额/排名）只能来自工具取数，AI 不得编造；无数据时只做语义判断并标「待数据验证」。
