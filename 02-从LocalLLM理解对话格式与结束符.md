# 从 LocalLLM 理解模型的对话格式与结束符

> 本文从一个极简的本地大模型封装类 LocalLLM 出发，依次说明：模型如何标记一段输出的结束、结束符（eos）是什么、为什么一段默认配置会与 qwen 模型不匹配、如何查证、配置错误的后果、如何修改，最后说明 LocalLLM 的结构本质。
>
> 顺序：读代码 → 默认 stop → 发现不匹配 → 对话格式与 eos → 查证 → 后果 → 修改 → 结构本质。
>
> 文中代码均已贴出，脱离原项目也可阅读。

---

## 1 起点：LocalLLM 封装了什么

LocalLLM 是对 llama-cpp-python（本地运行 GGUF 模型的库）的封装，对外提供一个"输入文本、返回文本"的接口。

### 1.1 完整代码

模型加载耗时且占用内存（数 GB）。用类在 `__init__` 中加载一次、存入实例，之后每次 `generate()` 复用：

```python
from llama_cpp import Llama


class LocalLLM:
    """对 llama-cpp-python 的封装：输入文本、返回文本。"""

    def __init__(self, model_path, temperature=0.2,
                 max_tokens=512, n_ctx=2048, n_gpu_layers=-1):
        # 模型加载一次，存入 self.llm，之后复用
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx,
                         n_gpu_layers=n_gpu_layers, verbose=False)
        self.max_tokens = max_tokens

    def generate(self, prompt, temperature=None, stop=None):
        kwargs = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            # 默认 stop —— 问题在这一行（见第 2、3 节）
            "stop": stop if stop is not None else ["</s>", "\n\n", "User:", "Assistant:"],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        response = self.llm(**kwargs)              # 调用底层模型，返回一个 dict
        return response["choices"][0]["text"].strip()
```

### 1.2 generate() 内部的数据流

调用方传入一个 prompt，`generate()` 内部的处理过程：

```
prompt 字符串
   │  ① 拼成参数字典 kwargs = {prompt, max_tokens, stop}
   ▼
self.llm(**kwargs)                 ② 调用底层模型（llama.cpp 推理）
   │  返回一个 dict
   ▼
response["choices"][0]["text"]     ③ 取出生成的文本
   │  .strip()
   ▼
返回字符串
```

---

## 2 generate() 里的默认 stop

`generate()` 拼 `kwargs` 时有一项 `stop`，调用方不传时使用这组默认值：

```python
"stop": stop if stop is not None else ["</s>", "\n\n", "User:", "Assistant:"],
```

模型逐个 token 生成输出。`stop` 是一组停止序列：当生成的内容中出现 `stop` 列表里的任一字符串时，生成在该处停止。

---

## 3 默认 stop 与本机模型不匹配

### 3.1 模型真身是 qwen2.5

这台机器上加载的 GGUF 文件名为 `llama-3-8b-instruct.gguf`，但文件内容是 qwen2.5。文件名只是标签（复制时沿用了旧名），不代表内容。判断模型类型应依据文件内容，不能依据文件名。

### 3.2 默认 stop 是老式 Vicuna / Llama-2 风格

这 4 个 stop 串没有一个对应 qwen：

| stop 项 | 来源 | 对 qwen 的作用 |
|---|---|---|
| `</s>` | Llama-2 的结束符 | 无效（qwen 不生成它） |
| `\n\n` | 通用的段落分隔约定 | 有害（会截断多段回答） |
| `User:` / `Assistant:` | Vicuna 风格对话标记 | 无效（qwen 不使用） |

### 3.3 拼 prompt 同样是 Vicuna 风格

调用方（一个 agent）在调用 `generate()` 之前拼接的 prompt 也使用了 `User:/Assistant:`：

```python
def generate_with_role(self, user_input):
    # self.system_prompt 用于设定模型的角色
    prompt = f"""{self.system_prompt}

User: {user_input}
Assistant:"""              # 手写 "User:/Assistant:"，老式 Vicuna 风格，非 qwen 所用格式
    return self.llm.generate(prompt)
```

因此问题在两处：拼 prompt 使用 Vicuna 标记、stop 使用 Vicuna 串，整体假设了模型属于 Vicuna / Llama 系。要理解差异，需先了解模型的对话格式。

---

## 4 模型的对话格式与结束符

### 4.1 对话格式（chat template）与结束符（eos）

instruct 模型训练时，对话被特殊 token 包装成固定格式，模型据此区分发话方与每轮的边界。其中标记"一轮输出结束"的特殊 token 称为结束符 eos（End Of Sequence）。程序检测到 eos 即停止生成。

### 4.2 各模型不同

没有统一标准，各模型训练时各自约定[^qwen]：

| 模型 | 结束符 eos | 对话标记 |
|---|---|---|
| qwen（ChatML） | `<\|im_end\|>` | `<\|im_start\|>role` |
| Llama-2 | `</s>` | `[INST] ... [/INST]` |
| Llama-3 | `<\|eot_id\|>` | `<\|start_header_id\|>role` |
| Vicuna | `</s>` | `USER:` / `ASSISTANT:` |

### 4.3 qwen 的 eos 是 `<|im_end|>`

qwen 使用 ChatML 格式：im 指 instant message（对话消息），`<|im_start|>` 标记一轮开始，`<|im_end|>` 标记一轮结束。因此 qwen 的 eos 是 `<|im_end|>`，编号 151645。

默认 stop 中的串均属其他模型，qwen 的结束符 `<|im_end|>` 不在该列表内。

---

## 5 查证：如何确认 qwen 的 eos

两种方式都可查证，结果一致[^qwen][^hf]。

### 5.1 查看官方配置（最直接）

模型的 HuggingFace 页面 → Files → 打开 `tokenizer_config.json` → 查看 `eos_token` 字段，Qwen 官方填写为 `<|im_end|>`[^qwen]。

### 5.2 用代码读取模型文件（本机实证）

GGUF 文件记录了模型自身的特殊 token，`llama_cpp` 可直接读取：

```python
from llama_cpp import Llama

# vocab_only=True：只加载词表，不加载权重
llm = Llama("模型文件.gguf", vocab_only=True, verbose=False)
print(llm.token_eos())                                  # → 151645
print(llm.detokenize([llm.token_eos()], special=True))  # → b'<|im_end|>'
```

两种方式指向同一结果：151645 对应 `<|im_end|>`。

---

## 6 配置错误的后果（实测）

将其他模型的 stop 与格式用于 qwen，会产生两类问题。

### 6.1 问题一：`\n\n` 截断回答

默认 stop 含 `\n\n`，当 qwen 的回答中出现空行时，生成在该处停止，空行之后的内容被丢弃。例如要求模型分两段输出、将关键标记放在第二段时，默认 stop 下第二段会丢失。

### 6.2 问题二：raw 格式导致输出质量下降

不使用 qwen 的 ChatML 包装、直接传入裸 prompt 时，qwen 会产生与请求无关的内容。对同一请求分别用两种格式：

```python
raw    = "请逐字重复：第一段：天气不错。（中间空一行）第二段：DONE_MARKER"
chatml = "<|im_start|>user\n" + raw + "<|im_end|>\n<|im_start|>assistant\n"
# 各运行一次，对比输出
```

实测输出（repr 形式，`\n` 表示换行）：

```
【raw 裸格式】  ' 1.0.0\n\n第一段：天气不错。\n\n第二段：DONE_MARKER 1.0.0\n\n好的，以下是...'
               输出开头为无关内容 1.0.0，并重复、附带多余文字

【ChatML 格式】 '第一段：天气不错。\n\n第二段：DONE_MARKER'
               输出与请求一致
```

`1.0.0` 是 raw 格式下 qwen 产生的无关输出。使用 qwen 训练所用的 ChatML 格式后，输出与请求一致。

---

## 7 修改方法

### 7.1 最小改动：使用 qwen 的 stop

将 `generate()` 的默认 stop 改为 qwen 的结束符：

```python
"stop": stop if stop is not None else ["<|im_end|>"],
```

只改这一处，所有不传 stop 的调用都会使用新默认值。

### 7.2 进阶改动：由库自动套用模板

llama-cpp-python 提供高层接口 `create_chat_completion`，它会读取 GGUF 内置的对话模板并使用正确的 eos：

```python
response = self.llm.create_chat_completion(
    messages=[{"role": "user", "content": prompt}]
)
```

这样更换模型时无需手改 stop 或拼 prompt。代价是接口从"prompt 字符串"变为"messages 列表"，影响所有调用方。极简版保留 raw 调用，此处仅说明存在该方式。

---

## 8 LocalLLM 的结构本质：一个本地 LLM 封装（SDK）

从结构上看 LocalLLM 与 OpenAI SDK 的封装方式。

### 8.1 封装结构相同

```
              创建 client        调方法          拼参数     调后端          解析返回
LocalLLM :    LocalLLM(path)     .generate()     kwargs     self.llm()      ["choices"][0]["text"]
OpenAI SDK:   OpenAI(key, url)   .create()       JSON       HTTP POST       解析 JSON
```

### 8.2 区别：后端位置不同

```
LocalLLM    ──调用──▶  本地模型（本机，进程内函数调用）
OpenAI SDK  ──调用──▶  远程服务器（如 OpenAI / DeepSeek，HTTP 网络请求）
```

返回结构也相近（都包含 `choices` / `finish_reason`），因为 `llama_cpp` 采用了与 OpenAI 一致的返回格式[^openai]。

### 8.3 OpenAI SDK 多出的部分

封装结构与 LocalLLM 相同，远程 SDK 另外处理：网络（HTTP）、认证（api_key 放入请求头）、流式（分块返回）、重试与超时。LocalLLM 只保留封装的核心结构，省略了这些部分。

### 8.4 由此看 eos / 格式由谁处理

这说明了本地需要处理 eos、而云端调用看不到 eos 的原因：

```
LocalLLM（本地）：  直接调用模型  →  eos / stop 由调用方处理（需指定 <|im_end|>）
云端 API：          经过服务端    →  服务端处理 eos，只返回"已停止"的标志
                                    （调用方看不到 eos）
```

| | LocalLLM（本地） | 云端 API / 服务端（如 OpenAI 兼容接口） |
|---|---|---|
| 后端 | 本机模型 | 远程服务器 |
| stop / eos | 调用方设置 `["<\|im_end\|>"]` | 服务端处理，调用方不可见 |
| 格式适配 | 调用方负责 | 服务端负责 |
| 联网 / 计费 | 不联网、无费用 | 联网、按 token 计费 |

LocalLLM 处于最底层（直接调用模型），底层细节由调用方处理。改用 `create_chat_completion` 或云端 API 时，这些细节由库或服务端处理，调用方不再接触。

### 8.5 补充：别把"客户端 SDK"和"服务端"的职责搞混（常见误解）

第 8.1–8.3 把 LocalLLM 类比成"一个 SDK"，又指出远程 SDK 还要管网络、认证、流式、重试。这容易让人误以为"套对话格式、处理 eos"也是 SDK（客户端库）干的。**不是。** 职责分界是：

| 谁 | 负责什么 |
|---|---|
| 客户端 SDK（如 `openai` 库） | 网络（HTTP）、认证（api_key）、重试、超时、流式解析 |
| 服务端 / 本地推理库的高层接口 | **套对话模板、tokenize、按 eos/stop 截断、抽取回答** |

套模板 / 处理 eos **永远在持有模型的那一端**（服务端，或本地的 `create_chat_completion`），绝不在客户端 SDK——因为 chat completions 的 **API 契约本身就只收 `messages`**，而"该套哪套对话模板"由**服务端的模型配置**决定（闭源服务还不公开）；客户端即便持有 tokenizer（如 OpenAI 自家开源的 `tiktoken`，纯本地数 token），也无从知道要套什么模板。

这点用 DeepSeek 官方 API 文档可直接坐实[^deepseek]：调用方**只传结构化 `messages`（`{role, content}`），文档不要求、也不允许传任何"对话模板 / prompt 格式"**；模型的结束符 eos 通常不会回传给你，你只会拿到一个 `finish_reason`（`stop` = 自然停止或命中你设的 stop 串；`length` = 撞到 max_tokens）。也就是说，**云端 API 把"对话格式 + eos"这层对调用方完全隐藏了**——"拿来就用"时根本意识不到它的存在，只有像 LocalLLM 这样裸调本地模型，这层才暴露出来、需要你亲手处理。

> 这也是为什么本文要从 LocalLLM 讲起：它把云端 API 替你藏起来的东西，原原本本摆在你面前。

---

## 脚注（信息源）

[^qwen]: Qwen 官方 `tokenizer_config.json`（`eos_token` = `<|im_end|>`、编号 151645）。<https://huggingface.co/Qwen/Qwen2.5-7B/blob/main/tokenizer_config.json>
[^hf]: Qwen 概念文档（特殊 token / chat template）。<https://qwen.readthedocs.io/en/latest/getting_started/concepts.html>
[^openai]: OpenAI API Reference — Chat Completions（返回结构 `choices` / `finish_reason`）。<https://platform.openai.com/docs/api-reference/chat>
[^deepseek]: DeepSeek 官方 API 文档 — *创建对话补全（Create Chat Completion）*。请求体仅含结构化 `messages`（`role`/`content`），不接受任何对话模板 / prompt 格式；`stop` 为"一个 string 或最多包含 16 个 string 的 list，在遇到这些词时 API 将停止生成"；`finish_reason` 取值含 `stop`（"模型自然停止生成，或遇到 stop 序列中列出的字符串"）与 `length`（"达到 max_tokens 或上下文长度限制"）。<https://api-docs.deepseek.com/zh-cn/api/create-chat-completion>
