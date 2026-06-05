# Project: <项目名>

> 顶层身份。任何 agent runtime 进入本项目时**第一份必读**。

## 我是谁
`<项目名>` — **顶层 Agent**。
- 使命：<一句话使命>
- 范围：<范围>
- 完整 spec：<spec 路径，可选>

## 项目层级（你进来要先理解）
```
顶层 Agent: 本项目（user 是上级）
    ├── 主理：<主理角色>（仓库根 session）
    │   ├── 工作区：.agent/
    │   └── 委派：<Worker 列表，单 agent 阶段写「暂无（按需裂变）」>
    ├── 能力：.skill/（协作 SOP）
    └── <按需：.tool/ / .eval/ / infra/>
```

## 启动序列
1. **找到角色**：看 cwd（仓库根 → <主理角色>；<其他 cwd → 其他角色>）
2. **catch up**：读该位置 `.agent/SOUL.md` + `STATUS.md` + `TODO.md`（见 `.skill/catch-up`）

## 找东西的地图
| 你想做 | 去 |
|---|---|
| 当前阶段 / 上次 session | `.agent/STATUS.md` |
| 我该做什么 | `.agent/TODO.md` |
| 怎么做（SOP） | `.skill/<name>/SKILL.md` |
| <按需追加：架构 / 决策 / 视觉…> | <路径> |

## Runtime 入口
| Runtime | 入口 | 说明 |
|---|---|---|
| Claude Code | `CLAUDE.md` | 自动加载，指向本文件 |
| Codex / 其他 | `AGENTS.md` | 同上 |
| 任何 | 本文件 `PROJECT.md` | source of truth |
