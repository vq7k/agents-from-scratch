# lesson10 答疑：AoT 依赖图

> AoT = Atom of Thought（思维原子）。本文沉淀学完 lesson10（AoT）后的核心理解与 4 个问题：
> 1. 本节课到底要"理解"什么？（§1）
> 2. `execute_graph` 这个真执行器怎么按依赖跑？（§2）
> 3. 这一版 AoT 的名实落差在哪——校验和并行各自承诺了什么、代码实际做到什么？（§3）
> 4. 它和前面几课怎么接上，整门课怎么收口？（§4）
>
> 主线：**AoT = lesson8 的规划 + lesson9 的原子动作 + 依赖关系，三者合成一张依赖图。`execute_graph` 是整门课第一个真正的执行器（拓扑执行）。但"生成图"那一步仍是"结构化输出换 schema"的老骨架，执行动作本身仍是占位。AoT 不是高级推理，是更好的结构——这正是全课的收口主题"没有魔法"。**
>
> 怎么读：只看结论翻文末「§5 速查表」；要原理读对应小节；想看环依赖怎么崩看「附录 A」。
> 代码锚点：`agent/agent.py:607 create_aot_plan` / `agent/agent.py:621 execute_aot_plan` / `agent/planner.py:96 create_aot_graph` / `agent/planner.py:150 execute_graph` / `complete_example.py:190 lesson_10_aot`。

---

## 0 主线

从 lesson8 到 lesson10，变的只是"计划"这个数据结构的形状：

```
lesson8（扁平 steps）：
  目标 ──create_plan──> {"steps": ["research", "write"]}
                          └─ 扁平字符串列表，顺序 = 列表先后，无依赖
                          └─ execute_plan 顺序 for 循环跑完

lesson10（依赖图 nodes）：
  目标 ──create_aot_graph──> {"nodes": [
                               {"id": "1", "action": "research", "depends_on": []},
                               {"id": "2", "action": "write",    "depends_on": ["1"]}
                             ]}
                          └─ 每个 node 三字段：id / action / depends_on
                          └─ execute_graph 反复扫描，谁的依赖都满足了才执行（拓扑执行）
```

两件事下面分别展开：
1. 左半边"生成图"没有任何新机制——还是结构化输出，只是 schema 长了（§1.2）。
2. 右半边 `execute_graph` 是本课真正新增的东西——整门课第一个真执行器（§2）。

数据结构的演进可以拆成三块，看清"本课到底新增了什么"：

| 字段 | 来自哪一课 | 本课的角色 |
|---|---|---|
| `action`（如 "research"、"write"） | lesson9 的原子动作（`create_atomic_action`，planner.py:50） | 每个节点是一个原子动作 |
| 节点列表本身（一个目标拆成多步） | lesson8 的规划（`create_plan`，planner.py:11） | 把 `steps` 列表升级成 `nodes` 列表 |
| **`depends_on`（依赖哪些节点）** | **本课唯一新增** | 把"顺序"从隐式的列表先后，变成显式的依赖声明 |

所以 lesson10 没有发明新能力，它把前两课的产物拼在一起，只多加了 `depends_on` 一个字段，再配一个能读这个字段的执行器。

---

## 1 本节课的重点理解内容

### 1.1 三个新概念

| 概念 | 是什么 | 代码落点 |
|---|---|---|
| 原子化规划（Atomic Planning） | 把计划构建成依赖图，每个节点是一个原子动作 | `create_aot_graph`（planner.py:96） |
| 依赖解析（Dependency Resolution） | 按 `depends_on` 决定执行顺序，依赖满足才能跑 | `execute_graph` 的 `all(...)` 判断（planner.py:185） |
| 校验式执行（Validated Execution） | 执行前检查图结构（文档说要查环、查引用、查必需节点） | `create_aot_graph` 的校验段（planner.py:134-145）——但实际只查字段，见 §3 |

文档把这三者讲清了一件事：依赖图让"谁先谁后"从模型生成的列表顺序里解脱出来，变成节点之间的显式声明。这是本课立的概念。但概念立得满，代码做到哪一步，要看 §1.4 和 §3。

### 1.2 主线命题：生成图 = 结构化输出 + 一个更长的 schema

`create_aot_graph`（planner.py:96）和 lesson8 的 `create_plan`（planner.py:11）、再往前 lesson3 的 `generate_structured`（agent.py:126）是**同一个模子**：

```
generate_structured（03）   create_plan（08）        create_aot_graph（10）
  严格要求: 只输出 JSON       严格要求: 只输出 JSON      严格要求: 只输出 JSON
  必须遵循: {schema}          必须遵循: {"steps":[...]}  必须遵循: {"nodes":[{id,action,depends_on}]}
  for attempt in range(3):   for attempt in range(3):  for attempt in range(3):
      llm.generate(...)          llm.generate(...)         llm.generate(...)
      extract_json_from_text     extract_json_from_text    extract_json_from_text
      校验通过就返回              校验通过就返回             校验通过就返回
```

差别只有一处：要的 JSON 形状不同——schema 从扁平列表变成了带 `id/action/depends_on` 三字段的节点列表。**"生成依赖图"在本课不是新能力，是结构化输出换了个更复杂的 schema 用。**这条线从 lesson3 一路贯穿到这里：03/04/05/08/09/10 全是同一台机器（严格要求 + `range(3)` 重试 + `extract_json`），只是 schema 越来越长。文档「AoT 是水到渠成的……它不是高级推理，而是更好的结构」说的就是这个。

### 1.3 用你跑出来的那段输出逐行拆

你实际跑 `lesson_10_aot()`（complete_example.py:190）得到：

```
AoT graph: {'nodes': [{'id': '1', 'action': 'research', 'depends_on': []}, {'id': '2', 'action': 'write', 'depends_on': ['1']}]}
Execution results: [{'node_id': '1', 'action': 'research', 'result': 'Executed: research', 'success': True}, {'node_id': '2', 'action': 'write', 'result': 'Executed: write', 'success': True}]
```

这两行分别由 `create_aot_plan`（agent.py:607）和 `execute_aot_plan`（agent.py:621）产出。逐项拆开：

**（a）`research` 在前、`write` 在后——顺序从哪来？**

不是列表碰巧排对，是 `depends_on` 算出来的。`execute_graph`（planner.py:150）反复扫描所有节点，只执行"依赖已全部在 `executed` 集合里"的节点（planner.py:185 的 `all(dep in executed for dep in dependencies)`）：

```
执行前: executed = {}
第 1 轮扫描:
  node1: depends_on=[]  → all(... for dep in []) 对空列表恒为 True → 立即执行 → executed={'1'}
  node2: depends_on=['1'] → '1' 已在 executed → 依赖满足 → 紧接着执行 → executed={'1','2'}
两个节点同一轮跑完，while 退出。
```

关键点：`depends_on=[]` 的节点（node1）因为"对空列表的 `all` 恒为 True"而被第一个跑进 `executed`；轮到 node2 时 `'1'` 已经在里面，依赖满足，紧接着跑。所以 `research→write` 是依赖关系推出来的执行顺序，不是列表先后。

（顺带一提：这次的目标"研究并撰写一篇文章"在 `temperature=0.0` 下，模型生成的图和 prompt 里给的 schema 示例（planner.py:119）一字不差。这是巧合也是模型偷懒——目标恰好就是"research 然后 write"。换个目标，图的形状才会真正变化。）

**（b）`result: 'Executed: research'`——这串字哪来？**

来自 `execute_aot_plan` 内部那个嵌套函数 `execute_action`（agent.py:632-634）：

```python
def execute_action(action: str):
    # 实际动作执行的占位实现
    return f"Executed: {action}"
```

就一行 f-string，**占位、没真执行**——它没有去联网搜索、没有写文件，只把动作名拼进 `"Executed: "`。`execute_graph` 把这个函数当 `executor_func` 传入（agent.py:636），对每个节点调一次（planner.py:188）。所以 `'Executed: research'` 不代表"研究真的做了"，只代表"这个占位函数被调用了一次，参数是 'research'"。

**（c）`success: True`——这个布尔哪来？**

来自 `execute_graph` 里包住每个节点的 `try/except`（planner.py:187-204）。`executor_func(node["action"])` 没抛异常，就走 `try` 分支记 `"success": True`（planner.py:193）。因为 `execute_action` 只是返回一个 f-string、不可能抛异常，所以这里**永远是 True**。它代表的是"执行器调用没崩"，不是"任务成功完成"。

### 1.4 三个概念的实际强度（别被名词唬住）

| 概念 | 文档怎么立 | 本课代码实际做到 |
|---|---|---|
| 依赖解析 | "确定正确的执行顺序，独立动作可并行" | **真做了顺序**：`execute_graph` 按 `depends_on` 拓扑执行（§2）。但**没有并行**——单线程 for 循环顺序跑（§3）。 |
| 校验式执行 | "执行前检查：依赖是否有效？有没有环？必需节点都在吗？" | 只查字段：每个节点有没有 `id/action/depends_on` 三字段 + `depends_on` 是不是 list（planner.py:138-141）。**不查环、不查依赖引用是否指向真实节点**（§3）。 |
| 执行 | "在遵守依赖的前提下执行动作" | 占位。`execute_action` 只返回 `f"Executed: {action}"`（agent.py:634），不调任何工具。 |

和 lesson8 比，本课唯一真正"做厚"了的是**执行顺序**——`execute_plan` 的傻 for 循环升级成了 `execute_graph` 的拓扑执行（这是真算法，§2）。其余两个概念（校验、并行）仍停在最弱版本甚至没做。读的时候把它们当"立了概念、给了骨架"，别以为已经实现到位。

---

## 2 execute_graph：本课第一个真执行器

lesson8 的 `execute_plan`（agent.py:553）是傻 for 循环——`for step in plan["steps"]` 顺序跑一遍，不判断任何依赖（08 答疑 §2.2 讲过）。lesson10 的 `execute_graph`（planner.py:150）第一次出现了真正的执行算法。逐行看：

```python
def execute_graph(graph: dict, executor_func) -> list:
    if not graph or "nodes" not in graph:        # 161-162 守卫：没有 nodes 直接返回空
        return []
    nodes = graph["nodes"]                        # 164
    executed = set()                              # 165 记录哪些节点 id 已经跑完
    results = []                                  # 166
    max_iterations = len(nodes) * 2               # 170 兜底：最多扫描节点数×2 轮
    iteration = 0                                 # 171
    while len(executed) < len(nodes) and iteration < max_iterations:  # 173 还有没跑完的 + 没超兜底
        iteration += 1                            # 174
        for node in nodes:                        # 176 每轮把所有节点扫一遍
            node_id = node["id"]                  # 177
            if node_id in executed:               # 180 跑过了就跳过
                continue
            dependencies = node.get("depends_on", [])              # 184
            if all(dep in executed for dep in dependencies):       # 185 ← 拓扑判断：依赖全满足才执行
                try:                                               # 187
                    result = executor_func(node["action"])         # 188 调占位执行器
                    results.append({"node_id": node_id, "action": node["action"],
                                    "result": result, "success": True})   # 189-194
                    executed.add(node_id)          # 195 成功，记入 executed
                except Exception as e:             # 196 失败隔离
                    results.append({..., "error": str(e), "success": False})  # 197-202
                    executed.add(node_id)          # 204 ← 即使失败也记入，防止 while 死循环
    return results                                # 206
```

四个要点：

1. **拓扑判断（planner.py:185）**：`all(dep in executed for dep in dependencies)`——一个节点的 `depends_on` 里每一项都已经在 `executed` 里，才执行它。这就是"依赖解析"。`depends_on=[]` 的节点对空列表 `all` 恒为 True，第一轮就能跑（§1.3-a）。

2. **反复扫描（while + for）**：一轮 for 不一定能跑完所有节点——某个节点这轮依赖没满足，下一轮再试。`while` 反复扫，直到 `len(executed) == len(nodes)`。这是把扁平 for 循环换成了"扫到不动为止"的迭代式拓扑排序。

3. **失败隔离（planner.py:196-204）**：每个节点用 `try/except` 单独包住。某个节点抛异常，记 `success: False`，**但 except 里照样 `executed.add(node_id)`（planner.py:204）**——否则这个永远失败的节点会让 while 一直认为"还有没跑完的"而空转。文档「失败是被隔离的（限定在单个节点内）」说的就是这个：一个节点崩了不拖垮整张图。

4. **兜底上限（planner.py:170）**：`max_iterations = len(nodes) * 2`。万一出现谁都满足不了依赖的死结（比如环），`while` 里的 `iteration < max_iterations` 保证它扫够 `节点数×2` 轮就退出，不会无限循环。代价是：环里的节点永远进不了 `executed`，会被静默丢掉（附录 A）。

对照 lesson8：`execute_plan` 没有 `executed` 集合、没有 while、没有依赖判断、没有 try/except——它只是 `for step in steps` 走一遍标个 `executed: True`。`execute_graph` 是本课第一个值得叫"算法"的执行器。

---

## 3 名实落差：校验与并行

本课文档承诺得比代码多。两处要如实对齐。

### 3.1 校验：文档说查三样，代码只查字段

文档把"校验式执行"立为新概念（10_atom_of_thought.md:31-35），说执行前要检查：「所有依赖是否有效？是否存在循环依赖？所有必需节点是否都在？」「常见问题」更明说「循环依赖——校验应当能捕获这一点……考虑加入环检测」（10_atom_of_thought.md:207-210）。

但**实际 `planner.py` 的 `create_aot_graph` 校验段（planner.py:134-145）**只做一件事：

```python
valid_nodes = []
for node in graph["nodes"]:
    if isinstance(node, dict) and "id" in node and "action" in node and "depends_on" in node:
        if not isinstance(node["depends_on"], list):   # depends_on 必须是 list
            continue
        valid_nodes.append(node)
if valid_nodes:
    return {"nodes": valid_nodes}
```

它只检查：每个节点是不是 dict、有没有 `id/action/depends_on` 三字段、`depends_on` 是不是 list。**不查环，不查 `depends_on` 里的 id 是否指向真实存在的节点。**文档承诺的三样检查，代码一样没做。

### 3.2 文档贴的代码 ≠ 实际跑的代码

还有一处脱节值得点明：`lessons/10_atom_of_thought.md` 里**贴出来**的 `create_aot_graph`（文档 :76-99），和**实际 `agent/planner.py` 里跑的那段**（planner.py:130-147）**不是同一份代码**。对照：

| | 文档贴的版本（10_atom_of_thought.md:76-99） | 实际文件版本（planner.py:130-147） |
|---|---|---|
| 写法 | `node_ids = set()` + `for...else` 双重循环 | `valid_nodes = []` 逐个筛 |
| 查字段 | 查 `id/action/depends_on` 在不在 | 查 `id/action/depends_on` 在不在 + `depends_on` 是 list |
| 查依赖引用 | **查**：`if dep not in node_ids: break`，依赖必须指向已知节点 | **不查**：完全不验证 `depends_on` 里的 id |
| 不合格节点怎么办 | 全有全无：任一节点不合格，整张图作废（返回 None） | 逐个过滤：丢掉坏节点，保留好节点，返回筛剩的 `{"nodes": valid_nodes}` |
| 环检测 | **没有** | **没有** |

两版唯一的共同点：**都没有任何环检测**——而文档正文恰恰把"捕获循环依赖"当成校验的卖点。所以无论你读的是文档贴的那段、还是实际跑的那段，环都查不出来。文档贴的版本至少还查了依赖引用有效性，实际跑的版本连这个都省了。读文档时以 `agent/planner.py` 的实际代码为准。

### 3.3 并行：文档反复说能并行，代码完全没做

文档从开头到结尾反复强调"独立动作可以并行执行"：开篇「让相互独立的动作可以并行执行」（:16）、依赖解析「使得相互独立的动作能够并行执行」（:29-30）、关键洞见「相互独立的动作可以并行执行」（:197）。

但 `execute_graph`（planner.py:150）是**单线程 for 循环顺序跑**——`for node in nodes` 一个接一个调 `executor_func`，**没有任何 thread、没有 async、没有并发**。即使两个节点 `depends_on` 都为空、本可以同时跑，代码也是先跑完一个再跑下一个。

文档自己在「可扩展性」里改了口：「之后很容易加入并行执行」（:140）——这等于自认本课没做并行。所以"并行"在 lesson10 是一个被反复宣传、但代码里一行都没有的概念。读的时候按"顺序执行、依赖正确"理解即可，别以为独立节点真的并发跑了。

---

## 4 和前面课怎么接上 + 课程收口

### 4.1 三课合一

lesson10 把前两课的产物拼成一张图，08 答疑「附录 A」已经预讲过这个对照，这里承接并补全：

| | lesson8（planning） | lesson9（atomic action） | lesson10（AoT） |
|---|---|---|---|
| 产物 | `{"steps": ["research","write"]}` | `{"action": ..., "inputs": {...}}` | `{"nodes": [{id, action, depends_on}]}` |
| 贡献给 AoT 的 | 节点列表（一目标拆多步） | 每个 `node` 的 `action` 字段 | 加 `depends_on` + 拓扑执行器 |
| 执行 | `execute_plan` 顺序 for | （只生成，不执行） | `execute_graph` 拓扑执行 |

一句话：AoT = lesson8 的"多步" + lesson9 的"原子" + 本课的"依赖"。`depends_on` 是唯一新字段，`execute_graph` 是唯一新执行器。lesson8 的扁平 `steps` 就是一张"所有节点 `depends_on` 都为空、被强排成一条线"的退化依赖图。

### 4.2 一条贯穿线收口

| 课 | 把什么做成显式数据 | 生成机制 | 执行器 |
|---|---|---|---|
| lesson6 | 循环状态（`steps`/`done`） | —— | `run_loop` |
| lesson7 | 跨交互的事实 | LLM 填 `save_to_memory` | —— |
| lesson8 | 多步任务的步骤 | 结构化输出 → `{"steps":[...]}` | `execute_plan`（傻 for） |
| lesson9 | 单步 → 原子动作 | 结构化输出 → `{"action",...}` | （占位） |
| lesson10 | 任务 → 依赖图 | 结构化输出 → `{"nodes":[...]}` | `execute_graph`（拓扑） |

从 lesson3 到 lesson10 一直是同一台机器：**结构化输出 + 校验 + 重试**。变的只有两样——schema 越来越长（从一个枚举字段，到带依赖的节点列表），执行器从无到有（从没有执行、到傻 for、到拓扑执行）。这正印证文档的收口：lesson10 标题「现在一切都说得通了」，最终洞见把 01-10 串起来，反复强调「没有魔法，没有隐藏的推理——只有结构、校验和明确的执行」（10_atom_of_thought.md:243）。

AoT 看起来像"会思考的图"，拆开看就是：一段结构化输出生成的 JSON + 一个读 `depends_on` 的 while 循环。它不聪明，它只是结构更清楚。这是整门课要你 get 的最后一点：Agent 是系统，不是头脑。

---

## 5 速查表

| 问题 | 一句话结论 |
|---|---|
| 本课要 get 什么 | AoT = 规划 + 原子动作 + 依赖关系；`execute_graph` 是第一个真执行器；生成图仍是结构化输出换 schema |
| `depends_on` 是新的吗 | 是本课唯一新增字段；`action` 来自 lesson9，节点列表来自 lesson8 |
| 生成图是新能力吗 | 不是。`create_aot_graph` 和 lesson3/08 同构，只是 schema 长了 |
| `research→write` 顺序哪来 | `depends_on` 算的：`execute_graph` 只执行依赖已全在 `executed` 里的节点（planner.py:185） |
| `Executed: X` 哪来 | `execute_action` 占位函数一行 f-string（agent.py:634），没真执行 |
| `success: True` 哪来 | `try/except` 没抛异常就记 True（planner.py:193）；占位函数永不抛，故恒为 True |
| execute_graph 比 execute_plan 强在哪 | while 反复扫描 + 依赖判断 + 失败隔离 + `max_iterations` 兜底，是真拓扑算法 |
| 校验有多强 | 只查字段（id/action/depends_on + depends_on 是 list）；**不查环、不查依赖引用**（planner.py:138-141） |
| 文档代码和实际代码一样吗 | 不一样：文档版用 `node_ids` 查引用、实际版用 `valid_nodes` 不查引用；**两版都无环检测**（§3.2） |
| 并行做了吗 | 没有。单线程 for 顺序跑，无 thread/async；文档自认"之后很容易加入"（§3.3） |
| 整门课的收口 | 03→10 同一台机器（结构化输出+校验+重试），schema 越长、执行器从无到有；没有魔法 |

---

## 附录 A：循环依赖会怎么崩（选读）

本节基于仓库内代码，无外部信源。

假设模型生成了一个环——node A `depends_on` B、node B `depends_on` A：

```python
{"nodes": [
  {"id": "A", "action": "x", "depends_on": ["B"]},
  {"id": "B", "action": "y", "depends_on": ["A"]}
]}
```

**第一关：`create_aot_graph` 拦不住。** 它的校验（planner.py:138-141）只检查每个节点是不是 dict、有没有三字段、`depends_on` 是不是 list。A、B 三字段齐全、`depends_on` 都是 list，全部通过——图被原样返回（planner.py:145）。环检测代码不存在（§3.2）。

**第二关：`execute_graph` 空转后静默丢节点。** 进 `execute_graph`（planner.py:150）：

```
nodes=[A,B], executed={}, max_iterations = len(nodes)*2 = 4
第 1 轮: A 的 depends_on=['B'] → 'B' 不在 executed → 跳过
        B 的 depends_on=['A'] → 'A' 不在 executed → 跳过
第 2 轮: 同上，两个都跳过
第 3 轮: 同上
第 4 轮: iteration(4) < max_iterations(4) 为 False → while 退出
executed 始终为空，results 始终为空 → 返回 []
```

A 依赖 B、B 依赖 A，谁的依赖都永远满足不了（planner.py:185 的 `all(...)` 对它俩永远是 False），两个节点谁都进不了 `executed`。`while` 空扫到 `iteration` 撞上 `max_iterations`（planner.py:173）退出，返回一个**不完整**的结果——这个纯环例子里直接返回空列表，把两个节点都静默丢了。

如果是混合情况（node1 无依赖 + node2/node3 互相依赖成环），则 node1 正常跑、node2/node3 被丢，`results` 里只剩 node1——同样是静默丢节点，不报错、不提示。

结论：`max_iterations = len(nodes) * 2`（planner.py:170）这个兜底保证了**不会死循环**，但它换来的代价是**静默丢节点**——环里的节点不执行、不报错、悄悄从结果里消失。文档说"校验应当能捕获循环依赖"，但实际既没在校验阶段拦下环，也没在执行阶段报告"有节点没跑成"。这正是 §3 名实落差的具体后果。

---

**核心要点：** AoT 是结构，不是魔法。它把 lesson8 的多步规划、lesson9 的原子动作、再加一个 `depends_on` 字段，合成一张依赖图；`execute_graph` 是整门课第一个真执行器，用 while 反复扫描按依赖拓扑执行。但生成图那步仍是"结构化输出换 schema"的老骨架，执行动作仍是 `f"Executed: {action}"` 占位，校验只查字段不查环，并行一行都没写。从 lesson3 到 lesson10 自始至终是同一台机器——结构、校验、明确执行，没有隐藏的推理。
