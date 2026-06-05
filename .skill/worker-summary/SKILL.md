# skill: worker-summary

Worker 完成阶段任务后怎么 return 给 Orchestrator。

## 何时用

Worker session 完成一个阶段（不一定整个 TODO，可以是单个 task）后。

## 必写的 3 个文件

按这个顺序：

### 1. 更新自己的 `.agent/STATUS.md`

按 `.skill/status-update` 写。重点：完成了什么 / 阻塞 / 下一步。

### 2. 归档本次 session：`.agent/sessions/<YYYY-MM-DD>-<topic>/`

3 个子文件：

```
context.md     # 本次目标 / 约束 / 范围
decisions.md   # 本次决策摘要（细节链向 .agent/decisions/ 或 spec §12）
outputs.md     # 产出物索引（文件路径 / commit hash / 验收证据）
```

### 3. 如有踩坑：追加 `.agent/learned-rules.md`

按 `.skill/learned-rules` 写。

## 然后回 Orchestrator 一份口头 summary

格式（≤ 5 行）：

```
- 完成: <列出 task>
- 文件: STATUS / sessions/<date>-<topic>/ / [learned-rules 如有更新]
- 阻塞: <如有>
- 待 Orchestrator 决策: <如有>
- 下一步: <Worker 自己接着做 / 等 Orchestrator>
```

## 边界 case

- **本次无新决策**：`decisions.md` 写一行"本次无新决策"，**不省略文件**（保持 3 文件结构）
- **本次无踩坑**：**跳过** `learned-rules.md` 更新，**不算缺失**。禁止硬编规则凑数

## 反例

- ❌ 只口头汇报，不写文件 — 下一 session 丢失
- ❌ STATUS.md 没更新 — Orchestrator catch up 时仍是旧状态
- ❌ session 归档目录建了但 3 个文件不齐 — 信息不完整
- ❌ 没踩坑还硬编规则到 learned-rules — 见 `.skill/learned-rules` 反例

## 校验

`ls .agent/sessions/<date>-<topic>/ | wc -l` ≥ 3（context / decisions / outputs）。`grep -E "## (当前阶段|最近一次 session|阻塞|下一步)" .agent/STATUS.md | wc -l` = 4。
