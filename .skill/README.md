# .skill/ — 项目级 Agent 协作 SOP（根级）

operating procedures（标准操作流程）。

## 项目级 vs 模块级

`.skill/` 分两层：

| 层 | 位置 | 内容 | 维护者 |
|---|---|---|---|
| **项目级根** | `.skill/`（本目录） | 跨多 worker 通用的 agent 协作机制 | Orchestrator |
| **模块级** | `apps/<m>/.skill/`（可选） | 该模块特有的 SOP（含框架 / 测试栈 / 部署方式） | 该模块 Worker |

边界口诀：
- **跨多 worker 都能用** → 根 `.skill/`（如 catch-up / delegate-worker / status-update）
- **仅特定 worker** → 模块 `.skill/`（如 `apps/web/.skill/smoke-test/` 是 Next.js + Playwright 特定）

## 根级边界（本目录不可越过）

- ✅ 仅放 **agent 协作机制**（怎么写 STATUS / 怎么委派 / 怎么 catch up 等）
- ❌ 不放编程语言 / 框架 / 业务知识（Bun / Spring / Next.js 等）→ 进模块级 `apps/<m>/.skill/`
- ❌ 不放 git 工程规范（commit message / branch model 等）

任何根级 SKILL.md 一旦混入"具体编程实践"或"业务规则"，应**下沉到模块级**或**拆出去**。模块级 SKILL.md 反之欢迎包含框架特定实践，但仅限本模块。

## 与 `.agent/` 的关系

- `.agent/` = 角色定义 + 状态（who / what / status）
- `.skill/` = 怎么做（how-to / SOP）

正交。

## 与 superpowers/skills 的关系

- superpowers/skills（`~/.claude/plugins/...`）= 通用 skill（brainstorming / writing-plans 等），跨项目
- `.skill/`（本目录）= 本项目专有 SOP，跟仓库走

## 当前 skill 清单

| skill | 用途 |
|---|---|
| `catch-up` | session 启动时怎么 catch up |
| `status-update` | 怎么写 `.agent/STATUS.md` |
| `learned-rules` | 怎么写 `.agent/learned-rules.md` |
| `decision-log` | 怎么落决策（项目级 vs 模块级） |
| `delegate-worker` | Orchestrator 怎么委派 Worker |
| `worker-summary` | Worker 怎么 return summary 给 Orchestrator |
| `eval-run` | 怎么跑 `.eval/` agent 系统验证 |
| `regression-eval` | 根目录 / SOUL 改动后跑完整 pass^3 + meta-eval 验证 |
| `worker-review` | Worker 交付独立 review（跨 family PI judge，不能 self-judge） |
| `init-agent-teams` | 在已存在项目里初始化 Agent teams（init）+ 体检（check）；自包含、成长型 |

## 引用方式

各 `CLAUDE.md` 中"可用 skills"段链接到本目录的具体 SKILL.md，按需读。
