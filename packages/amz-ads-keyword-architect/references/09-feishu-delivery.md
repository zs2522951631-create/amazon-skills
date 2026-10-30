# 交付通道：Excel ↔ 飞书表格（Step 8/9 收口）

> 本 skill 支持**双通道**交付：本地 Excel（默认）与飞书在线表格（可选）。同一份 `sheets` 数据，两条通道共用，**绝不为某通道单独编造或丢弃数据**。

---

## 1. 通道决策（先检测，再按偏好，最后兜底）

按以下顺序确定交付通道，**不要默认就往飞书写**：

```
Step A 用户是否明确指定？
  - 用户说「Excel / 表格文件 / 本地」          → Excel 通道（默认）
  - 用户说「飞书 / 飞书表格 / 飞书云文档 / 在线」 → 飞书通道
  - 用户没说                                    → 进 Step B

Step B 检测飞书能力是否可用：
        lark-cli auth status   （读 identities.user.available）
  - lark-cli 不存在 / user.available=false / 无 sheets:spreadsheet:create scope
        → 仅 Excel；一句话说明「飞书未接入，已交付本地 Excel，需要可后续导入飞书」
  - 可用 → 进 Step C

Step C 询问偏好（一次性、二选一，给默认值）：
  「交付到 ① 本地 Excel（默认，离线可改） 还是 ② 飞书在线表格（多人协作/链接分享）？」
  - 用户选飞书但没给已有表 → 再问：新建表，还是写入已有表（给表格链接或标识）？
```

- 认证状态显示需要刷新时，通常可由工具链自动刷新，**不算飞书不可用**。判定可用只看 `user.available`（或 `bot.available`）+ 是否含 `sheets:spreadsheet:create` scope。
- 默认偏好本地产出 + Excel；**无明确信号时默认 Excel**，飞书是显式选项。

---

## 2. 数据来源：一次生成，双通道复用

不论走哪条通道，都先用脚本生成同一份工作簿，避免两套数据漂移：

```bash
python3 scripts/build_kw_architecture.py 拓词总表.csv \
  --product-name "yoga mat" --core-terms "yoga mat" --asin B0DEMOMAIN \
  --conflict-terms "bath mat,door mat,puzzle mat" \
  --clusters-csv clusters.csv --architecture-csv architecture.csv --voc-csv voc.csv \
  -o 广告架构拓词_B0DEMOMAIN.xlsx \
  --emit-sheets-json 广告架构拓词_B0DEMOMAIN.sheets.json   # ← 飞书通道才需要
```

- `-o *.xlsx`：Excel 通道直接交付；也是飞书「导入路径」的源文件。
- `--emit-sheets-json *.json`：导出每个 Sheet 的 `{name, headers, rows, values}`（`values` = 表头行 + 数据行的 2D 数组），喂给飞书「原生构建路径」的 `lark-cli sheets +append --values`。Excel 通道不传此参即可。

---

## 3. 飞书通道 · 路径甲（推荐）：导入已生成的 Excel

最省事、最不易出错——一次把所有 Sheet 带进飞书，保留本 skill 的 Sheet 语义命名。

1. 调 **lark-drive** skill：把本地 `广告架构拓词_*.xlsx` 导入为飞书在线电子表格（sheet）。
2. 导入完成后，在线表可直接在飞书中打开与分享。

适用：用户只要「一张能在飞书打开/分享的表」，不在意页签的精确命名。

---

## 4. 飞书通道 · 路径乙：原生构建（lark-cli sheets）

用户明确要「飞书原生页签结构 / 冻结表头 / 后续要在飞书里追加写」时走这条。调 **lark-sheets** skill 编排：

1. 读 `--emit-sheets-json` 产物，得到 sheets 数组。
2. **新建表**：`lark-cli sheets +create --title "广告架构拓词_<ASIN>_<日期>" --headers <第一个sheet的headers JSON> --data <第一个sheet的rows JSON>`，拿回表格标识。
   **写入已有表**：先 `lark-cli sheets +info --url <URL>` 读现有页签，缺哪个补哪个。
3. 其余每个 sheet：用表格标识创建页签并追加 `values`（`values` 已含表头行）。
4. 表头行冻结 / 加粗：`+batch-set-style`（可选，非阻塞）。

> 提示：`+create --dry-run` 的输出 body 只回显 `title`（建表那一个 API 调用），`--headers`/`--data` 不在 dry-run plan 里回显——它们随后续 `+append` 写入，属正常，不是参数没生效。实跑（去掉 `--dry-run`）才真正写入表头与数据。

> 原生构建默认沿用本 skill 的 Sheet 名（语义紧凑）；如需对齐特定页签命名规范，逐项改 `--title` 即可。

---

## 5. 失败模式与降级（飞书写入不改业务结论）

| 触发条件 | 处理 | 输出标记 |
|---|---|---|
| macOS Keychain 被沙盒拦截 | 在沙盒外重试同一条 lark-cli 命令，不改业务逻辑 | — |
| `user.status=needs_refresh` | 正常，直接调用即可自动刷新；不当失败处理 | — |
| 飞书 create/append 写入失败 | 不改业务判断；保留本地 `.xlsx` + `.sheets.json` + 可重试命令，说明失败点 | `飞书待重试` |
| 用户要飞书但 lark-cli 不可用 | 仅交付 Excel；说明飞书未接入及后续导入方式 | `飞书未接入` |
| 已有表缺页签 | 只补缺失页签，不覆盖既有数据 | — |

**铁律**：无论哪条通道失败，都不得为了「交付成功」而虚构搜索量/排名/ACOS/订单/Review 原文（与反模式黑名单第 2、5 条一致）。
