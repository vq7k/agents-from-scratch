# 第 05 课 —— 引入工具(Tools)

## 我们要回答什么问题?

**「模型能不能让我去做某件事?」**

工具(tools)把 Agent 的能力扩展到文本生成之外。Agent 不再只能生成文本,而是可以请求执行各种动作,比如计算、调用 API 或文件操作。

## 你将构建什么

一个工具调用(tool calling)系统,它能:
- 让 Agent 请求特定的工具,并附带结构化的参数
- 在执行前对工具请求做校验
- 把工具请求与工具执行分离开
- 无需重新训练模型就能扩展 Agent 的能力

## 引入的新概念

### 1. 工具接口(Tool Interfaces)

**工具接口**是一套 Agent 可以请求调用的、定义好的 API。工具有名字和参数,比如 `calculator(a, b, operation)`。Agent 负责请求工具,但由系统负责执行它。

这种分离至关重要——Agent **描述**它需要什么,但**控制实际发生什么的是你**。

### 2. 结构化工具调用(Structured Tool Calls)

工具调用是对函数调用的**结构化 JSON 描述**。模型输出类似 `{"tool": "calculator", "arguments": {"a": 42, "b": 7, "operation": "multiply"}}` 这样的 JSON,然后由你的代码来校验并执行它。

这和第 04 课的决策很像,只不过这里 Agent 不是在挑选一个动作,而是在指定一次函数调用。

### 3. 由模型选择的动作(Model-Chosen Actions)

Agent 自己决定**用哪个工具**以及**传入什么参数**。你定义有哪些可用工具,但由 Agent 来选择哪一个适合当前情境。

这正是「能动性(agency)」的体现——Agent 在选择并配置动作。

## 重要规则

模型负责**请求**工具,系统负责**执行**工具。目前还没有任何自主性(autonomy)。这种分离让你掌握控制权与安全性。

## 我们暂时还不做的事

- 还没有 agent loop([第 06 课](06_agent_loop.md))
- 还没有记忆([第 07 课](07_memory.md))
- 还没有自动执行工具——你仍然要手动执行工具调用

## 代码

看 `agent/agent.py` 里的 `request_tool()` 方法:

```python
def request_tool(self, user_input: str) -> dict | None:
    """
    让模型请求一次工具调用。

    第 05 课版本。

    Args:
        user_input: 用户的请求

    Returns:
        工具调用描述,如果请求失败则返回 None
    """
    prompt = f"""{self.system_prompt}

You are a tool-calling assistant. When asked a math question, you must respond with ONLY valid JSON.

Available tool: calculator
- Parameters: a (number), b (number), operation ("add", "subtract", "multiply", or "divide")

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Example format:
{{"tool": "calculator", "arguments": {{"a": 42, "b": 7, "operation": "multiply"}}}}

User request: {user_input}

Response (JSON only):"""
    
    for attempt in range(3):
        response = self.llm.generate(prompt, temperature=0.0)
        parsed = extract_json_from_text(response)
        
        if parsed and "tool" in parsed and "arguments" in parsed:
            return parsed
    
    return None

def execute_tool_call(self, tool_call: dict) -> Any:
    """
    执行模型请求的一次工具调用。

    Args:
        tool_call: 包含 "tool" 和 "arguments" 的字典

    Returns:
        工具执行的结果
    """
    return execute_tool(tool_call["tool"], tool_call["arguments"])
```

注意:
- **结构化输出**——工具调用是经过校验的 JSON,和第 03 课类似
- **校验**——我们会检查 "tool" 和 "arguments" 两者是否都存在
- **关注点分离**——请求和执行是两个独立的方法
- **可扩展性**——无需改动模型就能轻松添加新工具

## 如何运行

看 `complete_example.py` 里的 `lesson_05_tools()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

tool_call = agent.request_tool("What is 42 * 7?")
print(f"Tool request: {tool_call}")

if tool_call:
    result = agent.execute_tool_call(tool_call)
    print(f"Tool result: {result}")
```

![工具调用流程](diagrams/lesson-05-tool-calling.png)

## 与第 04 课的对比

**第 04 课(决策):**
```
Input: "What should I do?"
Choices: ["answer", "calculate", "translate"]
Output: "calculate"
```
Agent 从一个动作列表里挑选。

**第 05 课(工具调用):**
```
Input: "What is 42 * 7?"
Tool: calculator
Arguments: {"a": 42, "b": 7, "operation": "multiply"}
Result: 294
```
Agent 指定一次带参数的工具调用,并拿到结果。

## 关键洞见

### 工具是接口,而不是能力本身

Agent 并不拥有这种能力——你才拥有。Agent 通过一个结构化接口描述它需要什么,而由你来提供具体实现。这让控制权始终在你手上。

### 无需重新训练

要增加新能力,你只需添加新工具。模型不需要重新训练——它只需要理解工具接口即可。这非常强大。

### 通过分离实现安全

把工具请求与执行分离后,你就可以对实际发生的事情做校验、记录和控制。只要你的代码不放行,Agent 就无法执行危险操作。

### 结构化 = 可靠

沿用第 03、04 课同样的结构化 JSON 模式,能让工具调用既可靠又易于解析。模型输出结构化数据,你校验它,然后执行。

## 常见问题

**「模型请求了一个不存在的工具」**
- 拿模型给出的工具名跟你的可用工具列表做校验
- 在 prompt 里给出清晰的可用工具示例
- 对无效工具名做优雅的兜底处理

**「参数类型不对」**
- 在执行前校验参数类型
- 在工具描述里把期望的类型讲清楚
- 对复杂工具可以考虑使用 schema 校验

**「该用工具的时候模型却不请求工具」**
- 把「什么时候应该用工具」讲清楚
- 在 prompt 里给出示例
- 对某些类型的请求,可以考虑把使用工具设为强制

## 练习

1. 添加一个新工具(例如 "weather" 或 "search")并测试它
2. 试着发起一些无效的工具调用,看看校验如何处理
3. 修改工具接口,观察模型如何适应
4. 创建带不同参数类型(字符串、数字、布尔值)的工具

## 下一步是什么?

在[第 06 课](06_agent_loop.md)中,我们将创建 **agent loop**——把决策和工具调用组合进一个不断重复的循环里。

---

**核心要点:** 工具调用 = 在不重新训练的前提下扩展能力。工具是你所控制的接口,而不是 Agent 自带的能力。
