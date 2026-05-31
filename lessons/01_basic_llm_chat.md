# 第 01 课 —— 与模型对话

## 我们要回答什么问题?

**「我到底该怎么和语言模型对话?」**

这是最根本的基础。在构建 Agent 之前,我们需要理解最简单的一种交互:输入文本,输出文本。

## 你将构建什么

一个极简的交互,它会:
- 加载一个本地 LLM
- 向它发送文本
- 接收返回的文本

仅此而已。没有魔法,没有框架,只有最基本的东西。

## 引入的新概念

### 1. Prompt(提示词)

**prompt** 就是你发送给模型的文本。它可以是一个问题,比如「什么是 AI Agent?」;一条指令,比如「解释一下量子计算」;或者一个请求,比如「写一首关于海洋的诗」。模型会根据它在训练阶段学到的模式,对这段文本进行补全或回应。

### 2. Token

模型看到的不是一个个单词,而是一个个 **token**。token 是文本的片段(通常是单词或子词)。例如,「Hello world」可能是 2 个 token,而「artificial intelligence」根据模型不同,可能是 2 到 4 个 token。

这一点很重要,因为模型有 token 上限(上下文窗口),生成速度以「每秒 token 数」来衡量,而且更长的 prompt 会消耗更多 token,留给回复的空间也就更少。

### 3. 上下文(Context)

**上下文**是模型一次能「看到」的全部内容。它包括你的 prompt、之前的任何对话,以及系统指令。模型有一个**上下文窗口**(例如 2048 个 token)。如果超出这个范围,模型就看不到更早的文本了。

## 我们(暂时)不做什么

- 不用系统提示词([第 02 课](02_system_prompt.md))
- 不用结构化输出([第 03 课](03_structured_output.md))
- 不用工具([第 05 课](05_tools.md))
- 不构建 Agent([第 06 课](06_agent_loop.md))
- 不用记忆([第 07 课](07_memory.md))

这一课刻意保持极简。

## 代码

看 `agent/agent.py` 中的 `simple_generate()` 方法:

```python
def simple_generate(self, user_input: str) -> str:
    """
    最简单的交互方式 —— 只是把文本传给 LLM。
    """
    return self.llm.generate(user_input)
```

就这样。一行代码。毫无复杂之处。

## 如何运行

看 `complete_example.py` 中的 `lesson_01_basic_chat()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/llama-3-8b-instruct.gguf")

response = agent.simple_generate("What is an AI agent?")
print(response)
```

## 内部到底发生了什么?

1. 你的文本被转换成 token
2. token 被发送给模型
3. 模型预测下一个 token
4. 重复这个过程,直到满足某个停止条件(结束 token、最大长度等)
5. token 被转换回文本
6. 文本返回给你

## 关键洞见

### 并不存在「理解」

模型并不「理解」你的问题。相反,它识别 token 中的模式,预测可能的后续内容,并生成概率性的文本。这一点很重要:**模型是模式匹配器,不是头脑。**

### 它是概率性的

同一个 prompt 跑两次,你可能得到不同的回复。这是因为模型在生成时引入了随机性(temperature),而且对同一段文本存在多种合理的后续。并不存在唯一「正确」的答案——只有概率性的输出。

### 输入文本 = 输出文本

它的本质就是如此。我们之后构建的一切(Agent、工具、记忆)都建立在这个简单的基础之上。

## 常见问题

**「回复被截断了」**
- 在 `shared/llm.py` 中调大 `max_tokens`

**「模型在重复自己」**
- 对于补全类模型,这很正常
- 我们会在[第 02 课](02_system_prompt.md)用更好的 prompt 来解决它

**「回复和 prompt 对不上」**
- 有些模型需要特定的格式
- 我们会在[第 02 课](02_system_prompt.md)和[第 03 课](03_structured_output.md)中加入结构

## 练习

1. 尝试不同的 prompt,观察回复有何不同
2. 修改 `shared/llm.py` 中的 `temperature`(0.0 = 确定性,1.0 = 有创造性)
3. 用 `max_tokens` 来控制回复长度

## 接下来是什么?

在[第 02 课](02_system_prompt.md)中,我们会加入**系统提示词(system prompt)**来塑造模型的行为。这能把随机的补全变成稳定、有用的回复。

---

**核心要点:** LLM 只是一个文本补全引擎。我们构建的一切,都是围绕这个简单机制展开的结构化交互。
