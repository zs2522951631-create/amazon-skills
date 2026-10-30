# amz-ads-keyword-architect · 亚马逊广告架构拓词 Skill

一个用于 **Amazon 关键词拓词 → 广告 campaign 架构 → 下游资产化 → 双通道交付** 的
[Claude / Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)。给定本品锚点
与竞品 ASIN，按八步流程把「词」做成可落地的广告投放结构，并输出一份多 Sheet 工作簿。

> 核心铁律：**不虚构任何数值型指标**（搜索量 / SFR / ACOS / CTR / CVR / 排名 / 市场份额）。
> 数值只能由数据工具取数，缺数据一律标「待数据验证」，仅做语义判断。

## 它能做什么

覆盖全链路：

```
找词 → 拆解 → 需求三层分析 → 相关性×需求×竞争×趋势分级
     → 属性 7 类分类 → 聚类成主题簇 → 广告架构落地
     → VOC库 / 收录排名追踪 → Excel / 飞书双通道交付
```

- 标品 ≤15 / 非标品 ≤30 个 ad group 主题簇上限
- 三道 CHECKPOINT + 反模式黑名单 + 反虚构铁律统一约束
- 自包含的分类与评分骨架（不依赖其他 skill）

## 目录结构

| 路径 | 内容 |
|------|------|
| `SKILL.md` | Skill 主入口：核心理念、八步流程、CHECKPOINT、绝对禁令 |
| `PROMPT-TEMPLATE.md` | 可复用的 prompt 模板（填占位符即用） |
| `references/01-09*.md` | 各步骤详解：流程 / 指标 / 分类 / 聚类 / 广告架构 / 工具数据 / 质检 / 下游应用 / 飞书交付 |
| `scripts/build_kw_architecture.py` | 把拓词 CSV 构建成多 Sheet `.xlsx` 工作簿（纯标准库，无第三方依赖） |
| `scripts/test_build_kw_architecture.py` | pytest 测试 |

## 快速开始

### 1. 作为 Skill 使用

把本目录放进 Agent 的 skills 目录（例如 `~/.claude/skills/amz-ads-keyword-architect`），
然后用 `PROMPT-TEMPLATE.md` 里的模板发起请求。Agent 会按 `references/01-flow.md`
的八步流程执行。

### 2. 单独运行工作簿脚本

脚本只用 Python 标准库，无需安装任何依赖（Python 3.10+）：

```bash
python3 scripts/build_kw_architecture.py 拓词总表.csv \
  --product-name "yoga mat" \
  --core-terms "yoga mat" \
  --conflict-terms "bath mat,door mat,puzzle mat" \
  --asin B0DEMOMAIN \
  --clusters-csv clusters.csv \
  --architecture-csv architecture.csv \
  --voc-csv voc.csv \
  -o 广告架构拓词_B0DEMOMAIN.xlsx
```

常用参数：

| 参数 | 说明 |
|------|------|
| `input` | 输入关键词 CSV（必填） |
| `-o, --output` | 输出 `.xlsx` 路径 |
| `--keyword-column` | 关键词列名（默认自动探测） |
| `--core-terms` / `--conflict-terms` | 核心词 / 否词（冲突词），逗号分隔 |
| `--brand-terms` / `--competitor-brands` | 自有品牌词 / 竞品品牌词 |
| `--clusters-csv` / `--architecture-csv` / `--voc-csv` | 可选：主题簇 / 广告架构 / VOC 词库 CSV |
| `--asin` | 用于填充收录排名追踪表的本品 ASIN |
| `--no-downstream` | 跳过 VOC / 追踪等下游 Sheet |
| `--emit-sheets-json` | 同时导出每个 Sheet 的 JSON manifest（飞书原生构建通道用） |

### 3. 跑测试

```bash
pip install pytest      # 仅测试需要
pytest scripts/
```

## 交付通道

- **本地 Excel（默认）**：`-o *.xlsx` 直接产出。
- **飞书（Lark）在线表格（可选）**：见 `references/09-feishu-delivery.md`。该通道依赖
  外部的 `lark-cli` 工具链，属**可选**集成；不使用飞书时忽略即可，
  不影响核心拓词与 Excel 交付。

## 数据工具依赖（可选）

流程中数值取数引用了 SIF、Sorftime 等第三方 Amazon 数据服务。这些是**可选的取数来源**，
不内置于本仓库。没有这些服务时，Skill 会自动降级为语义版分析，并把所有数值列标记为
「待数据验证」，**绝不以经验值编造**。

## 示例数据说明

仓库内所有 ASIN（`B0DEMOCMP1`、`B0EXAMPLE1`、`B0TESTASIN` 等）均为**占位示例**，
不指向任何真实在售商品。请替换为你自己的 ASIN 后再运行。

## License

[MIT](./LICENSE) — 使用前请把 `LICENSE` 中的 `<YOUR NAME OR ORGANIZATION>`
替换为你的署名。
