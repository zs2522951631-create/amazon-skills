# Import validation

验证日期：2026-10-30。所有检查使用上游固定 commit 的源码与合成/公开样例，未连接真实广告账户。

## 结果

| 检查 | 结果 |
|---|---|
| 上游文件完整性 | 808 / 808 文件的 Git blob SHA 与 sources.lock.json 中记录的上游一致 |
| Skill 入口清单 | 23 个可用 skill + 1 个编写模板，入口均存在 |
| Amazon Ads Skills 单元测试 | 2282 项通过 |
| Amazon Ads Skills 结构检查 | 15 个 skill 目录通过 validate_skills.py |
| Amazon Ads Skills eval 契约检查 | 55 个 fixture 文件通过 validate_evals.py |
| Amazon PPC Advanced Skills 合成测试 | unit / e2e / leakage 三组共 26 项通过 |
| Zach v2 核心测试 | test_prepare.py 与 test_decisions.py 共 101 项通过 |
| 亚马逊广告架构拓词 | 直接调用 8 个上游测试函数，全部通过；使用临时目录运行原有断言，无需安装 pytest |

## Zach 测试环境说明

本次完整 discovery 运行发现当前 Python 环境缺少 `beautifulsoup4`（导入名 `bs4`）。因此 `test_decision_logic.py`（旧版兼容逻辑）和 `test_listing_context_fetch.py`（Listing HTML 解析）两组未能加载；其余 v2 准备与决策测试已通过。

为明确范围，另行独立运行了 `test_prepare.py` 与 `test_decisions.py`。完整依赖声明保存在：

`packages/zach-amazon-skills/skills/zach-search-term-report-analyzer/requirements.txt`

使用者安装 requirements 后可在 `packages/zach-amazon-skills` 目录执行完整检查：

```bash
python -m unittest discover -s skills/zach-search-term-report-analyzer/tests
```

上游文件保持原文，没有为了让当前测试环境通过而改写或伪造依赖。MCP 实时读取、真实账户执行及模型实际广告优化效果不在本次本地检查范围内。

## 复核导入文件

在本合集根目录执行：

```bash
python scripts/verify_import.py
```
