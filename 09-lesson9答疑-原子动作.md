# lesson9 答疑：原子动作

> 本文沉淀学完 lesson9（atomic actions）后的核心理解与 4 个问题：
> 1. 本节课到底要"理解"什么？（§1）
> 2. 原子动作的代码长什么样、Agent 层和 planner 层各做什么？（§2）
> 3. 这一版原子动作有哪些局限、各自留给后续课什么？（§3）
> 4. 它和前后课怎么接上？（§4）
>
> 主线：**原子动作 = 把 lesson8 那种含糊的步骤字符串，转成「带动作名 + 参数」的结构化动作单元**（`{"action": ..., "inputs": {...}}`），目的是让步骤可校验、可执行。但生成它本质仍是"结构化输出换个 schema"——和 lesson3 的 `generate_structured`、lesson8 的 `create_plan` 同一套骨架，只是要的 JSON 形状变成"动作名 + 参数字典"。本课只做这一步转换，**不真执行**。
>
> 怎么读：只看结论翻文末「§5 速查表」；要原理读对应小节。
> 代码锚点：`agent/planner.py:50 create_atomic_action` / `agent/agent.py:583 create_atomic_action`（薄封装）/ `agent/planner.py:90`（那一行校验）/ `complete_example.py:167 lesson_09_atomic_actions`。

---

## 0 主线

lesson8 产出的是一串扁平的步骤字符串；lesson9 取出其中**一个** step，把它转成一个"动作名 + 参数"的结构化动作：

```
lesson8（产出）：goal → {"steps": ["research topic", "create outline", "write draft", ...]}
                                                       │
                                       取出单个 step（一个自由字符串）
                                                       │
                                                       ▼
lesson9（转换）：step "write draft" ──create_atomic_action──> {"action": "generate_text",
                                                               "inputs": {"topic": "...",
                                                                          "length": "..."}}
                  自由文本，给人读                            动作名 + 参数字典，可被校验
                  含糊、难校验                                （但本课不接执行器）
```

两个要点，下面分别展开：
1. 左半边"生成动作"没有任何新机制——它就是结构化输出换了个 schema（§1.2）。
2. 右半边"转成 `{action, inputs}` 这个形状"，才是本课真正立的东西；而这个形状本课**只生成、不执行**（§1.3）。

---

## 1 本节课的重点理解内容

### 1.1 三个新概念

| 概念 | 文档怎么讲 | 代码落点 |
|---|---|---|
| 原子性（Atomicity） | 把动作拆到尽可能小、不可分割，要么整体成功要么整体失败 | prompt 里一句话要求"简单的、原子化的操作名"（planner.py:78） |
| 类型化执行（Typed Execution） | 动作带经过校验的 schema，必须含 `action` 和 `inputs` | 校验只有一行：`if action and "action" in action`（planner.py:90） |
| 确定性（Determinism） | 同一动作给相同输入得相近结果 | `temperature=0.0`（planner.py:87），和前面每课一样 |

三个名词听着都是新东西，但 §1.4 会逐个对齐代码——本课每个都只做了最弱的一版，确定性甚至没有任何新增。

### 1.2 主线命题：又是结构化输出换 schema

`planner.py` 的 `create_atomic_action`（:50）、同文件的 `create_plan`（:11）、`agent.py` 的 `generate_structured`（:126）是**同一个模子**：

```
generate_structured(agent.py:126)    create_plan(planner.py:11)        create_atomic_action(planner.py:50)
  严格要求:只输出合法 JSON 三条        严格要求:只输出合法 JSON 三条        严格要求:只输出合法 JSON 三条
  必须遵循的 schema: {schema}          必须遵循的格式:{"steps":[...]}     必须遵循的格式:{"action":...,"inputs":{...}}
  temperature=0.0                     temperature=0.0                   temperature=0.0
  for attempt in range(3)             for attempt in range(3)           for attempt in range(3)
  extract_json_from_text              extract_json_from_text            extract_json_from_text
  校验: parsed is not None(:174)      校验: "steps" 在且是 list(:44)    校验: "action" 在(:90)
```

差别只有两处：要的 JSON 形状不同（任意 schema / `{"steps":[...]}` / `{"action":..., "inputs":{...}}`），以及那一行校验的强度不同（见 §1.4、§2.3）。**"原子动作"在本课不是新能力，是结构化输出换了个 schema 用。**文档"注意"段第三条「结构化输出 —— 沿用前几课相同的 JSON 模式」（lessons/09_atomic_actions.md:118）说的就是这个。

一个如实的细节：`generate_structured`/`decide` 在 agent.py 里给 prompt 套了 ChatML 三段式外壳（`<|im_start|>...`，agent.py:155-165），而 planner.py 的 `create_plan`/`create_atomic_action` 用的是裸 f-string，没套 ChatML（planner.py:65-84）。这点差异不影响"同一模子"的结论——三段式模板（三条硬约束 + 格式说明 + 待处理内容）、`temperature=0.0`、`range(3)` 重试、`extract_json_from_text` 都一致。

### 1.3 真正的设计点：把步骤变成"动作名 + 参数"的可执行形状（但不执行）

新东西在右半边——把一个自由字符串 step，提炼成 `{"action": ..., "inputs": {...}}` 这个形状。这个形状值得注意，因为它正是**工具调用的形状**：lesson5 的工具调用是 `{"tool": ..., "arguments": {...}}`（agent.py:319），同样是"动作名 + 参数字典"，只是键名不同（详见附录 A）。换句话说，lesson9 把"工具调用的形状"从计划步骤里提炼了出来。

但要看清本课的边界：**它只生成这个形状，不接执行**。文档明说"不实现动作的实际执行——只做转换和校验"（lessons/09_atomic_actions.md:44）。`create_atomic_action` 干的全部事情就是"字符串 step → action dict"这一步转换；产出的 dict 没有任何函数去消费、去执行，它是个悬空的结构。真正的执行器要等 lesson10 的 `execute_graph`（planner.py:150）才出现。

所以 lesson9 的定位是 8→9→10 链条的**中间层**：lesson8 给出扁平步骤，lesson9 把单个步骤塑成可执行单元的形状，lesson10 才把这些单元组织成图并真正跑起来（§4 展开）。

### 1.4 三个概念 vs 代码实际强度（别被名词唬住）

把 §1.1 的三个名词和代码逐个对齐，本课做到的是每个的最弱版本：

| 概念 | 文档怎么立 | 本课代码实际做到 |
|---|---|---|
| 原子性 | "拆到最小、不可分割、要么全成要么全败" | **没有任何机制保证真原子**。只是 prompt 里一句"action 应该是简单的、原子化的操作名"（planner.py:78），模型怎么填就怎么算，代码不检查动作到底原不原子。 |
| 类型化执行 / schema 校验 | "动作带校验的 schema，**必须含 `action` 和 `inputs`**"（lessons/09_atomic_actions.md:117） | 校验只有一行 `if action and "action" in action`（planner.py:90）——**只查 `action` 键在不在，连文档自己承诺的 `inputs` 都没强制检查**（见 §2.3）。 |
| 确定性 | "同输入得相近结果" | 靠 `temperature=0.0`（planner.py:87），和 lesson3 以来每一课完全一样，**无任何新东西**。 |

为什么校验这么虚？不是作者偷懒，是 schema 的**开放性**决定的。把校验强度排一下：

| 课 | 产出 schema | 校验 | 强度 |
|---|---|---|---|
| lesson4 `decide` | `{"decision": 枚举之一}` | `decision in choices`（agent.py:249） | 最严：值必须在白名单里 |
| lesson5 `request_tool` | `{"tool":..., "arguments":{...}}` | 两个键都查（agent.py:319）；执行时 `tool` 还要在白名单（tools.py:80） | 较严 |
| lesson8 `create_plan` | `{"steps": [...]}` | `"steps"` 在且是 list（planner.py:44） | 中 |
| lesson9 `create_atomic_action` | `{"action":..., "inputs":{...}}` | 只查 `"action"` 在（planner.py:90） | 最弱 |

`decide` 的 schema 是**封闭枚举**——动作只能是 `choices` 里那几个，所以能拿"值是否 in choices"去卡。`create_atomic_action` 的 schema 是**开放结构**——`action` 名是任意字符串、`inputs` 是任意字典，没有白名单可对，所以它的校验天然只能退化到"键在不在"。校验之虚，是开放 schema 的固有结果，不是实现疏忽。

---

## 2 原子动作的代码结构

### 2.1 两层：Agent 层比 lesson8 还薄

```
Agent.create_atomic_action(step)        # agent.py:583，薄封装
  └─ return create_atomic_action(self.llm, step)   # agent.py:601，纯转发
```

planner 层（`planner.py` 的 `create_atomic_action`）是纯函数：进 `llm` + `step`，出动作字典，不碰状态。Agent 层（agent.py:583）比 lesson8 的 `create_plan` 还薄——lesson8 那个封装至少多做一件事（成功后 `self.state.current_plan = plan`，agent.py:549），而本课的封装连状态都不存，就一行 `return`（agent.py:601）。这是"机/数据分离"的延续，只是本课连"写一笔状态"都还不需要。

### 2.2 planner 层逐行看

```python
def create_atomic_action(llm, step):              # planner.py:50
    prompt = f"""将这个步骤转换为一个原子动作。只输出合法的 JSON。
    ...（三条硬约束）...
    必须遵循的格式: {{"action": "动作名", "inputs": {{"参数名": "参数值"}}}}
    action 应该是一个简单的、原子化的操作名称。    # planner.py:78，唯一"原子性"约束，纯措辞
    inputs 应该是一个字典,包含该动作所需的参数。    # planner.py:79
    待转换的步骤: {step}"""
    for attempt in range(3):                       # planner.py:86，三次重试
        response = llm.generate(prompt, temperature=0.0)   # planner.py:87
        action = extract_json_from_text(response)  # planner.py:88
        if action and "action" in action:          # planner.py:90，唯一校验
            return action                          # planner.py:91
    return None
```

和 `create_plan`（planner.py:11）并排看，骨架逐行同构；唯一实质差异就是第 90 行那句校验，以及 prompt 里要的格式。

### 2.3 校验只有一行，且只查 action——文档与代码不一致

这是本课最该如实记下的一点。文档在两处明确承诺动作必须**同时**含 `action` 和 `inputs`：

- 概念段"类型化执行"：「动作必须包含 "action" 和 "inputs" 字段」（lessons/09_atomic_actions.md:117）。
- "常见问题 / 校验失败"：「检查动作是否同时包含 "action" 和 "inputs" 字段」（lessons/09_atomic_actions.md:189）。

但实现里那一行是：

```python
if action and "action" in action:   # planner.py:90
    return action
```

**只查 `action` 键，根本没查 `inputs`。**一个只有 `{"action": "generate_text"}`、缺了 `inputs` 的返回值照样通过、照样被返回。文档承诺的"必须同时含两个字段"在代码里没有兑现。

更能说明问题的是：文档"常见问题"里自己又写了一条「考虑为 `inputs` 增加 schema 校验」（lessons/09_atomic_actions.md:191）——等于作者自认 `inputs` 这层校验没做，是留给读者的练习。所以读这一课时，把"类型化执行 / schema 校验"理解成"立了概念、给了最小骨架（只卡一个键）"，别以为参数真被校验过。

---

## 3 这一版原子动作的局限，及各自留给后续课什么

| 局限 | 本课现状 | 留给哪一课 |
|---|---|---|
| 校验太浅 | 只有 planner.py:90 一行查 `action` 键，`inputs` 不查（§2.3） | lesson10 的节点校验查 `id`/`action`/`depends_on` 三键在不在 + `depends_on` 是 list（planner.py:138-140）；但 `inputs` / 参数内容**仍然不校验**，这层校验后续课也没真正补上 |
| 不真执行 | `create_atomic_action` 只做"字符串 → `{action, inputs}`"转换，产物悬空、无人消费（§1.3） | lesson10 的 `execute_graph`（planner.py:150）接 `executor_func` 真执行，`result = executor_func(node["action"])`（planner.py:188） |
| 原子性无机制保证 | 全靠 prompt 一句话 + 模型自觉，代码不检查（§1.4） | 无专门后续——这是开放 schema 的固有限制，框架不强制，只能靠 prompt 引导 |

三条里，前两条是 lesson10 接着补的方向，第三条则是结构性的——只要 `action` 名是开放字符串，"是否原子"就没法用代码判定。本课的策略和 08 一致：先把"步骤 → 动作单元"这件事的**结构**立起来（生成 `{action, inputs}`），把**深度**（校验多严、参数怎么卡、动作怎么执行）留给后面。

---

## 4 和前后课怎么接上

lesson9 卡在 8 和 10 中间，承上启下。把三课的产物并排，演进一目了然：

```
lesson8                    lesson9                        lesson10
{"steps":[                 取出单个 step                   {"nodes":[
  "research topic",  ───>  "research topic"        ───>      {"id":"1","action":"research","depends_on":[]},
  "write draft",           转成                              {"id":"2","action":"write","depends_on":["1"]}
  ...]}                    {"action":"research",           ]}
                            "inputs":{...}}
扁平字符串列表             孤立的 {action, inputs}          带 depends_on 的依赖图
顺序执行（占位）           不执行                          execute_graph 拓扑执行（真执行）
create_plan(:11)          create_atomic_action(:50)       create_aot_graph(:96)+execute_graph(:150)
```

接上的关键：lesson10 图节点的 `action` 字段（planner.py:119 的格式示例、:138 的校验），就是 lesson9 这层产物里那个 `action` 的雏形。

- **承上（接 lesson8）**：lesson8 的 `steps` 是一串自由字符串，含糊、难校验。lesson9 取其中一个，塑成"动作名 + 参数"的结构。它解决的正是 08 答疑 §1.4 点出的"步骤是含糊字符串"那条局限——不过解决得很轻，只换了形状，没加真校验。
- **启下（接 lesson10）**：lesson9 产出的是**孤立**动作（无依赖、不执行）。lesson10 把多个这样的动作组织成带 `depends_on` 的图，并用 `execute_graph` 按依赖拓扑执行（planner.py:173-205），还接上了真执行器 `executor_func`。lesson9 的 `{action, inputs}` 是那张图里单个节点的雏形。

一条贯穿线（接 06/07/08）：

| 课 | 把什么做成显式数据 | schema 形状 | 校验强度 | 产物去向 |
|---|---|---|---|---|
| lesson3 | 任意结构化输出 | `{schema}` | 非空即可 | 直接返回 |
| lesson4 | 决策 | `{"decision": 枚举}` | 值 in choices（最严） | 直接返回 |
| lesson8 | 多步任务的步骤 | `{"steps":[...]}` | steps 是 list | 存 `current_plan` |
| lesson9 | 单个步骤的动作单元 | `{"action":..., "inputs":{...}}` | 只查 action 键（最弱） | 悬空，待 lesson10 |

从 lesson3 到 lesson9 是同一台机器——"结构化输出 + 校验 + 重试"，差别只在三处：schema 形状、校验强度、产物去向。lesson9 校验最弱，正因为它的 schema 最开放（§1.4）。

---

## 5 速查表

| 问题 | 一句话结论 |
|---|---|
| 本课要 get 什么 | 原子动作 = 把含糊步骤字符串转成 `{"action":..., "inputs":{...}}`；生成它仍是结构化输出换 schema |
| 是新能力吗 | 不是。`create_atomic_action` 和 `create_plan`、`generate_structured` 同一模子（模板 + `temperature=0.0` + `range(3)` 重试 + `extract_json`） |
| 真正新增的是什么 | "动作名 + 参数"这个形状（= 工具调用的形状）；但本课只生成形状，不接执行 |
| 校验有多强 | 一行 `if action and "action" in action`（planner.py:90）：只查 `action` 键，`inputs` 不查 |
| 文档 vs 代码 | 文档说"必须含 `action` 和 `inputs`"（md:117/189），代码只查 `action`；文档自己又写"考虑为 inputs 增加校验"（md:191），等于自认没做 |
| 为什么校验这么弱 | schema 是开放结构（action 名任意、inputs 任意），没有白名单可对；对照 `decide` 是封闭枚举所以最严 |
| 真执行吗 | 不。只做"字符串 → action dict"转换，产物悬空，执行留给 lesson10 `execute_graph` |
| "原子性"由谁保证 | 没机制保证。靠 prompt 一句"原子化操作名" + 模型自觉 |
| 在 8→9→10 里的位置 | 中间层：8 出扁平步骤 → 9 塑成孤立动作单元 → 10 组织成依赖图并真执行 |

---

## 附录 A：原子动作的形状 ↔ lesson5 工具调用（选读）

lesson9 的 `{action, inputs}` 和 lesson5 的工具调用几乎是同一个东西，并排看最清楚（全部基于本仓库代码）：

| | lesson5 工具调用 | lesson9 原子动作 |
|---|---|---|
| 产出形状 | `{"tool": "calculator", "arguments": {"a":42, "b":7, "operation":"multiply"}}` | `{"action": "generate_text", "inputs": {"topic":"...", "length":"..."}}` |
| 动作名键 | `tool` | `action` |
| 参数键 | `arguments` | `inputs` |
| 生成处 | `request_tool`（agent.py:258） | `create_atomic_action`（planner.py:50） |
| 校验 | `"tool"` 和 `"arguments"` **都查**（agent.py:319） | 只查 `"action"`（planner.py:90） |
| 动作名取值 | 闭集：执行时 `tool` 必须在 `tools` 字典里，否则 `raise ValueError`（tools.py:80） | 开集：`action` 是模型随便填的任意字符串 |
| 谁执行 | `execute_tool` 真执行——`return tools[tool_name](**arguments)`（tools.py:83），把参数解包传给真实 Python 函数 `calculator` | 无人执行，产物悬空 |

两个结论：

1. **形状同源**：lesson9 等于把 lesson5"工具调用"的形状（动作名 + 参数字典）从计划步骤里重新提炼了一遍。理解了工具调用，就理解了原子动作的结构。
2. **lesson9 反而比 lesson5 更弱**：lesson5 的工具调用校验两个键（agent.py:319），且执行阶段有白名单兜底（tools.py:80）、有真执行器（tools.py:83）；lesson9 只校验一个键、动作名是开集、且完全不接执行。原因还是 §1.4 那条——lesson5 的工具名是闭集（`tools` 字典就那么几个），能卡白名单；lesson9 的动作名是开集，卡不了。lesson9 提炼出了形状，但把校验和执行都留到了后面。

本节全部基于本仓库已有代码，无外部信源。

---

**核心要点：** 原子动作 = 把 lesson8 的含糊步骤字符串，转成"动作名 + 参数"的结构化动作单元 `{"action":..., "inputs":{...}}`。生成它和 lesson3/lesson8 是同一台"结构化输出 + 校验 + 重试"的机器，只是 schema 形状变了。本课真正新增的只是这个形状本身（= 工具调用的形状），而校验只卡一个 `action` 键（连文档承诺的 `inputs` 都没查）、动作不真执行——这些都是有意留给 lesson10 的骨架，校验之弱则是开放 schema 的固有结果。
