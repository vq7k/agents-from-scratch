# 第 09 课  -  原子化步骤与安全执行

## 我们要回答什么问题?

**「如何让计划变得安全且可预测?」**

像「写一篇文章」这样的计划步骤含糊不清,难以校验。原子动作(atomic actions)把步骤拆解成尽可能小、定义明确的操作,从而可以被校验并安全执行。

## 你将构建什么

一个原子动作系统,它能够:
- 把含糊的计划步骤转换成具体的、带类型的动作
- 在执行前对动作进行校验
- 用 schema 确保参数正确
- 让执行过程可预测、可调试

## 引入的新概念

### 1. 原子性(Atomicity)

**原子性**意味着把动作拆解成尽可能小的单元。不再是「写一篇文章」,而是「generate_text」配上具体参数,比如主题(topic)和长度(length)。

原子动作是不可分割的——要么完整成功,要么完整失败,不存在中间的部分状态。

### 2. 确定性(Determinism)

**确定性**意味着结果可预测。对同一个原子动作给定相同的输入,你应当得到相近的结果(考虑到 LLM 本身的随机性)。

原子动作通过消除歧义,让执行变得确定。

### 3. 类型化执行(Typed Execution)

**类型化执行**意味着动作带有经过校验的 schema。每个动作都要指定:
- 动作名称(例如 "generate_text")
- 必需的输入(例如 {"topic": string, "length": string})
- 校验规则

这能在执行前就捕获错误。

## 我们(暂时)不做什么

- 不处理动作之间的依赖关系([第 10 课](10_atom_of_thought.md))
- 不做并行执行
- 不实现动作的实际执行——只做转换和校验

## 代码

查看 `agent/planner.py` 中的 `create_atomic_action()` 函数:

```python
def create_atomic_action(llm: LocalLLM, step: str) -> dict | None:
    """
    把一个计划步骤转换成原子动作。
    
    用于:第 09 课
    
    Args:
        llm: 要使用的语言模型
        step: 计划中的某个步骤
        
    Returns:
        以字典形式表示的原子动作;若生成失败则返回 None
    """
    from shared.utils import extract_json_from_text
    
    prompt = f"""将这个步骤转换为一个原子动作。只输出合法的 JSON。

严格要求:
1. 只输出合法的 JSON
2. 不要解释、不要 markdown、JSON 前后不要有多余文本
3. 必须以 {{ 开头、以 }} 结尾

必须遵循的格式:
{{
  "action": "动作名",
  "inputs": {{"参数名": "参数值"}}
}}

action 应该是一个简单的、原子化的操作名称。
inputs 应该是一个字典,包含该动作所需的参数。

待转换的步骤:
{step}

回复（仅 JSON）:"""
    
    for attempt in range(3):
        response = llm.generate(prompt, temperature=0.0)
        action = extract_json_from_text(response)
        
        if action and "action" in action:
            return action
    
    return None
```

以及 `agent/agent.py` 中:

```python
def create_atomic_action(self, step: str) -> dict | None:
    """
    把一个计划步骤转换成原子动作。
    
    第 09 课版本。
    
    Args:
        step: 计划中的某个步骤(例如 "Write an explanation of AI agents")
        
    Returns:
        包含 "action" 和 "inputs" 的原子动作字典;若生成失败则返回 None
    """
    return create_atomic_action(self.llm, step)
```

注意:
- **步骤转换** —— 含糊的步骤变成带参数的具体动作
- **schema 校验** —— 动作必须包含 "action" 和 "inputs" 字段
- **结构化输出(structured output)** —— 沿用前几课相同的 JSON 模式
- **重试逻辑** —— 多次尝试以获得有效的原子动作

## 如何运行

查看 `complete_example.py` 中的 `lesson_09_atomic_actions()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

# 把一个计划步骤转换成原子动作
step = "Write an explanation of AI agents"
atomic_action = agent.create_atomic_action(step)
print(f"Step: {step}")
print(f"Atomic action: {atomic_action}")

# 以计划中的某个步骤为例
plan = agent.create_plan("Create a tutorial about Python")
if plan and "steps" in plan and plan["steps"]:
    first_step = plan["steps"][0]
    atomic_action_from_plan = agent.create_atomic_action(first_step)
    print(f"\nPlan step: {first_step}")
    print(f"Atomic action from plan step: {atomic_action_from_plan}")
```

## 与第 08 课的对比

**第 08 课(规划):**
```
Goal -> Plan: ["Research topic", "Create outline", "Write draft"]
```
计划是一个由含糊步骤描述组成的列表。

**第 09 课(原子动作):**
```
Step: "Write draft" -> Atomic: {"action": "generate_text", "inputs": {"topic": "...", "length": "..."}}
```
步骤变成具体的、带类型且参数经过校验的动作。

## 关键洞见

### 小步骤 = 安全系统

动作越小,系统越安全。原子动作具有以下特点:
- 更容易校验——你可以在执行前检查参数
- 更容易测试——每个动作都能独立测试
- 更容易调试——失败被隔离在具体的某个动作上
- 更难发生灾难性失败——小动作的「爆炸半径」有限

### 含糊 vs 具体

「写一篇文章」是含糊的。「generate_text(topic='AI agents', length='1000 words')」是具体的。具体性使校验和可预测的执行成为可能。

### 校验要尽早发生

通过在执行前校验动作,你能尽早捕获错误。一个含有无效动作的计划,可以在任何实际工作开始之前就被拒绝。

### 构建积木

原子动作是构建积木。复杂的工作流由许多简单的原子动作搭建而成,每一个都经过校验、都是安全的。

## 常见问题

**「原子动作还是太含糊」**
- 在 prompt 中给出更清晰的指令
- 提供优质原子动作的示例
- 考虑把动作名称约束到一个预定义的集合中

**「校验失败」**
- 检查动作是否同时包含 "action" 和 "inputs" 字段
- 确认 JSON 结构正确
- 考虑为 inputs 增加 schema 校验

**「转换失败」**
- 有些步骤可能无法干净地映射成原子动作
- 考虑多次重试(已实现)
- 提供更多关于「什么才算优质原子动作」的上下文

## 练习

1. 把不同类型的计划步骤转换成原子动作
2. 对比相似步骤所生成的原子动作
3. 尝试在执行前校验原子动作
4. 试验不同的输入参数结构

## 接下来是什么?

在[第 10 课](10_atom_of_thought.md)中,我们将把规划、原子动作和**依赖关系**结合起来,创建执行图,从而以正确的顺序、甚至并行地运行动作。

---

**核心要点:** 小步骤 = 安全系统。原子动作通过把含糊的计划拆解成具体、经过校验的操作,让执行变得可预测、可调试且安全。