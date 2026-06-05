# skill: delegate-worker

Orchestrator 怎么委派 Worker。

## 何时用

Orchestrator 决定要做 `apps/<m>/` 业务代码（web 的 `app/`/`components/`/`lib/`/`data/`，biz 的 `src/main/{java,kotlin}/`，ai 的 `*.py`/`routers/` 等），但**自己不能动手**（角色边界）。

**例外**：`Dockerfile` / `Dockerfile.dockerignore` / `playwright.config.ts` / 部署 script 由 Orchestrator 直接维护，不委派（V0.2 ADR [`.agent/decisions/2026-05-28-dockerfile-blocklist.md`](../../.agent/decisions/2026-05-28-dockerfile-blocklist.md)）。

## ⚠️ Opus 不是 Worker

**Opus（cwd = `infra/`）是与 Orchestrator 同级的专家角色，user 是 Orchestrator + Opus 的共同上级。**

- ❌ Orchestrator **不能** 委派 Opus（同级不能委派）
- ✅ user 直起 Opus session（cwd = `infra/`）
- ✅ 其他 Agent（Orchestrator / Worker）有基础设施需求 → 写 `infra/.agent/TODO.md` 推任务，commit message 标 `task→infra`（**异步**，opus 启 session 时按 SOP 接）

详 spec [§3 + §6](../../docs/superpowers/specs/2026-05-28-opus-infra-module-design.md)。

本 skill 下文 "委派的两种方式" / "委派前 Orchestrator 必做的 3 件事" 仅适用 Web / Biz / AI / Design Worker。

## ⚠️ Design Worker 是 Worker 级，与 Web Worker hot loop

**Design Worker（cwd = `packages/design/`）受 Orchestrator 委派**（与 web/biz/ai 同 Worker 级，**非**像 Opus 那种同级专家）。

- ✅ Orchestrator **可以** 委派 Design Worker（spec 标 `@design` 段）
- ⚠️ Design Worker 与 Web Worker **hot loop**：通过编译时 import（`@from-fullstack-to-ai/design`）+ 异步推 TODO（`packages/design/.agent/TODO.md` ↔ `apps/web/.agent/TODO.md`）+ Design Worker 派 sub-agent 反验 Web 实现（只读 + 跑 smoke 出截图，不改代码）
- ❌ Design Worker **不可** 跨模块写 `apps/web/` 代码（所有代码改动推任务到 web，commit `task→web`）
- ❌ Web Worker **不可** 改 `packages/design/` 产物（视觉决策走 Design Worker；新视觉需求推任务，commit `task→design`）

详 spec [§3 + §5 + §6](../../docs/superpowers/specs/2026-05-28-design-worker-module-design.md)。

**Orchestrator 红线**：
- spec 起草遇视觉 / IA 区段 → 标 `@design` → 委派 Design Worker
- 不直接 1:1 跟 Web Worker 拍视觉细节（V0.3.x 飞书范式 patch 模式 deprecated）
- Web Worker plan 起草前确认 `design-spec.md` 相关版本已 ready（前置依赖）

## 委派的两种方式

| 方式 | 适用 | 触发 |
|---|---|---|
| **手动新 session** | 长任务 / 需要 Worker 自主 brainstorm | 用户开新 Claude Code session，`cd apps/<m>/` |
| **SubAgent 调用** | 短任务 / Orchestrator 同 session 内编排 | Claude Code `Task` tool 启动 subagent（绑 Claude Code） |

## 委派前 Orchestrator 必做的 3 件事

1. **更新 `apps/<m>/.agent/TODO.md`** — 把要做的事写进去，足够 actionable
   - 任务清单
   - 必要约束（边界 / DoD / 验收）
   - 上下文链接（spec 章节 / 接口契约 / 其他依赖）
2. **不超出 Worker 边界** — 委派的任务必须在 Worker 可写区内
3. **决策追溯** — 在 Orchestrator 自己的 session 归档 `decisions.md` 记一笔："委派 <module> Worker 做 X"

## 委派 prompt 模板（手动 session 时给用户参考）

```
你刚启动，cwd 在 apps/<m>/。先按 CLAUDE.md 指引 catch up（见 .skill/catch-up）。
本次目标：<一句话>
任务清单见 .agent/TODO.md。
完成后按 .skill/worker-summary 回 Orchestrator。
```

SubAgent 调用时同样的指令作为 prompt。

## 委派后 Orchestrator 做的事

- 等 Worker return summary（Worker 按 worker-summary skill 写文件 + 回口头摘要）
- catch up Worker session 归档
- 决策追溯（项目级落 spec §12 或模块级落 `.agent/decisions/`）
- **触发 worker-review**（V0.1.2 后强制）：调 `.skill/worker-review` 跑 PI cross-family judge，结果归档 `.eval/runs/<date>-<worker>-<topic>-review/`。

## 反例

- ❌ Orchestrator 自己动手改 `apps/<m>/src/` — 违反角色边界
- ❌ 委派时不更新 `apps/<m>/.agent/TODO.md` — Worker 拿不到上下文
- ❌ 委派模糊任务（"把 web 做了"）— Worker 没法自助决策

## 校验

委派前确认 `apps/<m>/.agent/TODO.md` 含本次任务、Worker 启动后能 catch up。
