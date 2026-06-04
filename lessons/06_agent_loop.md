# 第 06 课 —— Agent 循环(Agent Loop)

## 我们要回答什么问题?

**「它怎样才能从一个聊天机器人变成一个 Agent?」**

答案:当它能够**观察、决策、行动,并不断重复**,且带有状态(state)时。聊天机器人响应一次就停下,而 Agent 会朝着目标走出多个步骤。

## 你将构建什么

一个 agent loop,它能:
- 按顺序运行多个步骤
- 在各步骤之间维持状态
- 基于当前状态决定动作
- 在目标达成或超过最大步数时终止

## 引入的新概念

### 1. Agent 循环(Agent Loop)

**agent loop** 就是不断重复的循环:观察、决策、行动。每一轮迭代中,Agent 审视当前情境,决定该做什么,执行该动作,然后重复,直到完成。

这正是 Agent 区别于简单聊天机器人的地方——Agent 不会在一次响应后就停下。

### 2. 状态转移(State Transitions)

**状态转移**记录 Agent 的状态如何随每一步变化。状态可能包含步数、完成情况、累积的结果,或其他跟踪信息。

状态让循环能够感知自己的进展和历史。

### 3. 终止条件(Termination Conditions)

**终止条件**决定循环何时停止。常见的条件包括:
- Agent 判定自己「完成了」
- 达到最大步数
- 目标已达成
- 发生错误

没有终止条件,循环就会永远跑下去。

## 我们暂时还不做的事

- 还没有跨循环的记忆([第 07 课](07_memory.md))
- 还没有规划([第 08 课](08_planning.md))
- 还没有复杂的推理——只是简单的逐步决策

## 代码

看 `agent/agent.py` 里的 `agent_step()` 和 `run_loop()` 方法:

```python
def agent_step(self, user_input: str) -> dict | None:
    """
    执行 agent loop 的一步:观察、决策、行动。

    第 06 课版本。

    Args:
        user_input: 用户输入或系统观察

    Returns:
        动作决策,如果这一步失败则返回 None
    """
    state_dict = self.state.to_dict()
    
    # user 段:状态 + 可用动作 + 指令 + 输入,用三引号写成「所见即所得」的多行文本
    instructions = f"""你是一个 agent,必须决定下一个动作。只输出合法的 JSON。

当前状态: steps={state_dict.get('steps', 0)}, done={state_dict.get('done', False)}

可用动作: analyze, research, summarize, answer, done

严格要求:
1. 只输出合法的 JSON
2. 不要解释、不要 markdown、JSON 前后不要有多余文本
3. 必须以 {{ 开头、以 }} 结尾

必须遵循的格式:
{{"action": "动作名", "reason": "理由说明"}}

用户输入: {user_input}"""

    # 套上 ChatML 三段式外壳(格式见第 02 课 / generate_with_role)
    prompt = (
        f"<|im_start|>system\n{self.system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{instructions}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    for attempt in range(3):
        response = self.llm.generate(prompt, temperature=0.0)
        parsed = extract_json_from_text(response)
        
        if parsed and "action" in parsed:
            if "reason" not in parsed:
                parsed["reason"] = f"Taking action: {parsed['action']}"
            self.state.increment_step()
            return parsed
    
    return None

def run_loop(self, user_input: str, max_steps: int = 5):
    """
    运行 agent loop 若干步。

    Args:
        user_input: 初始用户输入
        max_steps: 最多执行的步数

    Returns:
        动作结果的列表
    """
    self.state.reset()
    results = []
    
    while not self.state.done and self.state.steps < max_steps:
        action = self.agent_step(user_input)
        
        if action:
            results.append(action)
            
            # 简单的终止条件
            if action.get("action") == "done":
                self.state.mark_done()
        else:
            break
    
    return results
```

注意:
- **状态跟踪**——每一步都会递增步数计数器并检查是否完成
- **循环结构**——`while not done` 会一直持续到终止
- **动作累积**——结果会跨步骤被收集起来
- **安全限制**——`max_steps` 防止无限循环

## 如何运行

看 `complete_example.py` 里的 `lesson_06_agent_loop()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

print("\nNote: Repetition in early iterations is expected.")
print("The agent refines its understanding step by step and may repeat analysis")
print("before converging on a clearer explanation.\n")

results = agent.run_loop("Help me understand loops", max_steps=3)

for i, result in enumerate(results, 1):
    print(f"Iteration {i}:")
    action = result.get("action", "unknown")
    reason = result.get("reason", "No reason provided")
    print(f"  Action: {action}")
    print(f"  Reason: {reason}")
    if i < len(results):
        print()
```

输出会展示每一轮迭代所采取的动作及其理由。注意:前几轮出现重复是正常的——Agent 是在一步步打磨自己的理解。

## 与第 05 课的对比

**第 05 课(工具调用):**
```
Request -> Tool call -> Result -> Done
```
单次交互:请求、执行、返回。

**第 06 课(Agent 循环):**
```
Input -> Step 1 -> Step 2 -> Step 3 -> Done
          |        |        |
        Action   Action   Action
```
多个步骤依次进行,每一步都决定接下来做什么。

![Agent 循环流程](diagrams/lesson-06-agent-loop.png)

## 关键洞见

### Agent 不是一个聪明的 prompt

Agent 不是一个聪明的 prompt,它是一个**带状态的循环**。神奇之处不在 prompt 里——而在于观察、决策、行动这一不断重复的循环。

### 状态带来连续性

没有状态,每一步都是相互独立的。有了状态,各步骤就能彼此叠加,并跟踪朝目标推进的进展。

### 终止至关重要

永远要设置终止条件。没有它们,循环可能永远运行,或不必要地消耗资源。`max_steps` 是个简单但必不可少的安全机制。

### 越简单越好

这个循环刻意保持简单。复杂的推理可以放到后面——首先要把「不断重复地行动」这个模式建立起来。

## 常见问题

**「循环永远停不下来」**
- 检查终止条件是否正确设置
- 确认 `max_steps` 确实被强制执行
- 确保 Agent 能够发出「完成」信号

**「每一步看起来都是独立的」**
- 在 prompt 里包含状态信息
- 把累积的结果传给后续步骤
- 让决策过程能看到状态

**「Agent 没有进展」**
- 检查动作是否真的改变了什么
- 确认状态被正确更新
- 确保 Agent 能看到相关的状态信息

## 练习

1. 修改可用的动作,看看循环如何适应
2. 改变 `max_steps`,观察它如何影响行为
3. 添加步数之外的其他状态变量
4. 尝试不同的终止条件

## 下一步是什么?

在[第 07 课](07_memory.md)中,我们将加入**记忆**,让 Agent 能够跨多次交互记住信息,而不仅仅是在单次循环内。

---

**核心要点:** Agent = 循环 + 状态。就这么简单。循环带来多步行为,状态带来连续性。
