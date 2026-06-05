# Optional 模块（按需加挂，init 默认不强加）

> human 决定何时加（§check B2 第 4 组会提示缺口）。每个模块自包含，加挂方式见下。

| 模块 | 何时加 | 怎么加 |
|---|---|---|
| **decision-log** | 决策开始需要留痕（多人/多 session） | 建 `.agent/decisions/`，每决策一份 ADR（决定/背景/备选/影响） |
| **learned-rules** | 开始反复踩同类坑 | 建 `.agent/learned-rules.md`（≤30 条；场景/踩坑/规则/来源），可由历史挖掘提炼初始条目 |
| **隐私五层** | 项目有真名/机构/客户等需脱敏 | ① spec/SOUL 写硬约束 ② `.agent/secrets.env.example`+`sensitive-words.txt`（清空填本项目词）③ `check-no-leaks.sh` ④ commit 前必跑 ⑤ 可选 eval 验证。**历史挖掘产物入库前必过此闸** |
| **.eval/** | 需要验证 agent 系统行为本身 | 复制 `cases/suites/checks/judges/harness/` 目录架构；原则：跨 family judge / rubric 隐藏 / negative case / pass^3 / 程序化 check |
| **worker-review** | 交付需独立复核（不能 self-judge） | 跨角色 review，judge 与被审非同一 agent family |

**加挂后**：在目标项目 `CLAUDE.md` 「可用 skills」段追加对应行。
