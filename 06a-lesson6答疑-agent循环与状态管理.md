# lesson6 答疑：Agent 循环与状态管理

> 本文沉淀学完 lesson6（agent loop）后的核心理解与 3 个问题：
> 1. 本节课到底要"理解"什么？（§1）
> 2. `AgentState` 是状态机吗？（§2）
> 3. 怎么理解 Agent 的状态管理？（§3）
>
> 主线：**Agent = 循环 + 状态**。lesson6 用最小代码立起"观察→决策→行动不断重复 + 带状态"的骨架；但这一版的"连续性"刻意很弱（只把 `steps`/`done` 喂回 prompt），真正的历史回灌留到 lesson7（memory）。
>
> 怎么读：只看结论翻文末「§4 速查表」；要原理读对应小节。
> 配套：状态机（FSM）本身是什么、怎么应用、怎么落到业务，见 `06-状态机-从概念到订单流转设计.md`。
> 代码锚点：`agent/agent.py:340 agent_step` / `agent/agent.py:411 run_loop` / `agent/state.py AgentState`。

---

## 0 主线

```
聊天机器人：响应一次 → 停。
Agent：观察 → 决策 → 行动 → 重复，直到终止。  ← 多了"循环"和"状态"两样东西

lesson6 立的骨架：
  run_loop ── while not done and steps < max_steps ──> 反复调用 agent_step
                                                          │
                          每步：读状态(steps/done) → 拼 prompt → 问 LLM → 拿到 action → 改状态
                                                          │
                          终止：LLM 发 "done" 动作  或  steps 撞上 max_steps
```

关键：循环带来"多步行为"，状态带来"连续性"——但这一版连续性很弱，见 §1.3。

---

## 1 本节课的重点理解内容

### 1.1 主命题：Agent = 循环 + 状态

chatbot 响应一次就停；agent 是 `observe → decide → act` 不断重复，且带 state。文档原话："Agent 不是一个聪明的 prompt，它是一个**带状态的循环**。神奇之处不在 prompt 里——而在那个不断重复的循环。"

### 1.2 三个新概念

| 概念 | 是什么 | 代码落点 |
|---|---|---|
| Agent Loop（循环） | observe→decide→act 重复 | `run_loop` (agent.py:411) |
| State Transitions（状态转移） | 状态随每步变化（steps/done） | `AgentState`（state.py） |
| Termination（终止条件） | 何时停：`done` 信号 / `max_steps` | `while not done and steps<max` |

### 1.3 真正要 get 的点：这一版的"连续性"其实很弱（刻意的）

文档高调说"状态带来连续性"，但**最小实现的连续性几乎是空的**，这是有意为之：

1. `run_loop` 每一步都把**同一个初始 `user_input`** 传给 `agent_step`（不变）；
2. 喂进 prompt 的"状态"只有 `steps` 和 `done` **两个值**——**前几步的 action 结果（`results`）根本没回灌进 prompt**；
3. `temperature=0.0` → LLM 每轮看到的唯一变量就是 `steps` 计数器。

→ 所以文档明说"前几轮出现重复是正常的"。把上一步结果喂回去 = **lesson7（memory）才补**。lesson6 只立"重复行动 + 不跑飞"这副骨架。

### 1.4 两道终止闸

`while not self.state.done and self.state.steps < max_steps`：

- **`done` 动作**：LLM 主动输出 `{"action":"done"}` → `run_loop` 调 `mark_done()` 置 `done=True`（智能终止）。
- **`max_steps`**：安全阀，防 LLM 永远不发 done 时无限循环（兜底终止）。

缺一不可：只有前者，模型不发 done 就跑飞；只有后者，每次都要跑满 max_steps。

---

## 2 `AgentState` 是状态机吗？

### 2.1 结论：不是 FSM，是"显式状态容器"（state container）

`AgentState` 是一个**数据对象 + 几个 mutator 方法**，存的是"一组变量的当前值"（`steps`/`done`/`current_plan`/`last_action`），不是"当前处于哪个状态"。它不是有限状态机。

### 2.2 FSM 判据对照

| FSM 要素 | AgentState 实际 |
|---|---|
| 有限离散的命名状态 | ❌ `steps` 是无界整数（0,1,2…），不是有限态 |
| 转移函数 δ:(S×E→S') | ❌ `increment_step()` 只是 `steps += 1`，直接改字段，无转移规则 |
| 任意时刻"处于"某一态 | ❌ 它同时持有多个独立变量，不是"处在哪个态" |

（FSM 的完整定义见配套文档 `06-状态机-...md` §1。）

### 2.3 那台"机"在 `run_loop` 里（机与数据分离）

如果硬要在 lesson6 里找状态机，它在 `run_loop` 的控制流，不在 `AgentState`：

```
状态 {RUNNING, DONE}
RUNNING ──(LLM 返回 done 动作 / steps≥max / agent_step 返回 None)──> DONE
```

转移规则就写在 `while not done and steps < max` 这行 + 里面的 `if`。
**`run_loop` 是那台两态机；`AgentState` 是这台机读写的"寄存器/内存"。机与数据分离。**

---

## 3 怎么理解 Agent 的状态管理

`state.py` 文件头那句是设计哲学（呼应 PHILOSOPHY「没有魔法」）：

> 状态是显式的、可检视的、可修改的。它不会隐藏在对话历史里，也不会藏在某种神秘的上下文中。

### 3.1 显式 vs 隐式（藏在对话历史）

- **隐式**：很多框架把状态藏在 conversation history / context 里——把所有历史拼进 prompt，让 LLM"自己记"。你看不见、改不了。
- **本课（显式）**：状态是一个独立 Python 对象，字段一眼看穿，能 `print`、能断点、能手改。**LLM 不负责记状态，代码负责记状态。**

### 3.2 状态管理三动作：读 / 写 / 重置

| 动作 | 方法 | 在循环里何时发生 |
|---|---|---|
| 读 | `to_dict()` → 注入 prompt | 每步开头，让 LLM 看见 steps/done（**状态影响决策的唯一通道**） |
| 写 | `increment_step()` / `mark_done()` | 每步 +1；收到 `done` 动作时置真 |
| 重置 | `reset()` | 新任务开始（`run_loop` 第一行） |

### 3.3 一个易忽略点：预留但未用的字段

`AgentState.__init__` 里有 **4 个字段**，但 lesson6 的 `agent_step`/`run_loop` **只读写 `steps` 和 `done`**——`current_plan` / `last_action` 是上游为后续课**预埋**的（注释写明：07 记忆 / 08 规划 / 09 执行 / 10 依赖）。所以本课真正"活"的状态只有两个：**步数计数器 + 完成标志**。

---

## 4 速查表

| 问题 | 一句话结论 |
|---|---|
| 本课要 get 什么 | Agent = 循环 + 状态；循环带多步行为，状态带连续性 |
| 为什么前几轮重复 | 每步喂同一 input，状态只回灌 steps/done，temp=0 → 输入几乎没变（刻意，lesson7 补） |
| 两道终止闸 | `done` 动作（智能）+ `max_steps`（兜底），缺一不可 |
| AgentState 是 FSM 吗 | 不是，是"显式状态容器"（数据对象） |
| 那台 FSM 在哪 | 在 `run_loop`（两态 RUNNING/DONE）；机与数据分离 |
| 状态管理本质 | 显式管理：读(to_dict→prompt)/写(increment/mark_done)/重置(reset) |
| 真正活跃的状态 | 只有 `steps` + `done`；`current_plan`/`last_action` 是后续课预埋 |
