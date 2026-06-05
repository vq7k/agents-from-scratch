# 2026-06-05 · lesson6 06a §2 重写为 FSM 状态机入门案例

## 触发
user 续 lesson6 → 让把 06a §2「AgentState 是状态机吗」改成「lesson6 状态机设计讲解 / 入门案例 / 图文结合」→ 多轮打磨图与措辞 → "太复杂 / 理论符号劝退" → 去符号 → 折叠不生效 → 挪附录 → 提交 + push。

## 做了什么
- **06a §2 重写**：从辨析「AgentState 是不是 FSM」改为正面「lesson6 的状态机：最小 FSM 入门案例」（2.1 图 / 2.2 选读五元组 / 2.3 转移表 + 代码 / 2.4 机与数据分离 / 2.5 与 06c 订单对照）。全部对齐 `agent/agent.py:411 run_loop`·`:340 agent_step`·`agent/state.py`，代码行号逐一核对。
- **补出第三道终止闸**：原 §1.4 只讲 done + max_steps，补 `agent_step` 连续 3 次解析失败返回 None → `else: break`。
- **状态图三轮迭代**：ASCII 绕线自环（差）→ ASCII 垂直主干 + ⟲ → Mermaid。Mermaid 两轮：`stateDiagram-v2`（`<<choice>>`）→ user 嫌丑 / 挤 / 字大 / 非直角 → 查官方语法换 **flowchart**（`curve: step` 直角 + `nodeSpacing 70` / `rankSpacing 90` 拉开 + `LR` + 菱形判定 + `classDef` 配色）。
- **去理论符号**（user "入门不友好"）：δ / Q / Σ → 工程化措辞（转移规则 / 状态 / 事件）；开头接 user 的订单系统经验；五元组对照表先折叠 → user 反馈 `<details>` 不生效 → **挪文末附录 A**（不依赖渲染器）。
- 配套修正：文首导航同步；配套引用笔误 `06-` → `06c-`；"课本定义" 指名 Sipser / Hopcroft–Ullman；表头 课本含义 → 形式定义含义。
- **答疑（未落正文，纯对话）**：Python 状态机框架（`transitions` / `python-statemachine` / `sismic` / `automat` / 手写 enum+dict）；自动机理论是什么 + SE 专业为何没系统学（CS 必修 / SE 弱化）；理论 FSM vs Java 八股 State Pattern（同源，工程 vs 理论两面）。
- **全局规则**：`~/.claude/CLAUDE.md` 新增「图表 / Mermaid」节 —— 需渲染图默认 **flowchart**（控制力最强：curve / 间距 / 形状 / 配色），stateDiagram 等语义图不暴露样式参数。

## 产出
- `06a-lesson6答疑-agent循环与状态管理.md` 改版（+113 / -19）：§2 重写 + 文末附录 A。
- commit `5d5094b` `docs(lesson6): 06a §2 重写为状态机入门案例` → push `origin/zh-cn`（`023c2f0..5d5094b`）。
- `~/.claude/CLAUDE.md` 图表规则（全局，不在本 repo）。

## 信源
- Mermaid 官方：stateDiagram / flowchart 语法、flowchart config schema（curve / nodeSpacing / rankSpacing）。
- Wikipedia：FSM / DFA / Automata theory / Chomsky hierarchy / State pattern。
- SE vs CS 课程差异（Stack Overflow Blog / UND / 论文）。

## 遗留
- **06a §2.1 的 ASCII 图仍在 `<details>`**：user 渲染器不折叠 → flowchart 下冗余显示。已建议删 ASCII（选项①），**user 未答**。
- **"`<details>` 折叠依赖渲染器、改用附录 / 选读"是否补进全局图表规则** —— user 未答。
- `shared/llm.py` user 在途调试 print（2 行注释）未提交（非主理职责，未碰）。
