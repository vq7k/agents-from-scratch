# 第 08 课 —— 把规划当作数据(而非思想)

## 我们要回答什么问题?

**「Agent 怎样才能解决多步骤的任务?」**

复杂任务需要多个步骤。规划(planning)把一个目标拆解成一连串可以逐步执行的动作。

## 你将构建什么

一个规划系统,它能:
- 从一个目标生成逐步的计划
- 把规划与执行分离
- 把计划存储为数据结构
- 按顺序执行计划

## 引入的新概念

### 1. 规划 vs 执行(Planning vs Execution)

**规划**是生成达成目标所需的步骤,**执行**则是真正去做这些步骤。把两者分离后,你就可以:
- 在执行前查看计划
- 在需要时修改计划
- 把规划与执行分开来调试

这种分离很强大——你可以在 Agent 动手之前,先看看它「认为」自己应该做什么。

### 2. 步骤排序(Step Ordering)

**步骤排序**决定各动作的先后顺序。步骤之间可能存在依赖(第 2 步需要第 1 步的输出),也可能彼此独立。

目前,我们按顺序执行步骤。后续课程会更显式地处理依赖关系。

### 3. 校验(Validation)

**校验**会在执行前检查计划。这个计划是合法的 JSON 吗?它是否具备所需的结构?这些步骤合理吗?

校验计划能在浪费时间执行之前就抓出错误。

## 我们暂时还不做的事

- 还没有依赖处理([第 10 课](10_atom_of_thought.md))
- 还没有原子动作(atomic actions)校验([第 09 课](09_atomic_actions.md))
- 还没有并行执行——步骤是顺序运行的

## 代码

看 `agent/agent.py` 里的 `create_plan()` 和 `execute_plan()` 方法:

```python
def create_plan(self, goal: str) -> dict | None:
    """
    生成一个达成目标的计划。

    第 08 课版本。

    Args:
        goal: 要达成的目标

    Returns:
        包含若干步骤的计划
    """
    plan = create_plan(self.llm, goal)
    
    if plan:
        self.state.current_plan = plan
    
    return plan

def execute_plan(self, plan: dict) -> list:
    """
    逐步执行一个计划。

    Args:
        plan: 包含 "steps" 列表的计划字典

    Returns:
        执行结果的列表
    """
    if not plan or "steps" not in plan:
        return []
    
    results = []
    
    for step in plan["steps"]:
        # 简单的执行——实际场景里你会调用工具等等
        result = {
            "step": step,
            "executed": True
        }
        results.append(result)
        self.state.increment_step()
    
    return results
```

以及 `agent/planner.py` 里的 planner 实现:

```python
def create_plan(llm: LocalLLM, goal: str) -> dict | None:
    """
    生成一个达成目标的计划。

    用于:第 08 课

    Args:
        llm: 要使用的语言模型
        goal: 要达成的目标

    Returns:
        以字典形式表示、含 "steps" 列表的计划;如果生成失败则返回 None
    """
    from shared.utils import extract_json_from_text
    
    prompt = f"""Create a step-by-step plan to achieve the goal. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"steps": ["step1", "step2", "step3"]}}

Goal: {goal}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(prompt, temperature=0.0)
        plan = extract_json_from_text(response)
        
        if plan and "steps" in plan and isinstance(plan["steps"], list):
            return plan
    
    return None
```

注意:
- **结构化输出**——计划是 JSON 数据结构
- **校验**——我们会检查计划是否具备预期的结构
- **重试逻辑**——多次尝试以拿到一个合法的计划
- **简单执行**——步骤按顺序执行(真正的执行逻辑放到后面)

## 如何运行

看 `complete_example.py` 里的 `lesson_08_planning()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

plan = agent.create_plan("Write a blog post about AI agents")
print(f"Plan: {plan}")

if plan:
    results = agent.execute_plan(plan)
    print(f"Execution results: {results}")
```

## 与第 07 课的对比

**第 07 课(记忆):**
```
User: "My name is Alice" -> Save to memory
User: "What's my name?" -> Retrieve from memory
```
存储并检索事实。

**第 08 课(规划):**
```
Goal: "Write article" -> Plan: ["Research", "Outline", "Write", "Review"]
Plan -> Execute each step -> Results
```
生成并执行一连串步骤。

![规划流程](diagrams/lesson-08-planning.png)

## 关键洞见

### 计划不是思想

计划不是思想——它们是**数据结构**。这让它们可查看、可修改、且安全。你可以在执行前查看、编辑并校验它们。

### 规划 = 数据生成

规划并不是什么高深的推理——它是结构化数据的生成。模型生成一个步骤列表,就跟它生成任何其他结构化输出一样。

### 分阶段进行

把规划与执行分离,让你可以:
- 不执行就调试计划
- 在运行前修改计划
- 对相似目标复用计划
- 独立地测试规划

### 简单执行

目前,执行很简单——只是遍历各个步骤。后续课程会加入更复杂的执行,带上依赖和校验。

## 常见问题

**「计划太含糊」**
- 把目标说得更具体
- 在 prompt 里给出优秀计划的示例
- 考虑把非常笼统的目标拆解开

**「步骤顺序不对」**
- 顺序由模型决定——必要时加以校验
- 考虑补充依赖信息
- 必要时在执行前审阅并重新排序

**「执行什么都没做」**
- 本课的执行只是个占位实现
- 实际中,你会调用工具或其他函数
- 这里模式比具体实现更重要

## 练习

1. 为不同类型的目标生成计划
2. 在执行前手动修改计划
3. 对同一个目标多次运行,比较生成的计划
4. 尝试校验计划是否完整

## 下一步是什么?

在[第 09 课](09_atomic_actions.md)中,我们将通过把计划步骤转换为带校验 schema 的**原子动作(atomic actions)**,让执行更安全。

---

**核心要点:** 规划 = 数据生成,而非推理。计划是可查看的数据结构,能支撑多步骤的执行。
