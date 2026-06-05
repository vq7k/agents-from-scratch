# init-agent-teams dry-run 凭证

> 验证 init 的侦察+历史挖掘可跨项目工作（**只读，不落地**到样例项目）。日期：2026-06-04。

## 样例项目
- 路径：<样例项目>（脱敏，仅记类型：某内容生产流水线/脚本编排工具，含一个前端 web 子模块）
- CC 历史 session 数：2

## A1 静态侦察
- README/目录可读：✅
- 识别出的画像：某内容生产流水线工具，按结构化目录组织内容并用脚本跑流水线，附一个前端 web 子模块；治理文档集中在仓库根

## A2 历史挖掘（1 个 session map 验证）
- map 抽取返回结构化结果：✅（按 history-mining.md §1 取体量最大的 session 做 map）
- 字段齐（project_profile/division_signals/decisions/pitfalls/current_state/conventions）：✅（JSON parse ok，6 字段全 present）
- 敏感原文已 `<REDACTED>`：✅（占位生效；产物经红线自检无样例真实项目名/绝对路径）
- 注：抽出的具体内容**未留存**，仅保留「能抽出结构化且脱敏」这一事实；临时产物用后即删

## structure-check 自测（本仓）
- 初测：14/15 PASS，1 FAIL（B2-2「STATUS 5 段齐」误判——本仓 STATUS.md 用 9 个自有命名段，撞硬编码的 5 个模板段名）。
- **已修（v0.2）**：B2-2 改为「分段 ≥4 + 含 actionable readiness 锚点（不强求固定段名）」，本仓复测 **全 PASS / exit=0**。属 brownfield 命名差异，非模板缺陷。

## 发现的问题
| # | 问题 | 处置 |
|---|---|---|
| 1 | structure-check 的 STATUS 段校验硬编码模板段名，宿主项目若已有命名不同的 STATUS 必 FAIL（即便健康），与 A4「不覆盖原有约定」相悖 | ✅ **RESOLVED（v0.2）**：B2-2 改为「分段 ≥4 + 含 actionable readiness 锚点」，不强求固定段名；本仓复测全 PASS |

## 结论
- 🟢 init 侦察+历史挖掘协议跨项目可走通（只读验证）
- 真实落地 + check 全流程留待首个真实目标项目实战
