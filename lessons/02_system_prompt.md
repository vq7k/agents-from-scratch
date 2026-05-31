# 第 02 课 —— 给模型一个角色

## 我们要回答什么问题?

**「为什么同一个模型会表现得不一样?」**

你可能已经注意到,LLM 可以扮演不同的人设——技术专家、创意写手、得力助手。这是怎么做到的?

## 你将构建什么

一个使用**系统提示词(system prompt)**的脚本,它会:
- 给模型指定一个特定的角色
- 稳定它的行为
- 控制语气和格式

## 引入的新概念

### 1. 系统提示词(System Prompt)

**系统提示词**是一条用来塑造模型回应方式的指令。它就像在对话开始前,先给一个人安排好角色。

系统提示词示例:
```
"You are a calm, precise teacher who explains concepts simply."
```

```
"You are a creative writer who uses vivid imagery."
```

```
"You are a code reviewer who finds bugs and suggests improvements."
```

### 2. 指令层级(Instruction Hierarchy)

大多数模型都理解这样一个层级:
1. **系统提示词** —— 整体的行为和角色
2. **用户提示词** —— 实际的问题或请求

系统提示词拥有更高的「优先级」——它指导模型如何理解用户提示词。

### 3. 行为塑造(Behavior Shaping)

行为 ≠ 智能。行为 = 指令。

同一个模型可以:
- 偏技术或偏随意(语气)
- 啰嗦或简洁(长度)
- 有创造性或重事实(风格)

这一切都取决于系统提示词。

## 我们(暂时)不做什么

- 不用结构化输出([第 03 课](03_structured_output.md))
- 不做决策([第 04 课](04_decision_making.md))
- 不用工具([第 05 课](05_tools.md))
- 不用记忆([第 07 课](07_memory.md))

## 代码

看 `agent/agent.py` 中的 `generate_with_role()` 方法:

```python
def generate_with_role(self, user_input: str) -> str:
    """
    带系统提示词生成,用以塑造行为。
    """
    # 使用一种不会让模型混乱的格式
    prompt = f"""{self.system_prompt}

User: {user_input}
Assistant:"""
    
    response = self.llm.generate(prompt)
    # 清理掉可能出现的标签残留
    response = response.replace('<SYSTEM>', '').replace('</SYSTEM>', '')
    response = response.replace('<USER>', '').replace('</USER>', '')
    return response.strip()
```

注意我们新增了:
- 把系统提示词放在开头
- 用一个简单的「User:」/「Assistant:」格式来组织对话
- 加入清理代码,移除可能出现的标签残留

## 如何运行

看 `complete_example.py` 中的 `lesson_02_with_role()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/llama-3-8b-instruct.gguf")

# 这个 agent 有一个默认的系统提示词:
# "You are a calm, precise, and helpful AI assistant..."

response = agent.generate_with_role("What is an AI agent?")
print(response)
```

## 与第 01 课对比

**不带系统提示词([第 01 课](01_basic_llm_chat.md)):**
```
Input: "What is an AI agent?"
Output: "An AI agent is a system that perceives its environment and acts autonomously to achieve specified goals. It processes information, makes decisions, and can adapt to changing conditions using machine learning algorithms..."
```

**带系统提示词:**
```
Input: "What is an AI agent?"
Output: "Think of an AI agent as a helpful assistant that can observe what's happening around it and take actions to help you accomplish tasks. Like how a thermostat watches the temperature and adjusts heating automatically - but much more sophisticated."
```

同样的问题。同样的模型。不同的行为。

## 系统提示词的威力

### 示例 1:技术专家
```python
agent.system_prompt = "You are a senior software engineer who explains concepts with code examples."
```

### 示例 2:ELI5(像对 5 岁小孩那样解释)
```python
agent.system_prompt = "You explain complex topics using simple words and everyday analogies."
```

### 示例 3:简洁回应者
```python
agent.system_prompt = "You give accurate answers in 1-2 sentences maximum. No elaboration unless asked."
```

## 关键洞见

### 行为是可配置的

你并没有改变模型——你改变的是对它输出的**约束**。模型依然在预测 token;系统提示词只是改变了这些 token 的概率分布。

### 一致性得到提升

没有系统提示词时,模型可能会:
- 这一次回复很正式,下一次又很随意
- 有时啰嗦,有时简短
- 语气前后不一致

系统提示词能带来**行为上的一致性**。

### 仍然是概率性的

即使有了系统提示词,回复依然会有变化。但这些变化是在你设定的**约束范围之内**发生的。

## 常见的系统提示词模式

### 1. 角色定义
```
You are a [role] who [behavior].
```

### 2. 设定约束
```
You must [requirement]. You never [prohibition].
```

### 3. 输出格式
```
Always respond with [format]. Use [style].
```

### 4. 组合使用
```
You are a helpful assistant. 
You explain concepts clearly using examples.
You keep responses under 100 words unless asked to elaborate.
```

## 常见问题

**「模型无视我的系统提示词」**
- 有些模型对系统提示词的遵循程度比其他模型更好
- 试着把指令写得更明确、更具体
- 使用更强硬的措辞(用「You MUST...」而不是「Try to...」)

**「回复仍然不一致」**
- 这很正常——LLM 本就是概率性的
- 调低 `temperature` 以获得更高的一致性
- 我们会在[第 03 课](03_structured_output.md)中加入校验

**「系统提示词太长了」**
- 把它控制在 100 到 200 词以内
- token 越多 = 留给用户输入和回复的空间越少

## 练习

1. 尝试不同的系统提示词,观察行为变化
2. 写一个让回复极其简洁的系统提示词
3. 写一个让回复极其详尽的系统提示词
4. 试试相互冲突的指令(哪一条会胜出?)

## 接下来是什么?

在[第 03 课](03_structured_output.md)中,我们会加入**结构化输出**,让回复变得可靠、可解析。我们要的不再是自由文本,而是经过校验的 JSON。

---

**核心要点:** 行为不是智能,而是约束。系统提示词把一个通用模型变成一个专属的助手。
