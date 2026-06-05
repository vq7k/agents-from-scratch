# init-agent-teams：runtime 历史对话挖掘

> init 模式 A2 调用。把 Claude Code/Codex 历史**提炼续接**进 Agent teams，而非从 0 填空模板。
> **强约束**：所有提炼产物写入任何文件前，必须**脱敏并过隐私闸**（见 §4）。

## 1. 定位历史源

| runtime | 路径 | 隔离方式 |
|---|---|---|
| Claude Code | `~/.claude/projects/<ENC>/*.jsonl`，`<ENC>` = 目标项目绝对路径把 `/` 换成 `-` | 已按项目目录隔离，直接定位 |
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`（+ `~/.codex/history.jsonl`） | **全局存储**，须读每条 rollout 的 cwd/meta **过滤出属于目标项目**的 |

```bash
# Claude Code：算 ENC + 列 session
TARGET=<目标项目绝对路径>
ENC=$(echo "$TARGET" | sed 's#/#-#g')
ls -lS ~/.claude/projects/"$ENC"/*.jsonl 2>/dev/null   # 按大小排，大的信息多
# Codex：按 cwd 过滤（rollout 头部含 cwd）
grep -rl "$TARGET" ~/.codex/sessions/ 2>/dev/null | head -50
```

## 2. 加载策略（体量大，禁止全量塞上下文）

- 按时间**倒序**（最近 session 最相关）。
- **map-reduce**：每个 session 派一个 SubAgent 抽结构化信号出摘要，再由主 agent 汇总。**不全文读进主上下文**。
- 跨 runtime 合并去重（同项目可能 Claude Code + Codex 都用过）。

### map 阶段 SubAgent prompt template
```text
你是 history-miner SubAgent。读单个 session 文件，抽结构化信号，**不要全文复述**，返回 ≤300 字 JSON。

文件：<单个 .jsonl 绝对路径>

抽取（缺则留空）：
- project_profile: 项目做什么 / 技术栈 / 模块边界（只记证据确凿的）
- division_signals: 反复出现的分工模式（哪类活被分开做 / 谁负责什么）
- decisions: 明确的选型 / 架构决策（一行一条）
- pitfalls: 反复踩的坑 / 被 user 纠正的点（一行一条）
- current_state: 最近在做什么 / 未完成项
- conventions: 已形成的约定 / 偏好

返回 JSON：{project_profile, division_signals[], decisions[], pitfalls[], current_state, conventions[]}
⚠️ 不要把真名/机构/客户等敏感原文放进返回值，遇到用 <REDACTED:类别> 占位。
```

### reduce 阶段（主 agent）
合并所有 SubAgent JSON → 去重 → 产出统一「项目历史画像」：
- `project_profile`/`conventions` → 喂 A1 画像、`PROJECT.md`、`SOUL.md`「我做」
- `division_signals` → A3 角色裁剪**证据**（仅辅助 human 判裂变，不替决策）
- `decisions` → Optional `.agent/decisions/`
- `pitfalls` → Optional `.agent/learned-rules.md`
- `current_state` → `STATUS.md`「当前 actionable / 最近一次 session」+ `TODO.md`

## 3. fallback
目标项目无任何历史（全新启用）→ 跳过本流程，init 仅用 A1 静态侦察。

## 4. 脱敏闸（强约束）
历史对话极可能含真名/机构/客户。**任何提炼产物写入 Agent teams 文件前**：
1. 若已启用 Optional 隐私五层 → 跑 `check-no-leaks.sh <file>`，PASS 才入库。
2. 若未启用隐私模块 → 至少人工核对一遍提炼产物无敏感原文（SubAgent 已用 `<REDACTED:类别>` 占位）。

## 5. 职责边界
挖掘/提炼是 agent 做；**「角色怎么裁、哪些决策/坑入库」仍 human 拍板**。历史是证据输入，不替 human 决策。
