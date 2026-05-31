# 第 03 课 —— 让输出变得可靠

## 我们要回答什么问题?

**「我怎样才能不再去解析自由文本?」**

自由文本形式的回复是不可预测的。模型有时会加上解释,有时会换一种格式,有时还会产生幻觉。我们需要**结构**。

## 你将构建什么

一个系统,它会:
- 强制模型输出 JSON
- 校验返回结果
- 失败时重试

## 引入的新概念

### 1. 输出契约(Output Contracts)

**输出契约**是对模型必须返回什么内容的一份规约。我们不再说「回答这个问题」,而是说「返回符合这个 schema 的 JSON」。

```json
{
  "answer": string,
  "confidence": "high" | "medium" | "low"
}
```

### 2. 信任边界(Trust Boundaries)

永远不要直接信任 LLM 的输出。永远要:
1. 解析它
2. 校验它
3. 处理失败情况

这是第一个真正的「工程」时刻——把 LLM 当作一个可能会出错的组件来对待。

### 3. 校验(Validation)

校验确保输出符合你的契约:
- 它是合法的 JSON 吗?
- 它包含必需的字段吗?
- 各个值的类型对不对?

## 代码

看 `agent/agent.py` 中的 `generate_structured()` 方法:

```python
def generate_structured(self, user_input: str, schema: str) -> dict | None:
    """
    生成结构化的 JSON 输出,带校验和重试。
    
    第 03 课版本。
    
    Args:
        user_input: 用户的问题或请求
        schema: JSON schema 的描述
        
    Returns:
        解析后的 JSON 字典;若所有重试都失败,则返回 None
    """
    prompt = f"""{self.system_prompt}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no extra text before or after the JSON
3. Start your response with {{ and end with }}

Schema you must follow:
{schema}

User request: {user_input}

Response (JSON only):"""
    
    # 最多尝试 3 次
    for attempt in range(3):
        response = self.llm.generate(prompt, temperature=0.0)
        parsed = extract_json_from_text(response)
        
        if parsed is not None:
            return parsed
    
    return None
```

注意我们新增了:
- **强力指令** —— 用「CRITICAL INSTRUCTIONS」明确提出「只输出 JSON」的要求
- **temperature 控制** —— 用 `temperature=0.0` 获得更确定、更一致的输出
- **JSON 提取** —— `extract_json_from_text()` 用来处理模型加了额外文本的情况
- **重试逻辑** —— 最多尝试 3 次以拿到合法 JSON,把概率性的行为变成可靠的结果

## 如何运行

看 `complete_example.py` 中的 `lesson_03_structured()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/llama-3-8b-instruct.gguf")

schema = '''
{
  "topic": string,
  "difficulty": "beginner" | "intermediate" | "advanced"
}
'''

result = agent.generate_structured(
    "Explain quantum computing",
    schema
)

print(result)
# {"topic": "'quantum computing", "difficulty": "advanced"}
```

## 这为什么重要

### 之前(自由文本)
```
Output: "Okay! This task is medium difficulty. I'd suggest building..."
```
- 无法解析
- 不一致
- 不可靠

### 之后(结构化)
```
Output: {'topic': 'quantum computing', 'difficulty': 'advanced'}
```
- 可解析
- 可预测
- 已校验

## 关键洞见

### LLM 是概率性的

它们不会每次第一次就输出合法的 JSON。重试能把概率性的行为变成可靠的行为。

### 结构胜过小聪明

一个带校验的简单 prompt,胜过一个不带校验的聪明 prompt。

### 这就是工程

你正把 LLM 当作系统中的一个组件来对待:
- 输入:prompt + schema
- 输出:经过校验的数据,或错误
- 重试:如果校验失败

## 常见问题

**「模型在 JSON 之前加上了解释」**
- 使用 `extract_json_from_text()` 辅助函数(它会从文本中找出 JSON)
- 在 prompt 中强调「ONLY valid JSON」

**「仍然收到非法的返回」**
- 调低 temperature 以获得更确定的输出
- 把 schema 写得更具体
- 使用专门为结构化输出训练过的模型

**「重试消耗了太多 token」**
- 3 次重试通常已经足够
- 跟踪重试次数,以此监控模型质量

## 接下来是什么?

在[第 04 课](04_decision_making.md)中,我们会加入**决策**——让模型选择要采取的动作,而不只是回答问题。

---

**核心要点:** 结构化输出 + 校验 = 可靠的 Agent。
