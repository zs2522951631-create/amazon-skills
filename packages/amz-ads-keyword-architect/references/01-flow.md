# 八步流程详解

---

## 流程总览（含否词旁路）

```
Step 0  锚点：本品 spec + 竞品同类校验 + 必含/必排属性 + 类目门 + ASIN 回显确认
Step 1  多源采集：ABA / 竞品反查 / 选品指南针 / VOC，按源打标签+置信度，以 ABA 为锚
Step 2  归一化+拆解：lemmatize、停用词、单复数、保留错拼、n-gram 词根
Step 3  需求量化：TF-IDF 词频 + ABA SFR + SIF 需求三层（history/root_trend/demand）  ← 机会维，≠ 相关性
Step 4  双维打分：相关性（语义+反查 ASIN 同类占比）× 搜索需求 × 意图明确度
Step 5  属性多维拆解：品牌/品类/属性/场景痛点/人群/适配/否词（7 类优先级链）
Step 6  语义聚类：归成 ad group 投放主题簇 + 跨 ASIN 覆盖率 + coverage_ratio 决策
Step 7  广告架构分级：相关性×搜索量×竞争/CPC×趋势 → campaign/adgroup/匹配/预算/攻守测
          ↘ 否词池（贯穿 Step 0–7 全程持续沉淀）
Step 8  输出 + 回流校验出口
```

---

## Step 0 · 锚点建立

**输入**：用户提供的本品说明、竞品 ASIN、站点、类目。

**动作**：
1. 建立本品锚点表（材质/规格/型号/形态/适用对象/必含属性/必排属性/竞品同类校验/站点）。
2. 触发类目门：若用户未指定具体类目，主动弹提示确认是否用通用默认阈值。
3. **ASIN 回显确认**：原文回显竞品 ASIN 串让用户确认，防止 ASIN 串行/错位。
4. 竞品 ASIN < 3 个先要求补足；类目/形态明显不一致先提示确认，不混在一起拓词。

**用哪个工具**：Sorftime `ProductRequest`/`ProductSearch` 核实竞品同类；SIF `market_get_asin_keyword_signals` 辅助。

**输出**：锚点表（含必含属性、必排属性、否词种子池初始化）。

**易错点**：锚点未填就开拓词，导致相关性和否词判断无参照系；ASIN 串错导致整轮数据跑偏。

---

## Step 1 · 多源采集（带置信度，以 ABA 为锚）

**输入**：竞品 ASIN、ABA 导出（若有）、选品指南针导出（若有）。

**动作**：按源打标签 + 置信度加权，不同源简单合并会让噪声稀释权威源。

| 来源 | 性质 | 置信度 | 特别处理 |
|---|---|---|---|
| ABA（亚马逊官方搜索词）| 权威，带 SFR + top3 点击/转化份额 | 最高 | 作为锚点 |
| 选品指南针 / 商机探测器 | 趋势 / 季节性 / 机会 | 高 | 提供时间维 |
| 竞品反查词（第三方工具）| 量大但有噪声 | 中 | 按反查 ASIN 同类占比过滤 |
| 评论 VOC | **「需求语言」非「搜索语言」** | 中（需转化）| Sorftime `ProductReviewsQuery` 拉评论正文；先映射成标准搜索表达再入池，不直接投 |

**用哪个工具**：Sorftime `ASINRequestKeywordv2`（竞品反查）、Sorftime `KeywordExtends`（拓词）、Sorftime `ProductReviewsQuery`（VOC）；若用户有 ABA/指南针导出则直接读取。

**输出**：原始词表（带来源标签 + 置信度权重）。

**易错点**：遗漏 VOC 转化步骤（评论词直接入池，搜索匹配率低）；忽略置信度差异直接合并。

---

## Step 2 · 归一化 + 词根 / n-gram 拆解

**输入**：Step 1 原始词表。

**动作**：
- lowercasing、词形还原（lemmatize）、单复数合并、停用词过滤（for/with/the）。
- **保留**错拼与缩写（用户真实搜索行为）。
- n-gram 词根：`noise cancelling` 当一个 bigram 处理，不拆成 noise + cancelling。
- 建议用传统 NLP（spaCy/NLTK）做这步，确定性强、可复现。

**用哪个工具**：传统 NLP 脚本（非 LLM，确保可复现）。

**输出**：归一化词根表（带原始词形映射）。

**易错点**：过度归一化丢掉错拼（高频错拼也有搜索流量）；n-gram 拆开导致后续匹配方式错误。

---

## Step 3 · 需求量化（机会维，≠ 相关性）

> 🔴 **核心修正**：**词频 ≠ 相关性**。高频词根多是泛大词（烧钱重灾区），高转化长尾常低频。

**输入**：Step 2 归一化词根表。

**动作**：
- 池内相对热度用 **TF-IDF**（抑制停用词/品类词虚高），不用裸词频。
- 绝对需求用 **ABA SFR（搜索频率排名）** 为主指标。
- 叠加 SIF 需求三层（`market_get_keyword_history` / `market_get_keyword_root_trend` / `market_get_keyword_demand`）。
- 叠加趋势：上升 / 平稳 / 衰退 / 季节性。

**用哪个工具**：SIF `market_get_keyword_history`、`market_get_keyword_root_trend`（含 `coverage_ratio`）、`market_get_keyword_demand`；ABA 导出直接读取。

**输出**：词根表附需求档（高/中/低）、趋势标签、`coverage_ratio` 值。

**易错点**：用词频或搜索量代理相关性（最常见错误）；忘记记录 `coverage_ratio` 导致 Step 6 聚类无依据。

---

## Step 4 · 双维打分（相关性 × 需求 × 意图）

**输入**：Step 3 词根表（带需求数据）。

**动作**：对每个词根打相关性档（高/中/低）+ 意图明确度（泛需求/明确属性/解决方案长尾）。

- **相关性主指标**：反查 ASIN 同类占比（≥70% 高 / 30-70% 中 / <30% 低），fallback 纯语义。
- **意图**决定后续匹配方式。
- 套用 100 分制评分骨架（详见 `06-tools-data.md`）；无数据走 65 分语义制。

**用哪个工具**：LLM 批量打相关性 + 意图标；SIF `market_get_asin_keyword_signals` 辅助佐证竞品布局。

**输出**：词根表附相关性档 + 意图 + 初始评分。

**易错点**：把 top3_click_share / top3_conversion_share 当相关性（它们是竞争信号，0.6/0.3 是竞争集中度阈值，不是相关性）；相关性备注为空（违反 CHECKPOINT 1）。

---

## Step 5 · 属性多维拆解（7 类优先级链）

**输入**：Step 4 词根表。

**动作**：按优先级链对每个词根分类，只取一个最高优先级：

```
品牌词 > 否词 > 人群词 > 场景痛点词 > 属性词 > 核心大词 > 长尾组合词
```

补量化维度：
- **跨 ASIN 覆盖率**：该属性词根在 N 个竞品 Listing 中出现的比例（>60% 品类必备必埋；30-60% 次级；<30% 差异化机会）。

详细分类判定规则见 `03-classification.md`（自包含，不依赖旧 skill）。

**用哪个工具**：LLM 按 rubric 批量打标（7 类）；SIF `ops_get_listing_keyword_distribution` 辅助覆盖率计算。

**输出**：词根表附类别 + 备注（备注不能为空，否词沉淀进否词池）。

**易错点**：备注为空；把多属性词误判为属性词（应判长尾组合词）；否词未及时进池。

---

## Step 6 · 语义聚类成投放主题簇

> 广告架构的单元是**簇**，不是单词根。这是从「词根」到「广告分级」之间缺失的一步。

**输入**：Step 5 分类后词根表 + `coverage_ratio`。

**动作**：
- 用 embedding 聚类 / LLM 归主题，把同意图、同属性维度的词归一个 **ad group 主题**。
- **簇数量上限**：标品广告 ≤ **15** 个；非标品广告 ≤ **30** 个。超出则按相关性×需求合并低优簇。
- `coverage_ratio` < 0.4 → 系统性铺长尾，可适当扩大簇数量；`coverage_ratio` > 0.8 → 集中精确词，簇粒度可粗。
- 每个簇标注：主属性维度 / 相关性档 / 需求档 / 趋势 / 跨 ASIN 覆盖率 / `coverage_ratio`。
- 输出对接脚本的 `--clusters-csv`。

**用哪个工具**：LLM 聚类（embedding + 归主题）。

**输出**：主题簇表（列：主题簇/主属性维度/相关性/需求/词数/趋势/跨ASIN覆盖率/coverage_ratio）；对接 `--clusters-csv`。

**易错点**：簇数量超上限未合并（执行成本爆炸）；簇粒度太细（每个词单独一簇）；忽略 `coverage_ratio` 导致长尾布局不足。

---

## Step 7 · 广告架构分级（决策矩阵 → campaign 落地）

> 🔴 **修正**：不能只按竞争度单维分级——「高相关低竞争」金词和「低相关低竞争」垃圾词会混档。至少四维：相关性/意图 × 搜索量 × 竞争/CPC × 趋势。

**输入**：Step 6 主题簇表 + 竞争度数据。

**动作**：按决策矩阵映射每个簇到 campaign/adgroup 动作；竞品广告架构反查作为实证锚点。

见 `05-ad-architecture.md` 完整决策矩阵。

**用哪个工具**：SIF `market_get_keyword_competition`（竞争三维评估）、`ads_get_asin_ad_ctructure`（竞品 campaign 规模）、`ads_get_ad_group_keyword_breakdown`（竞品 ad group 分词，学竞品成熟设计）。

**输出**：广告架构表（campaign/ad_group/匹配方式/预算占比/攻守测）；对接 `--architecture-csv`。

**否词池**：贯穿 Step 0-7 持续沉淀（冲突属性、跨品类、低相关）。

**易错点**：忽略趋势维（上升词需提前卡位即便当前量低）；否词池到这步仍空（违反 CHECKPOINT 2）。

---

## Step 8 · 输出 + 否词池 + 回流出口

**输入**：Step 7 全量产出。

**动作**：
- 汇总输出 Excel：**恒定 7 Sheet**（拓词总表 / P0-P1优先词 / Listing埋词建议 / PPC投放建议 / 否词候选 / 来源汇总 / 执行说明）+ **条件 Sheet**（主题簇←--clusters-csv / 广告架构←--architecture-csv / ASIN画像←--asin-summary）+ **下游 2**（VOC词库/收录排名追踪，除非 --no-downstream）。完整广告架构交付必须传 clusters/architecture CSV。
- 数值缺失列留空 + 标「待数据验证」，不编造。
- 留回流出口说明：投放后用 search term report 回流 → 否词/提词，避免一次性僵化。

**输出**：Excel 文件（优先）/ HTML 降级 / Markdown 降级。

---

## 否词旁路（贯穿全程）

否词池在 Step 0 初始化（必排属性作种子），Step 1-7 持续沉淀：
- Step 0：必排属性 → 否词种子
- Step 1：VOC 转化过滤掉的跨类目词
- Step 4：相关性「低」的词（<30% 同类）
- Step 5：7 类中直接标为「否词」的词
- Step 7：低相关 / SD 防守 / 不投 的词

**CHECKPOINT 2 要求**：输出前否词池必须非空。
