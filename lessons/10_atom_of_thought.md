# 第 10 课  -  AoT(思维原子,Atom of Thought)  -  现在一切都说得通了

## 我们要回答什么问题?

**「如何在不失去控制的前提下扩展规划?」**

复杂任务需要许多带依赖关系的动作。有些动作可以并行运行,有些则必须等待。AoT(思维原子,Atom of Thought)创建依赖图(dependency graph),从而安全、高效地执行复杂工作流。

## 你将构建什么

一个 AoT 系统,它能够:
- 创建包含节点(node)和依赖关系的依赖图
- 在执行前校验图结构
- 在执行动作时遵守依赖关系
- 让相互独立的动作可以并行执行

## 引入的新概念

### 1. 原子化规划(Atomic Planning)

**原子化规划**意味着把计划构建成依赖图,其中每个节点都是一个原子动作。节点可以依赖其他节点,从而形成明确的执行顺序。

这是第 08 课的规划与第 09 课的原子动作的自然结合,再加上依赖追踪。

### 2. 依赖解析(Dependency Resolution)

**依赖解析**用于确定正确的执行顺序。没有依赖的动作可以立即运行;有依赖的动作则要等待其依赖项完成。

这使得相互独立的动作能够并行执行,同时遵守顺序约束。

### 3. 校验式执行(Validated Execution)

**校验式执行**意味着在运行之前检查图结构。所有依赖是否有效?是否存在循环依赖?所有必需节点是否都在?

校验能在执行开始前捕获结构性错误。

## 代码

查看 `agent/planner.py` 中的 `create_aot_graph()` 函数:

```python
def create_aot_graph(llm: LocalLLM, goal: str) -> dict | None:
    """
    生成一张 AoT 执行图。
    
    用于:第 10 课
    
    Args:
        llm: 要使用的语言模型
        goal: 要达成的目标
        
    Returns:
        包含节点和依赖关系的 AoT 图;若生成失败则返回 None
    """
    from shared.utils import extract_json_from_text
    
    prompt = f"""Create an execution graph to achieve the goal. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{
  "nodes": [
    {{"id": "1", "action": "action_name", "depends_on": []}},
    {{"id": "2", "action": "action_name", "depends_on": ["1"]}}
  ]
}}

Each node must have:
- "id": unique identifier (string)
- "action": what to do (string)
- "depends_on": list of node IDs that must complete first (list of strings)

Goal: {goal}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(prompt, temperature=0.0)
        graph = extract_json_from_text(response)
        
        if graph and "nodes" in graph and isinstance(graph["nodes"], list):
            # 校验节点结构
            node_ids = set()
            for node in graph["nodes"]:
                if "id" not in node or "action" not in node or "depends_on" not in node:
                    break
                node_ids.add(node["id"])
            else:
                # 所有节点都有效,检查依赖是否引用了有效节点
                for node in graph["nodes"]:
                    for dep in node.get("depends_on", []):
                        if dep not in node_ids:
                            break
                    else:
                        continue
                    break
                else:
                    return graph
    
    return None
```

以及 `agent/agent.py` 中:

```python
def create_aot_plan(self, goal: str) -> dict | None:
    """
    生成一张 AoT 执行图。
    
    第 10 课版本。
    
    Args:
        goal: 要达成的目标
        
    Returns:
        包含原子节点和依赖关系的 AoT 图
    """
    return create_aot_graph(self.llm, goal)

def execute_aot_plan(self, graph: dict) -> list:
    """
    在遵守依赖关系的前提下执行一张 AoT 图。
    
    Args:
        graph: AoT 图
        
    Returns:
        执行结果列表
    """
    def execute_action(action: str):
        # 实际动作执行的占位实现
        return f"Executed: {action}"
    
    return execute_graph(graph, execute_action)
```

注意:
- **图结构** —— 节点带有 ID、动作和依赖关系
- **校验** —— 检查所有依赖是否引用了有效节点
- **依赖解析** —— execute_graph 函数负责处理顺序
- **可扩展性** —— 之后很容易加入并行执行

## 如何运行

查看 `complete_example.py` 中的 `lesson_10_aot()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

graph = agent.create_aot_plan("Research and write article")
print(f"AoT graph: {graph}")

if graph:
    results = agent.execute_aot_plan(graph)
    print(f"Execution results: {results}")
```

![思维原子图](diagrams/lesson-10-atom-of-thoght.png)

## 与第 09 课的对比

**第 09 课(原子动作):**
```
Step -> Atomic action: {"action": "...", "inputs": {...}}
```
单个步骤被转换成原子动作。

**第 10 课(AoT):**
```
Goal -> Graph: {
  nodes: [
    {id: "1", action: "...", depends_on: []},
    {id: "2", action: "...", depends_on: ["1"]}
  ]
}
```
多个原子动作,带有明确的依赖关系。

## 关键洞见

### AoT 是水到渠成的

到了这一步,AoT 给人的感觉是**水到渠成**,而非高深莫测。它是规划(第 08 课)、原子动作(第 09 课)再加上依赖关系的自然演进。一旦你理解了这些组成部分,图结构便顺理成章。

### 它不是高级推理

AoT 不是更聪明的思考,而是**更好的结构**:
- 每个节点都经过校验(来自第 09 课)
- 依赖关系是明确的(本课新增)
- 执行是确定的(遵守顺序)
- 失败是被隔离的(限定在单个节点内)

### 结构带来扩展能力

通过加入依赖关系,你就能处理含有大量动作的复杂工作流。依赖关系带来:
- 相互独立的动作可以并行执行
- 清晰的执行顺序
- 更容易调试(知道谁依赖谁)

### 校验是关键

图结构必须在执行前经过校验。循环依赖、缺失节点或无效引用都必须尽早被捕获。

## 常见问题

**「循环依赖」**
- 校验应当能捕获这一点
- 检查依赖关系是否构成一张有向无环图(DAG)
- 考虑在校验中加入环检测

**「依赖引用了不存在的节点」**
- 校验会检查这一点
- 确保依赖中的所有节点 ID 都存在于图中
- 考虑以更系统化的方式生成 ID

**「执行顺序看起来不对」**
- 确认依赖关系指定正确
- 检查 execute_graph 是否遵守依赖关系
- 考虑加入执行日志以查看顺序

## 练习

1. 创建具有不同依赖结构的图
2. 尝试构造一个循环依赖,看校验能否捕获它
3. 对比有依赖和无依赖时的执行顺序
4. 试验并行执行与顺序执行

## 最终洞见

你现在已经构建出一个 Agent,它能够:
1. 与 LLM 对话([第 01 课](01_basic_llm_chat.md))
2. 拥有一致的行为([第 02 课](02_system_prompt.md))
3. 产出经过校验的输出([第 03 课](03_structured_output.md))
4. 做出决策([第 04 课](04_decision_making.md))
5. 使用工具([第 05 课](05_tools.md))
6. 在循环中运行([第 06 课](06_agent_loop.md))
7. 记住事情([第 07 课](07_memory.md))
8. 规划动作([第 08 课](08_planning.md))
9. 安全地执行([第 09 课](09_atomic_actions.md))
10. 借助依赖关系实现扩展([第 10 课](10_atom_of_thought.md))

并且你**确切地理解了这一切是如何运作的**。没有魔法,没有隐藏的推理——只有结构、校验和明确的执行。

---

**核心要点:** AoT 是结构,不是魔法。Agent 是系统,不是头脑。依赖图让复杂工作流成为可能,同时保持控制力与可预测性。