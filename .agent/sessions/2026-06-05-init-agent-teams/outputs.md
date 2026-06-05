# 2026-06-05 · init-agent-teams（嵌入治理层）

## 触发
user `@.skill/init-agent-teams/` → 对本 brownfield 教学仓做 init。

## 做了什么
- **A1 静态侦察** + **A2 历史挖掘**：map-reduce 派 6 个 miner（5 Claude Code + 1 Codex）抽脱敏信号 → reduce 成统一画像。
- **A3 裁剪**：三问证据一致 → **单 agent 起步**（教学 i18n 与 Python 实现是同一条串行学习流，不裂 Worker；无独立运维面 → 无 infra；视觉非卖点 → 无 design）。
- **A4 嵌入**：`PROJECT/CLAUDE/AGENTS` 入口 + `.agent/{SOUL,STATUS,TODO}`；发现宿主已有同族旧脚手架 → `catch-up` 仅定点修冲突角色表（`Orchestrator/apps`→教程主理），`status-update` 等保留原样。
- **Optional**：5 份 `decisions/` ADR + 12 条 `learned-rules`（历史脱敏料）。
- **回写闭环**：`init-agent-teams` skill v0.2.1→**v0.2.2**（A4 补「同族脚手架冲突不整体覆盖、仅定点修」），已知问题清零。

## 产出
- commit `39f9405`（37 文件，+1344）+ 本次收尾 commit。
- `structure-check.sh` 全 PASS / exit=0。

## 遗留
- `complete_example.py` 有 user 在途改动（未碰，保持未暂存）。
- **下一步两候选待 user 拍板**：①进 lesson6 agent_loop ②收尾 lesson4-5 调试 print / demo 切换。
