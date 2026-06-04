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
    # ChatML 格式(见第 02 课):system 放角色,user 放指令 + schema + 请求
    prompt = (
        f"<|im_start|>system\n{self.system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n"
        f"严格要求:\n"
        f"1. 只输出合法的 JSON\n"
        f"2. 不要解释、不要 markdown、JSON 前后不要有多余文本\n"
        f"3. 必须以 {{ 开头、以 }} 结尾\n\n"
        f"必须遵循的 schema:\n{schema}\n\n"
        f"用户请求: {user_input}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    # 最多尝试 3 次
    for attempt in range(3):
        response = self.llm.generate(prompt, temperature=0.0)
        parsed = extract_json_from_text(response)
        
        if parsed is not None:
            return parsed
    
    return None
```

注意我们新增了:
- **强力指令** —— 用「严格要求」明确提出「只输出 JSON」,并禁止解释 / markdown / 多余文本
- **ChatML 格式** —— 沿用第 02 课的 `<|im_start|>...<|im_end|>` 划分 system / user / assistant(Qwen 的母语格式)
- **temperature 控制** —— 用 `temperature=0.0` 获得更确定、更一致的输出
- **JSON 提取** —— `extract_json_from_text()` 用来处理模型加了额外文本的情况
- **重试逻辑** —— 最多尝试 3 次以拿到合法 JSON,把概率性的行为变成可靠的结果

## 如何运行

看 `complete_example.py` 中的 `lesson_03_structured()` 方法:

```python
from agent.agent import Agent

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")

# schema 是给模型看的"输出格式说明"(伪 schema),不是真 JSON:
# string 表示填字符串,"a" | "b" 表示只能取其一。
schema = """{
  "topic": string,
  "difficulty": "beginner" | "intermediate" | "advanced"
}"""

result = agent.generate_structured("解释一下量子计算", schema)

print(result)
# {'topic': '量子计算', 'difficulty': 'advanced'}
```

## 这为什么重要

### 之前(自由文本)
```
Output: "好的!这个话题难度中等,我建议你先从基础概念入手……"
```
- 无法解析
- 不一致
- 不可靠

### 之后(结构化)
```
Output: {'topic': '量子计算', 'difficulty': 'advanced'}
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
- 在 prompt 中强调「只输出合法的 JSON」

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
