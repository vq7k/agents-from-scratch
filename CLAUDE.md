# agents-from-scratch — Claude Code Entry Point

> 自动加载入口。先读 [`PROJECT.md`](./PROJECT.md) — 顶层身份 + 找到你的角色。

## 必读
1. [`PROJECT.md`](./PROJECT.md) — 项目顶层身份 + 启动序列
2. `.agent/SOUL.md` / `.agent/STATUS.md` / `.agent/TODO.md` — 你是谁 / 上次状态 / 下一步

## 可用 skills（按需读）
- [`catch-up`](./.skill/catch-up/SKILL.md) — session 启动怎么 catch up
- [`status-update`](./.skill/status-update/SKILL.md) — 怎么写 STATUS
- [`init-agent-teams`](./.skill/init-agent-teams/SKILL.md) — 治理层 init/check（本骨架即由它搭建）

## 本项目硬约定（历史沉淀，反复被强调的红线）
- 始终中文回复，技术术语 / 代码标识符保留原文；禁用比喻 / 修辞，最简技术语言。
- **不替 user 跳过学习**：讲底层机制、不藏推理、user 想看的就摊开（PHILOSOPHY：没有魔法）。
- 最小可运行优先，**不过度封装 / 过度设计**。
- **只动指定文件**，不擅改未授权内容 / 不碰他人 git 变更；commit/push 仅 user 要求时，非 main 先开分支（当前 zh-cn）。
- 技术结论联网核实给信源，不臆断。
