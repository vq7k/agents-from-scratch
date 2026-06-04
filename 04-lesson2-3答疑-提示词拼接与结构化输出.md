# lesson2 / lesson3 答疑：提示词怎么拼、结构化输出怎么"填表"

> 本文沉淀学完 lesson2（system prompt）与 lesson3（结构化输出）后提出的 7 个问题，按"输入侧 / 输出侧"两层归类：
> 1. 手拼 `User:/Assistant:` 喂 qwen 为什么是错的？（§1.1）
> 2. `schema = """..."""` 三引号顶格写，是不是格式 bug？（§1.2）
> 3. schema 里的 `string` / `|` 是什么意思、起什么作用？（§2.1）
> 4. 模型只填了 `topic`/`difficulty`，"但是没回答我的问题啊"？（§2.2）
> 5. 课程代码为什么这么设计（用 topic/difficulty 而不是"解释"）？（§2.3）
> 6. 调试打印的"原始返回 / 格式化后"为什么两行一模一样？（§2.4）
> 7. 模型"完全按提示词返回了"吗？我看到的是预期回复吗？（§2.5）
>
> 一句话主线：**LLM 只会给定文本续写 token。你把输入拼成什么"形状"，并用 schema 约束输出成什么"形状"，决定了你拿到什么。** 拼输入是 lesson2，约束输出是 lesson3。
>
> 📖 怎么读：每节标题下的 **🎯 一句话** 是该节速览；只想要结论，直接翻到文末「§3 一页速查表」；想懂原理再读对应小节。

---

## 0 一条主线串起所有问题

```
LLM = 给定一段文本，续写下一个 token（循环）
   │
   ├─ 输入侧：把"角色 + 指令 + 请求"拼成模型认得的形状（§1）
   │     ├─ 对话模板要对（ChatML，lesson2）         → §1.1（详见 02 文档）
   │     └─ 三引号是字面量，所见即所得               → §1.2
   │
   └─ 输出侧：用 schema 约束模型产出的形状（lesson3，§2）
         ├─ schema 是"给模型看的格式说明"，不是真 JSON  → §2.1
         ├─ 心智模型：填表，不是问答（schema 是表头）    → §2.2
         ├─ 课程为何用 topic/difficulty 这种 schema     → §2.3
         ├─ extract 把文本解析成 dict（response 没变）   → §2.4
         └─ 形状对 = 预期；值由模型判断，故有防御机制    → §2.5
```

输入侧解决"模型听不听得懂我要它干嘛"，输出侧解决"它的回答能不能被程序可靠地用起来"。

---

## 1 输入侧：prompt 是怎么拼的

### 1.1 手拼 `User:/Assistant:` 喂 qwen 为什么是错的

**🎯 一句话｜** qwen 的母语是 ChatML；喂它老式 `User:/Assistant:`，它认不出角色和结束符 → 续写 / 串台 / 停不下来。

`llm.generate` 走的是**文本补全**接口（`llm(prompt=...)`），模型只看到我们拼的纯文本，**没人帮它套对话格式**。指令模型靠训练时那套"对话模板"的分隔符判断「轮到我说话 / 该在哪停」。

- 老式 Vicuna / Llama-2：用纯文本 `User:` / `Assistant:` 当分隔符。
- 我们的模型是 **Qwen**，母语是 **ChatML**：`<|im_start|>role\n内容<|im_end|>`，其中 `<|im_start|>` / `<|im_end|>` 是词表里的**特殊 token**，不是普通字符。

喂 qwen 它没学过的 `User:/Assistant:`，它认不出「谁在说话、该在哪停」，表现就是续写用户的话、角色串台、停不下来。所以本项目所有手拼 prompt 的方法都改成了 ChatML：

```python
prompt = (
    f"<|im_start|>system\n{self.system_prompt}<|im_end|>\n"
    f"<|im_start|>user\n{user_input}<|im_end|>\n"
    f"<|im_start|>assistant\n"          # 留空 assistant 段，等模型续写
)
```

> 这一块的完整机制（为什么 stop 是 `<|im_end|>`、为什么裸文本会停不下来、本地 vs 服务端谁套模板）见 `02-从LocalLLM理解对话格式与结束符.md` 和 `03-本地调用与服务端API-格式与结束符由谁处理.md`。本文不重复。

### 1.2 三引号 `"""..."""` 顶格写，不是格式 bug

**🎯 一句话｜** 三引号是字面量，所见即所得；顶格是为了发给模型的文本不带多余缩进。

lesson3 里这段 schema 看着"没对齐"：

```python
    schema = """{
  "topic": string,
  "difficulty": "beginner" | "intermediate" | "advanced"
}"""
```

**不是 bug。** 三引号字符串是**字面量**——引号里的每个空格、每个换行都原样进字符串，**不受代码缩进影响**。它真正的值是：

```
'{\n  "topic": string,\n  "difficulty": "beginner" | "intermediate" | "advanced"\n}'
```

即一段干净的、2 空格缩进的文本。**顶格写是故意的**：如果为了代码"好看"把里面也跟着缩进，那些前导空格会**真的**进字符串，发给模型的 schema 就变脏了。

> 验证：`print(repr(schema))` 就能看到真实值。
>
> 备选：若想代码里缩进对齐又不弄脏内容，用 `textwrap.dedent("""\ ...""")`，它会在运行时剥掉每行公共的前导空白（剥完要 `== 原值` 才算没改变内容）。[^pydedent]

---

## 2 输出侧：结构化输出（lesson3 主体）

### 2.1 schema 里的 `string` / `|` 是什么——"伪 schema"

**🎯 一句话｜** 它是写给模型看的"伪 schema"（格式说明），不是真 JSON，不拿去 `json.parse`。

注意 `string`（裸词）和 `|`（竖线）**都不是合法 JSON**。这是**故意的**：这段 schema 不是拿去 `json.parse` 的数据，而是**写给 LLM 看的"输出格式说明"**，是 TypeScript 风味的类型描述：

- `string` → 这个字段要填一个字符串
- `"a" | "b"` → 这个字段只能取列出的值之一（枚举）

它的**读者是模型，不是解析器**。运行时它被塞进 `Agent.generate_structured` 的 prompt 里（`必须遵循的 schema:\n{schema}`），模型照着这个结构**产出**真正合法的 JSON，再由 `extract_json_from_text` 解析。所以写得像伪代码反而更好懂。

### 2.2 心智模型：结构化输出 = 填表，不是问答 ⭐

**🎯 一句话｜** schema 是表头，模型只填你给的列；没有"解释"列，它就不会解释。

这是本轮**最重要的认知**。现象：输入"解释一下量子计算"，模型却返回

```json
{ "topic": "量子计算", "difficulty": "beginner" }
```

**根本没解释。** 但这不是模型的错，是 **schema 的错**——

> 结构化输出不是"问问题等回答"，而是"定义一张表让模型填空"。**schema 就是表头，模型只会填你给的列。**

这张表只有两列 `topic` / `difficulty`，**没有 `explanation` 这一列**，模型无处安放"解释"，只能把"解释一下量子计算"**当成待提取的素材**，填出 topic 和它判断的 difficulty。想要解释，就得先在 schema 里给它留个字段：

```json
{
  "topic": string,
  "explanation": string,        ← 加这一栏，解释才有地方放
  "difficulty": "beginner" | "intermediate" | "advanced"
}
```

一句话记住：**想要什么，先在 schema 里给它留个字段。**

### 2.3 课程代码为什么这么设计（topic/difficulty，而不是"解释"）

**🎯 一句话｜** lesson3 教"输出形状"不教"回答质量"；topic/difficulty 的枚举字段对错一眼可验。

因为 **lesson3 教的是"输出的形状"，不是"回答的质量"。** 原作者故意挑了一个元数据提取 / 分类式的 schema，用最少字段演示两种约束：

| 字段 | 类型 | 演示什么 |
|---|---|---|
| `topic` | string | 自由字符串字段 |
| `difficulty` | `"beginner"｜"intermediate"｜"advanced"` | **枚举**——值必须三选一，对错一眼可验 |

枚举字段"对错一眼可验"，正好聚焦 lesson3 的核心：**形状约束 + 校验 + 重试**。若换成 `explanation: string`（长文本），重点会滑向"这段解释写得好不好"，模糊掉"约束形状"这件事。

> 副作用：输入"解释一下量子计算"配 topic/difficulty 显得答非所问——这是 demo 的一个小瑕疵（更贴切的输入是"量子计算"或"判断这个话题的难度"），不影响教学目的。这正是 §2.2 那个困惑的来源。

### 2.4 调试里"原始返回 / 格式化后"为什么两行一模一样

**🎯 一句话｜** 两次打印的都是 `response`；`extract` 把结果给了 `parsed`。而 extract + 重试是"兜底"防御，这次没触发 ≠ 没用。

调试时这样打印：

```python
response = self.llm.generate(prompt, temperature=0.0)
print(f"原始返回 : {response}")
parsed = extract_json_from_text(response)   # ← 解析结果给了 parsed，没动 response
print(f"格式化后 : {response}")              # ← 打印的还是 response，当然一样
```

两行一样，是因为**两次打印的都是 `response`**。`extract_json_from_text` **不会"格式化" `response`**，它做的是：从文本里抠出 JSON、解析成 **Python dict 返回给 `parsed`**。`response` 自始至终没变。

真正"解析后"的东西是 `parsed`，也就是最后那行 `Structured result: {'topic': '量子计算', ...}`——注意它是**单引号**，那是 Python dict 的 `repr`（已经从 JSON 字符串变成对象了），不再是 JSON 文本。"格式化后"这个标签名不副实，要看转变应该打印 `parsed`。

**为什么这次看不出 `extract_json_from_text` 的作用——它是"兜底"设计** ⭐

`extract_json_from_text` 是**防御性设计**：模型有时会在 JSON 外面包一层 ` ```json `、加一句"好的，这是你要的："、或在前后掺解释。这个函数负责从这种"脏文本"里**抠出** JSON 再解析。

这次模型很守约，直接吐了干净 JSON，所以它"抠"的动作等于没抠（抠出来 == 原文）；重试 `for attempt in range(3)` 也只跑了第一次就 `return`，第 2、3 次根本没执行。

> 措辞精确化：不是"`parsed` 这行没执行"——它**一定执行**（每次调用都会跑，这次也成功解析了）。准确说是：它代表的**容错 + 重试能力这次没被迫启用**，因为没出现"模型不守约"的 case。

**关键设计思想**：这层防御**总会执行，但它的价值只在模型不守约时才显现**。没被触发 ≠ 没用——它是为"LLM 不总是听话"这个事实**兜底**，把模型当作一个**可能出错的组件**来对待。这也是为什么 lesson3 的核心不是"写个聪明 prompt"，而是"prompt + 解析 + 重试"这一整套：**带兜底的简单方案，胜过没兜底的聪明方案**。

### 2.5 模型"完全按提示词返回了"吗？我看到的是预期回复吗

**🎯 一句话｜** 形状逐条达标 = 预期回复；但"这次合规 ≠ 每次合规"，且具体值是模型判断、不保证一致。

**是的，但要分两层说清楚。**

**形状层面（lesson3 的验收标准）——逐条达标：**

| prompt 要求 | 实际输出 | |
|---|---|---|
| 只输出合法 JSON | 纯 JSON，无多余字 | ✓ |
| 不要解释 / markdown / 前后多余文本 | 没有 ` ```json `、没有前言后语 | ✓ |
| 以 `{` 开头、`}` 结尾 | 是 | ✓ |
| 遵循 schema | `topic` 是字符串、`difficulty` 取了枚举三选一的值 | ✓ |
| 可被解析 | 成功变成 Python dict | ✓ |

所以从"形状对不对"看，**这就是预期回复。**

**但有两个"不保证"：**

1. **这次合规 ≠ 每次合规。** `temperature=0.0` + 请求简单让它很稳，但模型本质是概率性的，换个输入它可能包一层 ` ```json `、加一句"好的，这是你要的 JSON"、或漏字段。**正因如此，代码有三道防御**：`extract_json_from_text`（容错抠 JSON）+ `for attempt in range(3)`（重试）+ `if parsed is not None`（校验）。这次三道都没派上用场，不代表它们多余。
2. **值不保证和文档一致。** 你跑出 `difficulty: "beginner"`，文档示例写 `advanced`——这**不是偏差**。具体值是模型的**主观判断**，随输入 / 模型 / 温度而变；文档里的值只是**示意**。

> 一句话：**结构化输出只保证"形状对"，不保证"模型的内容判断和别人一致"。** 形状对 = 预期；值不同 = 正常。

---

## 3 一页速查表

| 我问的 | 一句话结论 | 详见 |
|---|---|---|
| 手拼 `User:/Assistant:` 喂 qwen 行不行 | 不行，qwen 母语是 ChatML，认不出角色 / 结束符 | §1.1 |
| 三引号 schema 顶格是不是格式 bug | 不是，字面量所见即所得，顶格保证发给模型的文本干净 | §1.2 |
| schema 里 `string` / `\|` 是什么 | 伪 schema（写给模型看的格式说明），不是真 JSON | §2.1 |
| 为什么没回答我（只填字段没解释） | 结构化输出 = 填表；schema 没"解释"列就不解释 | §2.2 |
| 课程为何用 topic/difficulty | 教形状不教内容质量；枚举一眼可验 | §2.3 |
| "原始 / 格式化后"为何两行一样 | 打印的都是 `response`；`extract` 把结果给了 `parsed` | §2.4 |
| 我看到的是预期回复吗 | 形状达标 = 预期；值（beginner）是模型判断，不保证一致 | §2.5 |

---

## 脚注 / 延伸

[^pydedent]: Python 官方文档：`textwrap.dedent`（移除每行公共前导空白）<https://docs.python.org/3/library/textwrap.html#textwrap.dedent> ；三引号字符串字面量见 *Lexical analysis · String literals* <https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals> 。

- 输入侧机制（对话模板 / eos / 本地 vs 服务端）：见本仓库 `02-从LocalLLM理解对话格式与结束符.md`、`03-本地调用与服务端API-格式与结束符由谁处理.md`。
- 结构化输出的工业级做法（用 JSON Schema 强约束输出）可参考 OpenAI *Structured Outputs* 指南 <https://platform.openai.com/docs/guides/structured-outputs> ——本课程用的是"把 schema 写进 prompt + 解析 + 重试"的极简版，原理相通。

> 验证方式：§1.2 / §2.4 的结论均可在本机用 `repr()` / 打印 `parsed` 直接复现；§2.5 的"形状达标"对照本机实际运行输出。外部仅附稳定的官方文档链接供延伸，未逐条联网核对（区别于 03 文档的信源级考据）。
