# 第 07 课 —— 记忆(短期与长期)

## 我们要回答什么问题?

**「Agent 是怎么记住东西的?」**

Agent 需要跨多次交互记住信息。没有记忆,每次对话都得从零开始。记忆让 Agent 能在过往对话的基础上继续推进,并维持上下文。

## 你将构建什么

一个记忆系统,它能:
- 跨交互存储事实
- 在需要时检索相关记忆
- 把记忆整合进 Agent 的上下文
- 允许显式地管理记忆

## 引入的新概念

### 1. 上下文 vs 记忆(Context vs Memory)

**上下文**是当前 prompt 里的内容——模型此刻所能看到的一切。**记忆**则是能在多次交互间存活下来的持久化存储。

上下文是临时的,记忆是持久的。需要时,记忆会被加载进上下文。

### 2. 持久化(Persistence)

**持久化**意味着把事实跨轮次保存下来。当用户说「我叫 Alice」时,这个事实应当被存储,并在未来的交互中可用。

没有持久化,Agent 在每次交互后都会忘掉一切。

### 3. 检索(Retrieval)

**检索**就是在需要时取出相关的记忆。当用户问「我叫什么名字?」时,Agent 从记忆中检索出「用户的名字是 Alice」,并据此作答。

简单的检索可能就是「取出全部记忆」。更复杂的检索则会根据当前查询找出相关的记忆。

## 我们暂时还不做的事

- 还没有规划([第 08 课](08_planning.md))
- 还没有复杂的记忆检索——只用简单的「取出全部」检索
- 还没有记忆衰减或优先级排序

## 代码

看 `agent/agent.py` 里的 `run_with_memory()` 方法:

```python
def run_with_memory(self, user_input: str) -> dict | None:
    """
    带记忆上下文运行 Agent。

    第 07 课版本。

    Args:
        user_input: 用户输入

    Returns:
        响应,可能包含一次记忆更新
    """
    memory_context = self.memory.get_all()
    
    # 构建记忆上下文字符串
    if memory_context:
        memory_str = "You remember the following:\n" + "\n".join(f"- {item}" for item in memory_context)
    else:
        memory_str = "You have no memories yet."
    
    prompt = f"""{self.system_prompt}

You are an agent with memory. You must respond with ONLY valid JSON.

{memory_str}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}
4. If the user tells you information (like their name), save it to memory
5. If the user asks about something you remember, USE YOUR MEMORY to answer

Required JSON format:
{{"reply": "your response text", "save_to_memory": "fact to remember" or null}}

Examples:
- User says "My name is Alice" -> {{"reply": "Nice to meet you, Alice!", "save_to_memory": "User's name is Alice"}}
- User asks "What's my name?" and you remember "User's name is Alice" -> {{"reply": "Your name is Alice", "save_to_memory": null}}

User input: {user_input}

Response (JSON only):"""
    
    for attempt in range(3):
        response = self.llm.generate(prompt, temperature=0.0)
        parsed = extract_json_from_text(response)
        
        if parsed and "reply" in parsed:
            # 如有要求则保存到记忆
            if parsed.get("save_to_memory"):
                self.memory.add(parsed["save_to_memory"])
            
            self.state.increment_step()
            return parsed
    
    return None
```

注意:
- **记忆检索**——`memory.get_all()` 加载所有已存储的记忆
- **上下文整合**——记忆被包含进 prompt 中
- **显式存储**——Agent 通过 JSON 显式说明要保存什么
- **自动持久化**——一旦提供了 `save_to_memory`,它就会被自动存储

## 如何运行

看 `complete_example.py` 里的 `lesson_07_memory()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

# 第一次交互——存储名字
response1 = agent.run_with_memory("My name is Alice")
if response1 and "reply" in response1:
    print(f"Response 1: {response1['reply']}")

# 第二次交互——回忆名字
response2 = agent.run_with_memory("What's my name?")
if response2 and "reply" in response2:
    print(f"Response 2: {response2['reply']}")

print(f"Memory contents: {agent.memory.get_all()}")
```

![记忆系统](diagrams/lesson-07-memory.png)

## 与第 06 课的对比

**第 06 课(Agent 循环):**
```
Loop -> Step 1 -> Step 2 -> Step 3 -> Done
         |         |        |
       Action   Action   Action
```
状态在循环内持续存在,但循环结束时就被重置。

**第 07 课(记忆):**
```
Interaction 1 -> Save "name is Alice" -> Memory stores it
Interaction 2 -> Load memory -> "Your name is Alice"
```
记忆跨完全独立的多次交互持续存在。

## 关键洞见

### 记忆是显式的存储

记忆是**显式的存储**,而不是意识。它是你可以查看、修改和删除的数据。这里没有任何隐藏的推理——只有被存下来的事实。

### 越简单越强大

这个记忆系统很简单:存储字符串,再把它们全部取出来。但它却极其有用。更复杂的检索可以放到后面,而这套基础已经能用了。

### 由 Agent 控制存储

Agent 通过 `save_to_memory` 字段决定要保存什么。你也可以把这一步自动化,但显式控制能让行为更可预测。

### 上下文加载

记忆会被加载进 prompt 上下文。模型并不能直接访问记忆——它只能看到你放进 prompt 里的内容。

## 常见问题

**「Agent 没有保存信息」**
- 检查响应里是否包含 `save_to_memory`
- 确认 memory.add() 确实被调用了
- 确保 prompt 清楚地说明了何时该保存

**「Agent 忘事」**
- 确认记忆确实被加载进了 prompt
- 检查记忆是否跨调用持续存在
- 确保记忆上下文字符串确实被包含进去了

**「记忆变得太大」**
- 这个简单系统会永远存储所有记忆
- 可以考虑加入记忆上限或删除机制
- 更复杂的系统可以对记忆做优先级排序或摘要

## 练习

1. 保存多个事实,看看它们如何累积
2. 试着询问一些不在记忆里的内容
3. 手动查看 `agent.memory.get_all()`,看看存储的数据
4. 修改记忆的格式,观察它如何影响行为

## 下一步是什么?

在[第 08 课](08_planning.md)中,我们将加入**规划**——把复杂目标拆解成一连串步骤的能力。

---

**核心要点:** 记忆 = 数据存储,而不是思想。它是显式的、可查看的,并赋予 Agent 跨交互的连续性。
