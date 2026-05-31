# 第 04 课 —— 用 LLM 做决策

## 我们要回答什么问题?

**「模型能不能决定该做什么,而不只是回答问题?」**

这是**能动性(agency)**的第一次显现。模型不再只是用生成的文本来回应,而是从一组有限的选项中挑选动作。

## 你将构建什么

一个决策系统,它会:
- 给模型呈现一组有限的选项
- 强制模型恰好选出一个选项
- 校验决策,失败时重试
- 用这个决策来路由后续执行

## 引入的新概念

### 1. 决策 Schema(Decision Schemas)

**决策 schema** 是一组有限的、模型必须从中挑选的选项。模型不再生成自由文本,而是从预定义的动作中选择,比如「answer_question」「summarize_text」或「translate」。

这会极大地收窄输出空间——不再是无限种可能的回复,而只剩下少数几个合法的选项。

### 2. 路由逻辑(Routing Logic)

一旦做出决策,你的代码就可以据此**路由**执行流程。如果模型选了「summarize_text」,你就调用摘要函数;如果它选了「translate」,你就调用翻译函数。

这正是 Agent 根据自己「决定」要做的事,走上不同路径的方式。

### 3. 意图识别(Intent Detection)

通过把用户输入当作一个决策问题来构造,你其实是在做**意图识别**。模型分析用户想要什么,并把它映射到你提供的某个可用动作上。

这比试图解析自由文本来理解意图要简单得多。

## 我们(暂时)不做什么

- 不用工具([第 05 课](05_tools.md))
- 不构建 agent loop([第 06 课](06_agent_loop.md))
- 不用记忆([第 07 课](07_memory.md))
- 不做规划([第 08 课](08_planning.md))

## 代码

看 `agent/agent.py` 中的 `decide()` 方法:

```python
def decide(self, user_input: str, choices: list[str]) -> str | None:
    """
    让模型从一组有限的选项中做出选择。
    
    第 04 课版本。
    
    Args:
        user_input: 需要做决策的输入
        choices: 可选动作/决策的列表
        
    Returns:
        选中的动作;若决策失败,则返回 None
    """
    options = "\n".join(f"- {choice}" for choice in choices)
    
    prompt = f"""{self.system_prompt}

You must choose ONE of the following options. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Available choices:
{options}

Required JSON format:
{{"decision": "one_of_the_choices_above"}}

User request: {user_input}

Response (JSON only):"""
    
    for attempt in range(3):
        response = self.llm.generate(prompt, temperature=0.0)
        parsed = extract_json_from_text(response)
        
        if parsed and "decision" in parsed:
            decision = parsed["decision"]
            if decision in choices:
                return decision
    
    return None
```

注意我们新增了:
- **有限的选择空间** —— 模型必须从一个预定义的列表中挑选,而不是随意生成
- **校验** —— 我们会检查这个决策是否真的在选项列表里
- **结构化输出** —— 沿用第 03 课中相同的 JSON 提取模式
- **重试逻辑** —— 最多尝试 3 次以拿到一个合法的决策

## 如何运行

看 `complete_example.py` 中的 `lesson_04_decisions()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/llama-3-8b-instruct.gguf")

decision = agent.decide(
    "Can you summarize this article for me?",
    choices=["answer_question", "summarize_text", "translate"]
)

print(decision)
# Output: "summarize_text"
```

## 与第 03 课对比

**第 03 课(结构化输出):**
```
Input: "What is AI?"
Output: {"answer": "AI is...", "confidence": "high"}
```
模型生成结构化数据,其中的值是它自己创造出来的。

**第 04 课(决策):**
```
Input: "Summarize this article"
Choices: ["answer_question", "summarize_text", "translate"]
Output: "summarize_text"
```
模型从预定义的选项中做选择——不生成,只挑选。

## 关键洞见

### 挑选 vs 生成

模型不再生成内容,而是**从一个有限的动作空间中挑选**。这与自由文本生成有本质区别,也可预测得多。

### 能动性从这里开始

这正是 Agent 开始有「Agent 的样子」的地方。它不只是在回应——它在选择该做什么。这些选项也许很简单,但这个模式很重要。

### 受约束 = 可靠

通过把选项限制在一个小而明确的集合里,你让系统变得更可靠。模型无法凭空捏造出新的动作——它只能从你的列表里挑。

### 校验至关重要

永远要校验这个决策是否真的在你的选项列表中。模型可能返回某个看起来像决策、但并不在你允许集合里的东西。

## 常见问题

**「模型返回了一个不在我列表里的选项」**
- 用选项列表来做校验(代码已经这么做了)
- 把选项名取得清晰、无歧义
- 可以考虑加一次带更明确指令的重试

**「所有决策看起来都很随机」**
- 检查你的各个选项在语义上是否彼此区分明显
- 确保用户输入确实和这些选项相关
- 把 temperature 调得更低,以获得更确定的挑选结果

**「模型加上了解释」**
- `extract_json_from_text()` 辅助函数会处理这种情况
- 更强硬的指令会有帮助(代码里已经有了)
- 可以考虑直接拒绝带有额外文本的返回

## 练习

1. 创建一个有 5 个以上选项的决策,并用不同的输入测试
2. 试试有歧义的输入,看看模型会挑哪个选项
3. 加一个「none_of_the_above」选项,看看它在什么时候被选中
4. 对比 temperature 为 0.0 和 0.5 时的决策结果

## 接下来是什么?

在[第 05 课](05_tools.md)中,我们会引入**工具(tool)**——Agent 可以请求调用的能力,用以突破纯文本生成的局限。

---

**核心要点:** 决策 = 能动性。Agent 会做选择,而不只是回应。约束选项让行为变得可预测。
