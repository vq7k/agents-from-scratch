# lesson4 / lesson5 答疑：决策与工具调用

> 本文记录学完 lesson4（决策）与 lesson5（工具调用）后的 6 个问题：
> 1. `decide()` 在做什么？跟 lesson3 有何不同？（§1.1）
> 2. lesson4 是不是特别简单？（§1.2）
> 3. lesson5 没有工具注册逻辑、没明确讲参数？（§2.2）
> 4. 重头逻辑是不是在 `tools.py` 的封装、嵌套了几层？（§2.3）
> 5. 原始输出 `{"tool": "calculator", ...}` 说明了什么？（§2.4）
> 6. 一个 dict 怎么变成 `calculator(a=42, ...)` 调用？（§2.5）
>
> 主线：lesson3 让模型按指定字段输出，lesson4 让模型从给定选项中选一个，lesson5 让模型输出工具名和参数。三课使用同一套公共结构（ChatML 壳 + JSON 提取 + 重试 + 校验），区别是输出空间逐步收窄，lesson5 接上真实函数执行。
>
> 怎么读：只看结论翻到文末「§3 速查表」；要原理读对应小节。

---

## 0 主线

```
lesson3   按指定字段输出      输出空间 = 你给的字段，值由模型生成
lesson4   从选项中选一个      输出空间 = choices 里的某一个合法值
lesson5   输出工具名 + 参数    输出 {tool, arguments}，并执行真实函数

公共结构（三课相同）：ChatML 壳 + extract_json + for range(3) 重试 + 校验
```

lesson4 解决"模型能否决定做什么"，lesson5 解决"模型能否让系统执行某个函数"。

---

## 1 lesson4：决策

### 1.1 `decide()` 在做什么

结论：把输出限定为给定选项中的一个。这是 agent 第一次从有限选项中选择动作。

对比：

| | 输入 | 输出 | 说明 |
|---|---|---|---|
| lesson3 | "解释一下量子计算" | `{"topic":"量子计算","difficulty":"advanced"}` | 值由模型生成 |
| lesson4 | "帮我总结这篇文章" | `"summarize_text"` | 从给定选项中选一个 |

`decide(user_input, choices)` 的核心是两步：

```python
options = "\n".join(f"- {c}" for c in choices)   # ① 把选项写进 prompt
# … 让模型输出 {"decision": "..."} …
if decision in choices:                          # ② 成员校验：必须在选项内
    return decision
```

输出被限定在有限集合内，模型无法返回选项以外的值，因此结果可预测。

### 1.2 lesson4 为什么简单

结论：它是最简单的几节之一。相对 lesson3，新增内容只有两点。

| 复用 lesson3 | lesson4 新增 |
|---|---|
| ChatML 壳、`extract_json_from_text`、`for range(3)` 重试、`temperature=0.0` | ① 输出限定为枚举 `choices`<br>② `decision in choices` 成员校验 |

机制都是 lesson3 的，新增的只是把输出收窄为有限选项。

lesson5（工具）、lesson6（agent loop）都依赖"模型能决策"这一步：loop 需要先决定下一个动作。lesson4 代码量小，是因为机制已在前三课建立，它只增加选项约束。

---

## 2 lesson5：工具调用

### 2.1 请求与执行分离

结论：模型输出工具调用请求，系统执行工具。两者分离。

`tools.py` 顶部注释：*Tool 是 API，不是能力。Agent 请求 tool；由系统来执行它们。*

流程：

```
request_tool          execute_tool                 calculator
模型输出 {tool,args}  →  用 **args 解包调用  →  真函数执行  →  返回结果
```

与 lesson4 的区别：decide 只选一个标识符；工具调用要带参数、执行函数、返回结果。lesson5 第一次调用真实函数，294 由函数计算得出。

模型实际收到的完整 input（`request_tool` 把 instructions 和 ChatML 壳拼接后、喂给 `llm.generate` 的纯文本）：

```text
<|im_start|>system
你是一个冷静、严谨、乐于助人的 AI 助手。你用简单的方式解释概念，避免不必要的术语。你对自己知道和不知道的事情都保持诚实。始终用中文回答。<|im_end|>
<|im_start|>user
你是一个会调用工具的助手,只回答数学问题。只输出合法的 JSON。

可用工具: calculator
- 参数: a (数字), b (数字), operation ("add"、"subtract"、"multiply" 或 "divide")

严格要求:
1. 只输出合法的 JSON
2. 不要解释、不要 markdown、JSON 前后不要有多余文本
3. 必须以 { 开头、以 } 结尾

示例格式:
{"tool": "calculator", "arguments": {"a": 42, "b": 7, "operation": "multiply"}}

用户请求: 42 乘以 7 等于多少?<|im_end|>
<|im_start|>assistant
```

模型看到的是这段纯文本（f-string 在运行时才拼成它），不是源码。可对照看三点：三段式 `system` / `user` / `assistant` 的真实长相（`system` 放角色，`user` 放工具说明 + 指令 + 请求）；`assistant` 段留空结尾，模型从这里续写出 §2.4 那条 JSON；`system` 的"始终用中文回答"与 `user` 段的"只输出合法的 JSON"同时在场，本次模型让 JSON 指令优先。

### 2.2 没有工具注册 / 没讲参数

结论：结构化 schema 已定义（`get_tool_schema`），但全程未被调用；prompt 里的工具名和参数是硬编码的。

`tools.py` 有三个零件，用了两个：

| 零件 | 是什么 | 是否使用 |
|---|---|---|
| `calculator(a,b,operation)` | 工具函数 | 是，被 `execute_tool` 调 |
| `execute_tool` | 派发表 `{"calculator": calculator}` + `**arguments` 解包 | 是 |
| `get_tool_schema` | 结构化 schema（`type`/`enum`/`required`） | 否，只被 import，无调用 |

具体：

1. 工具注册：`execute_tool` 的 `{"calculator": calculator}` 是注册表的最小形态，但写死单条目，加工具要手改 dict。
2. 参数：结构化参数定义（`a: number`、`operation: enum`、`required`）写在 `get_tool_schema` 里，但 `request_tool` 没用它，prompt 里另写了一遍。两份定义独立维护，可能不一致。
3. 校验：文档 `05_tools.md` 说"附带结构化参数""执行前校验"，但代码只检查 `tool`/`arguments` 两个 key 存在、tool 名存在，不校验参数的类型 / 必填 / enum。参数错误会在 `calculator(**arguments)` 抛 `TypeError`。文档描述多于代码实现。

lesson5 只实现请求 / 执行分离，未实现注册表、schema 联动、参数校验。

进阶练习：① 把 `request_tool` 的 prompt 改为从 `get_tool_schema()` 生成；② 在 `execute_tool` 执行前按 schema 校验 arguments。

### 2.3 重头逻辑在哪

结论：嵌套在执行侧，属于职责分层；新增逻辑在请求侧 `request_tool`。

执行侧：

```
execute_tool_call（薄包装）  →  execute_tool（派发 + 解包）  →  calculator（真逻辑）
```

`execute_tool` 是常规派发，逻辑简单，谁调用都一样。lesson5 的新增内容在请求侧：让模型产出 `{tool, arguments}`（识别意图、填参数）。

执行侧的层数来自请求 / 执行分离，不是逻辑复杂度。

### 2.4 原始输出说明了什么

结论：它是请求，不是结果。294 尚未计算。

实跑 `request_tool("42 乘以 7 等于多少?")`，原始返回：

```json
{"tool": "calculator", "arguments": {"a": 42, "b": 7, "operation": "multiply"}}
```

三点：

1. 模型输出请求，不直接计算。若直接返回 294，就退回 lesson1。
2. 意图到参数映射正确："42 乘以 7"拆为 `a=42 / b=7 / operation=multiply`，工具名也对。
3. 294 尚未产生：这串 JSON 只是请求，计算由执行侧完成。

### 2.5 dict 怎么变成函数调用

结论：`execute_tool` 用 `**arguments` 把参数 dict 展开为关键字参数。

```python
def execute_tool(tool_name, arguments):
    tools = {"calculator": calculator}          # 派发表：名字 → 函数
    if tool_name not in tools:
        raise ValueError(f"Unknown tool: {tool_name}")
    return tools[tool_name](**arguments)         # ** 解包
```

`**arguments` 把 `{"a":42, "b":7, "operation":"multiply"}` 展开，等价于：

```python
calculator(a=42, b=7, operation="multiply")   #  → 294
```

`arguments` 的 key 必须和函数形参名一致（`a`/`b`/`operation`），这是 prompt 要告诉模型参数名的原因。

---

## 3 速查表

| 问题 | 结论 | 详见 |
|---|---|---|
| `decide()` 跟 lesson3 的区别 | 从生成值变为从选项中选一个；新增枚举约束 + 成员校验 | §1.1 / §1.2 |
| lesson4 是否简单 | 是，相对 lesson3 只新增两点；它是后续决策类功能的基础 | §1.2 |
| 没有工具注册 / 没讲参数 | `get_tool_schema` 未被调用，prompt 硬编码，无参数校验 | §2.2 |
| 重头是否在 `tools.py` | 嵌套在执行侧（职责分层），新增逻辑在请求侧 | §2.3 |
| `{"tool":...}` 输出 | 是请求不是结果，294 尚未计算 | §2.4 |
| dict 怎么变成调用 | `**arguments` 解包为关键字参数 | §2.5 |

---

## 脚注 / 延伸

- 公共结构（ChatML 壳 / `extract_json` / 重试 / 校验）见 `04-lesson2-3答疑-提示词拼接与结构化输出.md`；对话模板与结束符见 `02-…` / `03-…`。
- 工具调用的工业级做法（JSON Schema 强约束 + 服务端校验参数）见 OpenAI Function calling 指南 <https://platform.openai.com/docs/guides/function-calling>。本课程是极简版：工具名和参数写进 prompt + 解析 + 重试；`get_tool_schema` 已定义但未接入。
- 验证：§2.2（`get_tool_schema` 未被调用、`execute_tool` 写死派发表且不校验参数）、§2.5（`**` 解包）可在本机 `grep get_tool_schema` / 读 `agent/tools.py` 复现；§2.4 原始输出取自本机实跑 `lesson_05_tools()`。外部链接未逐条联网核对。
