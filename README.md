# Amazon Skills｜亚马逊广告运营技能合集

汇集四套开源项目：**23 个可用 skill、1 个编写模板、808 个上游文件**。保留源代码、共享 references、scripts、schemas、示例、测试、模板与作者许可证，供 Codex 等可读取文件的 Agent 使用。

## 已收录

| 项目 | 内容 | 本仓库入口 |
|---|---|---|
| Amazon Ads Skills · zerlinpi | 15 个 skill：竞价、预算、广告位、关键词、否词、诊断、利润与复盘 | [项目目录](packages/amazon-ads-skills/) · [原说明](packages/amazon-ads-skills/README.md) |
| Zach 搜索词报告分析 | 1 个 skill：清洗、词根分类、否词/控成本/放量建议，输出 Markdown、CSV、HTML、JSON | [SKILL.md](packages/zach-amazon-skills/skills/zach-search-term-report-analyzer/SKILL.md) · [原说明](packages/zach-amazon-skills/skills/zach-search-term-report-analyzer/README.md) |
| Amazon PPC Advanced Skills · nospicyplease | 6 个 skill + 1 个模板：下滑诊断、增长、账户计划、搜索词收割、Rocketcart 复核、案例脱敏 | [项目目录](packages/amazon-ppc-advanced-skills/) · [原说明](packages/amazon-ppc-advanced-skills/README.md) |
| 亚马逊广告架构拓词 · Derek | 1 个 skill：找词、分级、主题聚类、Campaign/Ad Group 架构与 Excel 交付 | [SKILL.md](packages/amz-ads-keyword-architect/SKILL.md) · [原说明](packages/amz-ads-keyword-architect/README.md) |

完整清单见 [SKILLS.md](SKILLS.md)。四套项目分别保存在 `packages/`，以保持原有相对路径和共享依赖。

## 在 Codex 中使用

先克隆本仓库，然后在 Codex 中打开克隆得到的目录：

```bash
git clone https://github.com/zs2522951631-create/amazon-skills.git
cd amazon-skills
```

首次可以直接对 Codex 说：

```text
读取根目录 AGENTS.md 和 SKILLS.md，按我的任务选择最合适的一个 skill，
再读取它的 SKILL.md 和必要的依赖。检查输入是否完整，然后完成分析。
```

例如：

```text
读取 packages/amazon-ads-skills/skills/amazon-ads-optimizer/SKILL.md，
结合我提供的广告报表做账户诊断，输出竞价、预算、广告位和否词建议。
站点、币种、时间范围、目标 ACOS 和库存信息以我提供的数据为准。
```

```text
读取 packages/zach-amazon-skills/skills/zach-search-term-report-analyzer/SKILL.md，
分析附件中的搜索词报表。ASIN、品牌、站点和目标 ACOS：由我填写。
```

```text
读取 packages/amazon-ppc-advanced-skills/amazon-search-term-harvest-planner/SKILL.md，
为自动和广泛广告中的搜索词制定精准收割与否词候选计划。
```

```text
读取 packages/amz-ads-keyword-architect/SKILL.md，
根据本品信息、竞品 ASIN 与关键词数据，输出广告架构工作簿。
```

这是仓库工作区使用方式。**仅上传到 GitHub 不会自动完成本机全局安装**；如果需要另行安装，请让 Codex 根据本合集目录处理共享资源，或直接在本仓库内按路径加载。尤其 Amazon Ads Skills 的 `../../references`、`../../scripts`、`../../schemas` 必须与其 `skills/` 一起保留。

## 运行依赖

| 项目 | 本地依赖 | 外部数据能力 |
|---|---|---|
| Amazon Ads Skills | Python 3.10+；检查脚本主要使用标准库 | 离线报表可用；实时读数需要另配 connector/MCP |
| Zach 搜索词报告分析 | Python 3.10+；pandas、beautifulsoup4、openpyxl，见 skill 内 requirements.txt | 本地报表与 Listing 快照可用；实时抓取为可选 |
| Amazon PPC Advanced Skills | Python 3.10+；保留完整 src 与测试文件 | 离线模式可用；实时账户功能另需 Rocketcart MCP |
| 广告架构拓词 | Python 3.10+；工作簿脚本使用标准库；运行其测试需 pytest | SIF / Sorftime 可选；飞书交付另需 lark-cli |

Zach 的依赖安装命令，从本仓库根目录执行：

```bash
python -m pip install -r packages/zach-amazon-skills/skills/zach-search-term-report-analyzer/requirements.txt
```

运行每套上游 README 的示例命令时，先进入对应包根目录。例如 Zach 的包根目录为 `packages/zach-amazon-skills`；其说明中的 `skills/zach-search-term-report-analyzer/...` 相对于该目录。

依赖文件已导入，第三方 Python 库和 MCP 服务需要在使用环境中配置。本次导入没有连接广告账户。各项目保留上游对建议、执行和回读的边界。

## 来源与校验

- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)：来源、作者与许可证。
- [sources.lock.json](sources.lock.json)：固定上游 commit、文件路径与 Git blob SHA。
- [VALIDATION.md](VALIDATION.md)：本次实际运行的检查结果。
- 校验导入内容是否完整、是否被修改：

```bash
python scripts/verify_import.py
```

上游目录内的原作者链接与安装说明按原文保留；使用本合集时优先采用上面的本仓库路径。本合集不会自动跟踪上游更新。
