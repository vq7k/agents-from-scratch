# 对话格式与结束符的处理位置：本地调用与服务端 API

> 本文说明三个问题，结论均附官方信源：
> 1. lesson_01 的 `generate()` 已设置 `stop=["<|im_end|>"]`，为何未停止，而是持续续写。
> 2. ChatML / 对话模板（chat template）的定义。
> 3. 同一请求经 DeepSeek API 返回单轮回答的原因，以及本地调用与服务端 API 的区别。
>
> 结论：套用对话模板、处理结束符（eos/stop）、抽取回答，由服务端或推理库的高层接口完成，不由客户端 SDK 完成。客户端 SDK（如 `openai` 库）只负责网络、认证、重试、流式。

---

## 0 因果链

```
LLM 基本行为 = 续写 token 序列
        │
        ├─ 输入裸文本（lesson_01）          → 模型按文档续写 → 持续生成 → 达到 max_tokens 才停止
        │
        └─ 输入经对话模板包装的文本           → 模型识别 assistant 回合 → 生成结束符 eos → stop 命中并停止
                │
                ├─ 本地：调用方自行包装，或用 create_chat_completion 包装
                └─ 服务端 API：服务端包装（调用方只传 messages）
```

---

## 1 LLM 的基本行为：续写 token 序列

HuggingFace 文档：

> "All causal LMs, whether chat-trained or not, continue a sequence of tokens. ... The list of `role` and `content` dictionaries that you pass to a chat model get converted to a token sequence, often with control tokens like `<|user|>` or `<|assistant|>` or `<|end_of_message|>`, which allow the model to see the chat structure."[^hf]

译：所有因果语言模型，无论是否针对对话做过训练，都只是续写一段 token 序列。传给对话模型的 `role`/`content` 字典列表会被转换为 token 序列，通常带有 `<|user|>`、`<|assistant|>`、`<|end_of_message|>` 等控制 token，使模型能识别对话结构。

- 所有因果语言模型（无论是否经过对话微调）只执行一种操作：给定 token 序列，预测下一个 token，循环执行。
- "一问一答"不是模型的内建能力，而是用特殊 token（控制 token）将文本标注为对话结构的结果。模型在训练中接触该结构，据此识别角色边界与回合结束。

---

## 2 stop 未触发的原因

### 2.1 stop 的判定方式

stop 是截断触发器：当生成文本中出现 stop 列表中的某个字符串时，在该位置停止。判定依据是模型实际输出的内容，而非回答是否完成。

### 2.2 模型未生成 `<|im_end|>`

`<|im_end|>` 是对话回合结束的特殊 token。模型仅在识别到对话结构（输入含 `<|im_start|>assistant` 起始标记）时，才会在回答后生成该 token。

lesson_01 的 `simple_generate` 传入裸文本（`agent.py` 中为 `return self.llm.generate(user_input)`），不含对话标记。模型将其作为普通文档续写；此类语料多为 FAQ / 教程结构，因此模型继续生成后续问答。普通文档不含 `<|im_end|>`，模型不生成该 token，stop 不触发，生成持续至 `max_tokens=512` 被截断。

即：停止于第 3 段是达到 token 上限，而非回答完成。

### 2.3 官方说明

HuggingFace 文档在说明 `add_generation_prompt`（在输入末尾追加 assistant 起始标记）时指出：

> "if you don't include these tokens, the model may get confused and do something strange, like continuing the user's message instead of replying to it!"[^hf]

译：如果不包含这些 token，模型可能会困惑并做出异常行为，例如继续续写用户的消息，而不是回复它。

lesson_01 缺少该起始标记，行为即文档所述的"继续续写用户消息而非回复它"（continuing the user's message instead of replying）。

> 验证：将 stop 改为 `["\n\n"]` 或 `["请"]`，lesson_01 会在首段后停止，因为模型会生成空行或"请"。这表明 stop 依据实际输出，与回答是否完成无关。

---

## 3 ChatML 与对话模板

### 3.1 ChatML

ChatML（Chat Markup Language）用特殊 token 标注多轮对话的角色与边界：

```
<|im_start|>system
你是一个助手<|im_end|>
<|im_start|>user
解释一下什么是 AI agent?<|im_end|>
<|im_start|>assistant
```

- `<|im_start|>` / `<|im_end|>`（im = instant message）是词表中的单个特殊 token，非普通字符拼接。
- 末尾的 `<|im_start|>assistant` 为 assistant 起始标记。模型回答后生成 `<|im_end|>`，`stop=["<|im_end|>"]` 在此命中。
- Qwen2.5 的 eos 为 `<|im_end|>`，token 编号 151645。[^qwen]

### 3.2 对话模板因模型而异

ChatML 是其中一种格式。`apply_chat_template` 将 `messages` 列表渲染为模型专属格式，依据 tokenizer 的 `chat_template` 属性[^hf]。同一基座微调出的模型，模板可能不同：

| 模型 | 渲染结果片段 | 结束符 eos |
|---|---|---|
| Mistral-7B-Instruct | `<s>[INST] Hello [/INST]...` | `</s>` |
| Zephyr-7B | `<\|user\|>\nHello</s>\n<\|assistant\|>\n` | `</s>` |
| Qwen（ChatML） | `<\|im_start\|>user\n...<\|im_end\|>` | `<\|im_end\|>` |
| Llama-3 | `<\|start_header_id\|>user<\|end_header_id\|>...` | `<\|eot_id\|>` |

HuggingFace 文档指出，使用错误的控制 token 会导致"明显更差的性能"（"drastically worse performance"）[^hf]；这是 02 文档中裸格式导致 qwen 输出无关内容的原因。

文档另有说明："Chat templates should already include all the necessary special tokens"（译：对话模板应已包含所有必要的特殊 token）[^hf]——即模板已含所需特殊 token（含 eos），不应重复添加。

---

## 4 本地调用与服务端 API：模板与 eos 的处理位置

### 4.1 客户端 SDK 与服务端的分工

| 层 | 代表 | 负责 | 不负责 |
|---|---|---|---|
| 客户端 SDK | `openai` 库 | 将 `messages` 序列化为 JSON、HTTP 发送、认证、重试、超时、流式解析 | 套对话模板、tokenize、处理 eos/stop |
| 服务端 / 推理引擎 | OpenAI 后端、DeepSeek 后端、vLLM、本地 llama.cpp | 用模型配套的 chat template 将 `messages` 渲染为 token、推理、按 eos/stop 截断、抽取 assistant 内容返回 | —— |

`openai` 库的官方描述为 "convenient access to the OpenAI REST API from any Python 3.9+ application"（译：为任何 Python 3.9+ 应用提供访问 OpenAI REST API 的便捷方式）[^openai-py]，即 REST API 的封装，不包含客户端侧的 prompt 格式化、模板渲染或 tokenization。

### 4.2 服务端套用模板：以 vLLM 为例

vLLM 是 OpenAI 兼容的推理服务端，文档说明：

> "The `/v1/chat/completions` endpoint applies a chat template according to the user's input format and feeds that value to the LLM."[^vllm]
>
> "vLLM requires the model to include a chat template in its tokenizer configuration. The chat template is a Jinja2 template that specifies how roles, messages, and other chat-specific tokens are encoded in the input."[^vllm]
>
> "The renderer converts an OpenAI-style request ... into prompt token ids by converting a list of messages to a single string-format prompt and then tokenizing the prompt to prompt token ids."[^vllm]

译（依次）：
1. /v1/chat/completions 端点根据用户输入格式套用对话模板，并把结果喂给 LLM。
2. vLLM 要求模型在其 tokenizer 配置中包含对话模板；该模板是 Jinja2 模板，规定角色、消息及其他对话专用 token 如何编码进输入。
3. 渲染器把 OpenAI 风格的请求转换为 prompt token ids：先将消息列表拼成单个字符串形式的 prompt，再 tokenize 为 token ids。

eos/stop 在服务端处理后，默认不将结束符返回客户端：

> "chat completions from `/v1/chat/completions` should not include the stop token in the text returned to the client."[^vllm]

译：/v1/chat/completions 返回给客户端的文本中不应包含 stop token。

即 02 文档所述"云端调用看不到 eos"：服务端用其完成截断后，从返回文本中移除[^llamacpp-eos]。

### 4.3 DeepSeek API 文档验证

DeepSeek chat completion 接口契约说明"客户端只传 messages、服务端负责其余"，三点[^deepseek]：

1. 请求仅含结构化 `messages`，不含模板/格式。每条为 `{role, content}`（role ∈ system / user / assistant / tool）。文档不要求、也不接受任何对话模板 / chat template / prompt 格式。
2. API 的 `stop` 参数与模型内置 eos 不同。文档定义 `stop` 为"一个 string 或最多包含 16 个 string 的 list，在遇到这些词时 API 将停止生成"，属调用方自定义停止串；模型自带的 `<|im_end|>` 由服务端处理。
3. eos 不返回，响应仅含 `finish_reason`：
   - `stop`——"模型自然停止生成，或遇到 stop 序列中列出的字符串"（自然停止即模型生成 eos，被服务端识别、截断、移除）。
   - `length`——"输出长度达到了模型上下文长度限制，或达到了 max_tokens 的限制"。

> 对应关系：lesson_01 达到 `max_tokens=512` 被截断，对应 `finish_reason = length`；正常单轮回答对应 `finish_reason = stop`。API 隐藏了对话格式与 eos，调用方不接触；本地裸调 llama.cpp 时该层暴露。

> 边界：DeepSeek 公开的是 API 契约（请求与响应字段），不公开内部模板字符串。"客户端只传 messages、服务端负责模板与 eos"的分工由该契约确定。OpenAI 同理（`openai` 库为 REST 封装，见 4.1）。

---

## 5 本地复现服务端行为：`create_chat_completion`

`llama-cpp-python`（`LocalLLM` 的底层依赖）提供两个接口，对应上述两种行为：

| 接口 | 行为 | 对应 |
|---|---|---|
| `create_completion()` / `llm(prompt)` | 裸文本补全，不套模板 | lesson_01，续写溢出 |
| `create_chat_completion(messages=[...])` | 自动套对话模板，等价于 OpenAI/DeepSeek 的 chat 接口 | 单轮回答 |

`create_chat_completion` 的工作方式：

> "The handler uses a `ChatFormatter` to convert structured messages into a model-specific prompt string. The handler invokes `create_completion` on the `Llama` instance with the formatted prompt."[^llamacpp-wiki]

译：handler 用 `ChatFormatter` 把结构化消息转换成模型专属的 prompt 字符串，再用该 prompt 调用 `Llama` 实例的 `create_completion`。

模板选择优先级：

> "Use the `chat_handler` if provided → use the `chat_format` if provided → use the `tokenizer.chat_template` from the gguf model's metadata (should work for most new models) → else fallback to the llama-2 chat format."[^llamacpp-doc]

译：若提供了 `chat_handler` 则用它 → 否则用 `chat_format` → 否则用 GGUF 元数据中的 `tokenizer.chat_template`（多数新模型适用）→ 都没有则回退到 llama-2 对话格式。

现代 GGUF 模型（含本机 qwen2.5）的 chat template 内嵌于模型文件，`create_chat_completion` 自动读取并使用对应格式与 eos，更换模型无需手动修改 stop。对应 02 文档 7.2 节。

> 代价：接口由 prompt 字符串变为 messages 列表，影响所有调用方。本课程保留裸 `create_completion`，用于展示无模板时的模型行为，作为后续课程中格式 / 停止 / 重试机制的对照基线。

---

## 6 三种调用方式对比

| | 本地·裸补全（lesson_01） | 本地·chat 接口 | 远程 API（OpenAI/DeepSeek） |
|---|---|---|---|
| 输入 | 裸 prompt 字符串 | `messages` 列表 | `messages` 列表 |
| 套对话模板 | 调用方 | llama-cpp-python 高层接口 | 服务端 |
| 处理 eos / stop | 调用方指定 `["<\|im_end\|>"]` | 库自动（读 GGUF 内置模板） | 服务端（返回时移除 eos） |
| 客户端 SDK 角色 | 无（进程内函数调用） | 无（进程内函数调用） | 网络 / 认证 / 重试 / 流式 |
| 联网 / 计费 | 否 / 无 | 否 / 无 | 是 / 按 token 计费 |
| 控制粒度 | 最底层 | 中等 | 最高层 |

---

## 7 与 02 文档的关系

02 文档 §8.4 已说明 eos / 格式适配由服务端负责、调用方不可见，结论正确。§8.5 补充了客户端 SDK 与服务端的职责分界：

> 客户端 SDK：网络、认证、重试、超时、流式。
> 服务端 / 本地推理库高层接口：套对话模板、tokenize、按 eos/stop 截断、抽取回答。

套模板与 eos 处理在持有模型的一端（服务端或本地推理库），不在客户端 SDK。

---

## 脚注（信息源）

[^hf]: HuggingFace Transformers 官方文档 — *Chat templates*。含 "All causal LMs ... continue a sequence of tokens"、`apply_chat_template` 读取 `chat_template`、`add_generation_prompt` 缺失时 "continuing the user's message instead of replying to it"、"Chat templates should already include all the necessary special tokens" 等原文。<https://huggingface.co/docs/transformers/en/chat_templating>
[^qwen]: Qwen 官方 `tokenizer_config.json`（`eos_token` = `<|im_end|>`，编号 151645）。<https://huggingface.co/Qwen/Qwen2.5-7B/blob/main/tokenizer_config.json> ；概念说明见 <https://qwen.readthedocs.io/en/latest/getting_started/concepts.html>
[^openai-py]: `openai/openai-python` 官方仓库 README — "convenient access to the OpenAI REST API from any Python 3.9+ application"；未提供任何客户端侧 prompt 格式化 / 模板渲染 / tokenization。<https://github.com/openai/openai-python>
[^vllm]: vLLM 官方文档 — *OpenAI-Compatible Server*。含 "/v1/chat/completions endpoint applies a chat template ... and feeds that value to the LLM"、"vLLM requires the model to include a chat template in its tokenizer configuration"、renderer 把 messages 转成 token ids、"should not include the stop token in the text returned to the client" 等原文。<https://docs.vllm.ai/en/stable/serving/openai_compatible_server/>
[^llamacpp-eos]: llama.cpp Issue #6859 — *OpenAI-Compatible Chat Completions API Endpoint Responses include EOS / stop tokens*（eos/stop 在服务端的处理与移除行为）。<https://github.com/ggml-org/llama.cpp/issues/6859>
[^llamacpp-wiki]: llama-cpp-python 文档（DeepWiki 整理）— *Chat Completion*。"The handler uses a `ChatFormatter` to convert structured messages into a model-specific prompt string. The handler invokes `create_completion` on the `Llama` instance with the formatted prompt."。<https://deepwiki.com/abetlen/llama-cpp-python/4.3-chat-completion>
[^llamacpp-doc]: llama-cpp-python 官方文档 — *Getting Started*，模板选用优先级（chat_handler → chat_format → gguf 内置 `tokenizer.chat_template` → fallback llama-2）。<https://llama-cpp-python.readthedocs.io/>
[^deepseek]: DeepSeek 官方 API 文档 — *创建对话补全（Create Chat Completion）*。请求体仅含结构化 `messages`（`role`/`content`，role ∈ system/user/assistant/tool），不接受任何对话模板 / prompt 格式；`stop` 为"一个 string 或最多包含 16 个 string 的 list，在遇到这些词时 API 将停止生成"；`finish_reason` 取值含 `stop`（"模型自然停止生成，或遇到 stop 序列中列出的字符串"）与 `length`（"输出长度达到了模型上下文长度限制，或达到了 max_tokens 的限制"）。<https://api-docs.deepseek.com/zh-cn/api/create-chat-completion>

---

> 验证方式：本文结论经联网检索并抓取官方页面交叉核对（HuggingFace / vLLM / openai-python / llama-cpp-python 官方文档及 llama.cpp issue）。开源推理栈为文档实证；闭源 OpenAI / DeepSeek 的"服务端套模板"依据公开 API 契约推断（内部私有格式不公开），见 4.3 节。
