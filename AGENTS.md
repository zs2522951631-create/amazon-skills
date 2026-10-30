# Amazon Skills workspace

这是四套上游项目的源码合集。入口是 README.md、SKILLS.md；固定来源见 sources.lock.json。

## 选择与加载

- 按问题选择一个主 skill，再按需加载依赖；不要一次读取全部 skill、测试、研究文档。
- 综合广告诊断：packages/amazon-ads-skills/skills/amazon-ads-optimizer/SKILL.md。
- 搜索词报表、词根分类、否词候选：packages/zach-amazon-skills/skills/zach-search-term-report-analyzer/SKILL.md。
- 搜索词转精准、目标活动和来源否词规划：packages/amazon-ppc-advanced-skills/amazon-search-term-harvest-planner/SKILL.md。
- 广告与产品状态联动的周/月计划：packages/amazon-ppc-advanced-skills/amazon-account-growth-operating-system/SKILL.md。
- 拓词与新广告架构：packages/amz-ads-keyword-architect/SKILL.md。
- 细分问题按 SKILLS.md 选择。templates 下的 skill 是编写模板，不能当成现成运营流程。
- 进入有 AGENTS.md 的包时读取并遵循该包的适用说明。

## 路径与运行

- 每个包保留上游目录结构；脚本命令相对于对应包根目录执行。
- 保持 shared references、scripts、schemas、assets、examples 与相关 skill 的相对位置。
- 工作区按路径加载即可，不要假设已经全局安装或已经连接 MCP。
- 本仓库收录依赖声明与源码；运行前检查当前环境的 Python 库和所需外部能力。

## 数据与动作

- 先检查站点、账户范围、币种、日期窗口、报表字段、业务目标和样本。
- 缺失数据不能当作零；结论标清数据事实、推断、缺口与置信度。
- 默认输出分析与建议。需要真实账户操作时，遵循已有用户授权及所选上游 skill 的执行、回读与监测流程。
- 不在这个合集内保存真实店铺报表、账号凭证或运行输出；工作输出放在用户指定的位置。

## 维护

- packages 中是固定 commit 的上游内容。维护合集说明时尽量保留上游原文。
- 若需修改上游内容，应明确记录改动，并相应更新来源/校验清单；不要静默覆盖作者署名。
- 使用 python scripts/verify_import.py 验证 808 个导入文件的 Git blob SHA。
