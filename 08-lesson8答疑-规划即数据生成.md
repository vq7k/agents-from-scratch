# lesson8 答疑：规划即数据生成

> 本文沉淀学完 lesson8（planning）后的核心理解与 4 个问题：
> 1. 本节课到底要"理解"什么？（§1）
> 2. 规划系统的代码长什么样、Agent 层和 planner 层各做什么？（§2）
> 3. 这一版规划有哪些局限、各自留给后续课什么？（§3）
> 4. 它和前面几课怎么接上？（§4）
>
> 主线：**规划不是推理，是数据生成**。"计划"就是一个 JSON 数据结构 `{"steps": [...]}`，生成它和 lesson3 让模型吐结构化 JSON 是同一件事——同样的 prompt 模板、同样的三次重试、同样的 `extract_json`，只是这次要的 JSON 恰好叫"步骤列表"。所以本课没有新机制；真正新的设计点是把**规划和执行拆成两步**，让计划在执行前可看、可改、可校验。
>
> 怎么读：只看结论翻文末「§5 速查表」；要原理读对应小节。
> 代码锚点：`agent/agent.py:534 create_plan` / `agent/agent.py:553 execute_plan` / `agent/planner.py:11 create_plan` / `complete_example.py:151 lesson_08_planning`。

---

## 0 主线

```
chatbot / 单步：给一个目标 → 直接做（或直接答）。

lesson8（两步）：
  目标 ──create_plan──> 计划（一个 JSON 数据结构）   ← 规划：生成步骤列表，不动手
       {"steps": ["research", "outline", "write", "review"]}
                                │
                                │  这中间你可以 print 它、改它、校验它
                                ▼
  计划 ──execute_plan──> 逐步执行 → 结果列表           ← 执行：遍历 steps，真正去做
```

两个关键点，下面分别展开：
1. 左半边"生成计划"没有任何新机制——它就是结构化输出（§1.2）。
2. 右半边和左半边**分开**，才是本课真正立的东西（§1.3）。

---

## 1 本节课的重点理解内容

### 1.1 三个新概念

| 概念 | 是什么 | 代码落点 |
|---|---|---|
| 规划 vs 执行 | 生成步骤（规划）与真正去做（执行）拆成两步 | `create_plan`(534) / `execute_plan`(553) |
| 步骤排序（Step Ordering） | 各步的先后顺序，可能有依赖 | 本课按 `steps` 列表顺序执行，无依赖（§3） |
| 校验（Validation） | 执行前检查计划合不合法 | `planner.py:44` 一行结构检查 |

### 1.2 主线命题：规划 = 结构化输出 + 一个特定 schema

`planner.py` 的 `create_plan`（:11）和 lesson3 的 `generate_structured`（agent.py:126）是**同一个模子**：

```
generate_structured（lesson3）        create_plan（lesson8）
  严格要求: 只输出合法 JSON …            严格要求: 只输出合法 JSON …
  必须遵循的格式: {schema}               必须遵循的格式: {"steps": ["步骤1", ...]}
  for attempt in range(3):              for attempt in range(3):
      response = llm.generate(...)          response = llm.generate(...)
      parsed = extract_json_from_text       plan = extract_json_from_text
      校验通过就返回                          校验通过就返回
```

差别只有一处：要的 JSON 形状不同——一个是任意 schema，一个固定是 `{"steps": [...]}`。**"规划"在本课不是新能力，是结构化输出换了个 schema 用。**文档「规划 = 数据生成，不是高深推理」「模型生成一个步骤列表，就跟它生成任何其他结构化输出一样」说的就是这个。理解了这点，本课左半边就没有任何神秘的地方。

### 1.3 真正的设计点：规划与执行分离

新东西在右半边——`create_plan` 只生成、**不做任何事**；`execute_plan` 才遍历步骤。为什么要拆开（文档列的四条价值）：

- 执行前能 `print(plan)` 看模型"打算怎么做"；
- 能在动手前手动改计划（练习 2 就是这个）；
- 能不执行就单独调试 / 测试规划；
- 同类目标能复用计划。

一句话：分离让你在 Agent 动手之前，先检查它的意图。这是本课唯一真正新增的结构。

### 1.4 三个概念的实际强度（要看清，别被名词唬住）

文档把"校验""步骤排序"立成概念，但本课代码做的是每个的最弱版本。把名词和代码对齐：

| 概念 | 文档怎么立 | 本课代码实际做到 |
|---|---|---|
| 校验 | "检查计划是否合法、结构对不对、步骤合不合理" | 只有一行：`"steps" in plan and isinstance(plan["steps"], list)`（planner.py:44）。**只查 steps 键在不在、是不是 list**，不查步骤内容、顺序、能不能执行。 |
| 步骤排序 | "步骤间可能有依赖" | 本课**无依赖**。`steps` 是扁平字符串列表，`execute_plan` 顺序 for 循环跑完，谁先谁后全看模型生成的顺序。 |
| 执行 | "按顺序执行步骤" | 占位。`result = {"step": step, "executed": True}`（agent.py:570），**没调任何工具**，只标了个 True。 |

这不是缺陷，是本课的范围划定——文档明说执行是占位、依赖留给第10课、原子动作校验留给第09课。读的时候把这三个名词理解成"立了概念、给了最小骨架"，别以为已经实现到位。

---

## 2 规划系统的代码结构

### 2.1 两层：Agent 层是薄封装，干活在 planner 层

```
Agent.create_plan(goal)         # agent.py:534，薄封装
  └─ plan = create_plan(llm, goal)   # 调 planner.py:11，真正生成
     if plan:
         self.state.current_plan = plan   # agent.py:549，多做的唯一一件事：把计划存进状态
     return plan
```

planner 层（`planner.py` 的 `create_plan`）是纯函数：进 `llm` + `goal`，出计划字典，不碰状态。Agent 层只比它多做一件事——成功后把计划写进 `self.state.current_plan`。这呼应 lesson6 的"机/数据分离"：生成逻辑（planner）和状态存储（AgentState）是分开的。

### 2.2 execute_plan 是占位执行（逐行看）

```python
def execute_plan(self, plan: dict) -> list:
    if not plan or "steps" not in plan:      # 守卫：没有 steps 直接返回空
        return []
    results = []
    for step in plan["steps"]:               # 顺序遍历，无依赖判断
        result = {"step": step, "executed": True}   # 占位：不调工具，只标 executed
        results.append(result)
        self.state.increment_step()          # 复用 lesson6 的步数计数器
    return results
```

注意 `increment_step()`（agent.py:575）是 lesson6 那个 `AgentState` 的方法——执行每个 step 都让 `steps` 加一。规划这一课没有自己的循环控制，借的是 lesson6 立的状态。

### 2.3 你打开的 planner.py 横跨三课

`planner.py` 一个文件装了 08/09/10 三课的函数，`agent.py:27` 一次性全导入。lesson8 只用第一个：

| 函数 | 课次 | 产出 | 执行方式 |
|---|---|---|---|
| `create_plan`(11) | **08** | `{"steps": [...]}` 扁平列表 | `execute_plan` 顺序跑 |
| `create_atomic_action`(50) | 09 | `{"action": ..., "inputs": {...}}` | 把一个步骤变成带参数的动作 |
| `create_aot_graph`(96) + `execute_graph`(150) | 10 | `{"nodes": [{id, action, depends_on}]}` 依赖图 | `execute_graph` 按依赖**拓扑执行** |

直接对照能看清演进：你现在觉得 lesson8 的"顺序执行、无依赖"弱，弱点正是 lesson10 的 `execute_graph` 要补的——它按 `depends_on` 决定谁先跑（详见附录 A）。lesson8 的扁平 `steps` 是那张依赖图的退化版（所有步骤依赖为空、纯线性）。

---

## 3 这一版规划的局限，及各自留给后续课什么

| 局限 | 本课现状 | 留给哪一课 |
|---|---|---|
| 校验太浅 | 只查 `steps` 是不是 list（§1.4） | 第09课：把步骤转成带 schema 校验的原子动作 |
| 顺序执行、无依赖 | 扁平 `steps`，for 循环顺序跑 | 第10课：AoT 依赖图 + 拓扑执行（`execute_graph`） |
| 执行是占位 | 只标 `executed: True`，不调工具 | 第09课起接真实动作；模式比实现重要（文档原话） |

三条其实是同一件事的三个侧面：lesson8 把"多步任务"这件事的**结构**先立起来（生成步骤 → 逐个执行），把每一环的**深度**（校验多严、依赖怎么排、执行调什么）都留给后面。先有能跑的骨架，再逐环加厚。

---

## 4 和前面课怎么接上

- **兑现预留字段**：06a §3.3 提过 `AgentState` 里 `current_plan` 字段一直空着没用——lesson8 就是它的兑现，`create_plan` 成功后 `self.state.current_plan = plan`（agent.py:549）。
- **借用 lesson6 的状态**：`execute_plan` 每步调 `increment_step()`，用的是 lesson6 那个步数计数器（§2.2）。
- **一条贯穿线**：

| 课 | 把什么做成显式数据 | 存在哪 |
|---|---|---|
| lesson6 | 循环状态（`steps`/`done`） | `AgentState` |
| lesson7 | 跨交互的事实 | `Memory.items` |
| lesson8 | 多步任务的步骤 | `current_plan` 里的 `{"steps": [...]}` |

三课都是同一主张：把该管的东西做成**可看、可改的显式数据结构**，而不是让模型在脑子里"自己想"。lesson8 把这主张用到"任务怎么拆"上——计划是数据，不是思想。

---

## 5 速查表

| 问题 | 一句话结论 |
|---|---|
| 本课要 get 什么 | 规划 = 结构化输出换个 schema（`{"steps":[...]}`）；真正新的是规划/执行分离 |
| "规划"是新能力吗 | 不是。`create_plan` 和 lesson3 `generate_structured` 同构，只是 JSON 形状固定 |
| 分离规划和执行图什么 | 执行前能看/改/校验/复用计划——动手前先检查意图 |
| 校验有多强 | 一行：只查 `steps` 是不是 list；不查内容/顺序/可执行性 |
| 步骤有依赖吗 | 没有。扁平列表顺序执行，依赖留给第10课 |
| 执行真做事吗 | 没有。占位，只标 `executed: True`，不调工具 |
| planner.py 为什么这么多函数 | 它横跨 08/09/10；lesson8 只用 `create_plan` |
| 和前面课的关系 | 兑现 `current_plan` 预留字段 + 借 lesson6 的 `increment_step`；延续"显式数据"主线 |

---

## 附录 A：从扁平 steps 到依赖图（选读）

`planner.py` 同文件里就放着 lesson8 的进化版，直接对照能看清"顺序执行"被换成什么：

```
lesson8  execute_plan（agent.py:553）          lesson10  execute_graph（planner.py:150）
  for step in plan["steps"]:                     while 还有没执行完的节点:
      执行 step                                      for node in nodes:
      （谁先谁后 = 模型生成的顺序）                       if 该节点的 depends_on 都已执行:
                                                            执行 node，记入 executed
  数据形状: {"steps": ["a","b","c"]}              数据形状: {"nodes":[{id,action,depends_on}]}
  排序依据: 列表先后                                排序依据: 依赖关系（拓扑执行）
```

要点：

- lesson8 的"步骤排序"是隐式的——顺序就是列表里的先后，模型怎么排就怎么跑，代码不判断。
- lesson10 把顺序变成**显式依赖**：每个节点声明 `depends_on`（它依赖哪些节点），`execute_graph` 反复扫描，只执行"依赖都已完成"的节点（planner.py:185），这是标准的拓扑执行（其注释自称"简单的拓扑执行"）。它还处理了执行失败（标记已执行避免死循环，planner.py:204）和兜底迭代上限（`max_iterations`，:170）。
- 所以 lesson8 的扁平 `steps` 等价于"一张所有节点 `depends_on` 都为空、被强行排成一条线"的退化依赖图。理解了这个对照，lesson8 顺序执行的局限和它为什么留到 lesson10，就一目了然。

这一节全部基于本仓库已有代码，无外部信源。

---

**核心要点：** 规划 = 数据生成，不是推理。计划是一个 `{"steps":[...]}` 的 JSON 数据结构，生成它和任何结构化输出无异；本课真正新增的是把规划和执行拆开，让计划在执行前可看、可改、可校验。校验之浅、执行之空、排序之无依赖，都是有意留给 09/10 课的骨架。
