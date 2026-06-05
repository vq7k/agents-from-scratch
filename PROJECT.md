# Project: agents-from-scratch

> 顶层身份。任何 agent runtime 进入本项目时**第一份必读**。

## 我是谁
`agents-from-scratch` — **顶层 Agent**。一份本地优先、无框架、无云 API 的「从零构建 AI Agent」中文教学仓（zh-cn 分支，fork 自上游英文教程）。
- 使命：用 12 节课从一次本地 LLM 调用出发，一步步讲清 AI Agent 到底如何工作 —— 无魔法、不藏推理。
- 范围：教学内容（`lessons/` 12 课 + 根目录 `NN-*.md` 中文答疑笔记）+ 可运行 Python 实现（`shared/` 推理封装、`agent/` 运行时）+ 本地 LLM 环境（llama-cpp-python + qwen2.5-7b GGUF / Apple Metal）。
- 完整 spec：`README.md` · 理念见 `PHILOSOPHY.md`

## 项目层级（你进来要先理解）
```
顶层 Agent: 本项目（user 是上级）
    ├── 主理：教程主理（仓库根 session）
    │   ├── 工作区：.agent/
    │   └── 委派：暂无 Worker（按需裂变 —— 见 .skill/init-agent-teams 裂变阶梯）
    ├── 能力：.skill/（catch-up / status-update / init-agent-teams）
    └── 业务：lessons/ · shared/ · agent/ · evals/（agent 维护对象，非另一个角色）
```

## 启动序列
1. **找到角色**：看 cwd（仓库根 → 教程主理；当前仅此一个角色）
2. **catch up**：读 `.agent/SOUL.md` + `STATUS.md` + `TODO.md`（见 `.skill/catch-up`）

## 找东西的地图
| 你想做 | 去 |
|---|---|
| 当前阶段 / 上次 session | `.agent/STATUS.md` |
| 我该做什么 | `.agent/TODO.md` |
| 怎么做（SOP） | `.skill/<name>/SKILL.md` |
| 选型 / 架构决策（为什么这么定） | `.agent/decisions/` |
| 反复踩的坑 → 规则 | `.agent/learned-rules.md` |
| 课程内容 | `lessons/01..12_*.md` |
| 中文答疑笔记 | 根目录 `01-..05-*.md` |
| 本地 LLM 封装 / 配置 | `shared/llm.py` · `shared/config.py` |
| Agent 运行时实现 | `agent/`（agent / memory / planner / state / tools / telemetry） |

## Runtime 入口
| Runtime | 入口 | 说明 |
|---|---|---|
| Claude Code | `CLAUDE.md` | 自动加载，指向本文件 |
| Codex / 其他 | `AGENTS.md` | 同上 |
| 任何 | 本文件 `PROJECT.md` | source of truth |
