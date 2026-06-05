# temperature 与 LLM 输出的确定性:问题分析与实测

> 本文记录并回答一个技术问题:同一输入循环调用 LLM,输出为何大概率相同、小概率不同。内容覆盖:问题现象与相关代码事实、对非确定性来源的候选假设、联网调研、本地实测、服务端(DeepSeek API)实测、最终结论与控制方法。所有结论均有实测数据或信源支撑。
>
> 主线:`temperature`[^temp] 控制随机性——`temperature=0` 为 greedy(取最高概率 token)[^greedy],`temperature>0` 为采样。本地(llama.cpp / Metal)实测 temp=0 为确定性映射;服务端(DeepSeek)实测 temp=0 亦复现,但不保证逐次确定(后端 `system_fingerprint`[^sysfp] 可变 + 多请求 batch invariance[^batch])。输出差异来自输入差异或采样,而非模型自身随机。
>
> 怎么读:只看结论翻 §5 与 §6 速查表;需要完整过程读 §1–§4。
> 配套:lesson6 见 `06a-lesson6答疑-agent循环与状态管理.md`;状态机概念见 `06c-状态机-从概念到订单流转设计.md`。

---

## 0 主线

```
现象：lesson6 的 run_loop 跑 N 轮，输出大多相同、偶尔不同
  │
问题：同一输入循环调用，为何大概率相同、小概率不同
  │
候选假设：H1 byte-identical / H2 GPU 浮点 / H3 随机 seed / H4 输入随 steps 变化
  │
调研：Thinking Machines / llama.cpp / llama-cpp-python / DeepSeek API 文档
  │
本地实测：temperature=0 共 38 次全同；temperature=0.8 共 8 次全不同
服务端实测：temperature=0 共 5 次全同；temperature=1.3 共 5 次全不同
  │
结论：temperature=0 → 本地实测确定（38 次全同 + logprobs[^logprobs] 验证每步取 argmax）；服务端复现但不保证（后端可变 + batch invariance）；差异源自输入或采样
```

---

## 1 问题描述

### 1.1 现象

lesson6 的 `run_loop("帮我理解 Agent", max_steps=10)` 输出:多数轮 `action`/`reason` 完全相同,少数轮措辞不同。示例 print 与文档描述为"逐步收敛到更清晰的解释",实际输出表现为重复。

### 1.2 待回答的问题

> 同一输入循环调用 LLM,为何输出大概率相同、小概率不同?随机性来自何处?

### 1.3 相关代码事实

| 事实 | 位置 |
|---|---|
| 每轮 prompt 含 `当前状态: steps={...}` | `agent/agent.py:378` |
| 推理使用 `temperature=0.0` | `agent/agent.py:401`(第 400 行为调试 `print`;行号以 grep 关键字为准) |
| 每轮结束执行 `increment_step()`(steps +1) | `agent/agent.py:407` |
| `Llama(...)` 未设 `seed`(默认 -1,即随机种子) | `shared/llm.py:44` |
| `n_gpu_layers=-1`(Apple Metal GPU) | `shared/llm.py:31` |
| 模型 | `qwen2.5-7b-instruct-abliterated.gguf` |

**关键推论**:`steps` 进入 prompt 且每轮 +1,因此 Iter1 的 prompt 含 `steps=0`、Iter2 含 `steps=1`……**每一轮的 prompt 输入并不相同**。这是后续判定的基础。

---

## 2 非确定性来源:候选假设与判定

对"输出为何会不同"列出候选假设,经调研(§3)与实测(§4)逐一判定:

| 假设 | 内容 | 判定(本机) | 判定依据 |
|---|---|---|---|
| H1 | `temperature=0` 时输出 byte-identical | **成立** | 实测:temp=0 共 38 次全同(§4.1);且 logprobs 验证每步取 argmax(实验⑦) |
| H2 | GPU 浮点非结合性[^fp]使 greedy 排序偶尔翻转 | **不成立** | Thinking Machines:隔离前向 run-to-run 确定;本机实测无差异 |
| H3 | 默认随机 `seed`(-1)使 `temperature=0` 仍随机 | **不成立** | 机制:greedy(argmax)不消费 RNG;实测:4 个不同 seed(含 -1)temp=0 全同(实验⑧) |
| H4 | 输出差异源自 prompt 随 `steps` 变化 | **成立** | 代码事实(§1.3)+ 实测:steps 0..9 递增 10 轮得 9 个不同(实验⑨) |

结论方向:差异由 **H4(输入变化)** 解释,**H2/H3 在本机不成立**。

---

## 3 调研(信源)

### 3.1 非确定性主因:batch invariance,而非浮点并发

[Thinking Machines — Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/):

- 同一矩阵乘法、同一输入重复执行,结果 bitwise 完全相同;
- **隔离的**单次前向 / 单个矩阵乘法,在同一输入(含固定 batch 组成)上 run-to-run bitwise 一致;LLM 前向**通常**不含需要 atomic add 的操作(原文限定 typically/usually);
- 推理服务非确定性的主因是 **batch invariance 缺失**:负载波动导致 batch size 变化,使同一请求的数值结果不同。**注意**:服务端即便用户只提交一条请求,该请求仍可能被与其他并发请求拼成同一 batch,故"用户 batch=1"在服务端**不等于**确定;确定仅在内核实际只处理这一条序列(batch 组成固定)时成立——本地单进程满足此条件(故 §4.1 实测确定),多请求服务端不满足。

### 3.2 Metal 后端与 llama-cpp-python 的已知行为

- Metal offload 未报告 run-to-run 非确定性(区别于 CUDA 首次请求差异,[llama.cpp #2838](https://github.com/ggml-org/llama.cpp/issues/2838))。
- [llama.cpp #4458](https://github.com/ggml-org/llama.cpp/issues/4458):报告的是 CPU-vs-GPU 分歧,非同机 run-to-run。
- llama-cpp-python 默认 `seed=-1`(随机),采用 sampler chain 架构;`temperature=0` 是否退化为纯 greedy 与版本相关,相关条目:[#972](https://github.com/abetlen/llama-cpp-python/issues/972) / [#890](https://github.com/abetlen/llama-cpp-python/issues/890) / [#1797](https://github.com/abetlen/llama-cpp-python/issues/1797) / [#1809](https://github.com/abetlen/llama-cpp-python/issues/1809)。

### 3.3 本地调研结论

理论上 `temperature=0` 为确定性 greedy,但 llama-cpp-python 的实际行为与版本相关,无法仅凭文档断定本机表现。判定需以本机实测为准。

### 3.4 DeepSeek API 文档(服务端)

温度建议见 [DeepSeek 参数文档](https://api-docs.deepseek.com/quick_start/parameter_settings);`system_fingerprint` 见 [DeepSeek Create Chat Completion API](https://api-docs.deepseek.com/api/create-chat-completion):

- `temperature` 默认值 **1.0**;按场景推荐:编码/数学 **0.0**、数据分析 1.0、通用对话/翻译 1.3、创作 1.5。(parameter_settings 页)
- 响应含 `system_fingerprint`——DeepSeek 官方定义为"标识模型运行所用的后端配置(the backend configuration that the model runs with)";该指纹变化即可能导致同输入结果偏移。(create-chat-completion 页)
- **关于 seed**:经 WebFetch 核实,DeepSeek 的 create-chat-completion API **未文档化 `seed` 参数**(请求参数列表无 seed,页面亦无 best-effort / determinism 字样)。常见"temperature=0 + 固定 seed 可复现、best-effort 不保证"的说法系 **OpenAI seed 文档口径**,不适用于 DeepSeek。本文据此**不依赖 DeepSeek seed**:服务端"不保证逐次确定"的判断仅基于 `system_fingerprint`(后端可变)与 §3.1 的 batch invariance。

即:服务端不保证逐次确定,与本地"实测确定"性质不同(根因即 §3.1 的 batch invariance 等服务端因素)。

---

## 4 实测

### 4.1 本地实测(llama.cpp / Metal)

统一环境:本机 venv + Metal,prompt 固定(无变化项):

```bash
venv/bin/python3 - << 'PYEOF'   # 在仓库根执行
import sys, hashlib
sys.path.insert(0, ".")
from shared.llm import LocalLLM
from shared.config import MODEL_PATH
prompt = ("<|im_start|>system\n你是一个 agent。<|im_end|>\n"
          "<|im_start|>user\n用一句话说明什么是循环。只输出 JSON：{\"action\":\"...\",\"reason\":\"...\"}<|im_end|>\n"
          "<|im_start|>assistant\n")
llm = LocalLLM(MODEL_PATH, max_tokens=80)
o = llm.generate(prompt, temperature=0.0)   # 调整 temperature 即为对照组
print(hashlib.sha1(o.encode()).hexdigest()[:10], repr(o[:90]))
PYEOF
```

| 实验 | 配置 | 次数 | 结果 |
|---|---|---|---|
| ① 同进程 | temp=0,同一 `Llama` 实例 | 5 | 全同 `sha1=65434c749a` |
| ② 跨进程 | temp=0,3 个独立进程(各自重置随机 seed) | 3 | 全同 `65434c749a` |
| ③ 高次数 | temp=0,同进程 | 30 | 全同(1 个版本) |
| ④ 对照 | `temperature=0.8`(启用采样) | 8 | 8 个全不同 |
| ⑦ greedy 验证 | temp=0,取 logprobs 看每步是否 top-1 | 1 | 15 token **全部** argmax |
| ⑧ 多 seed | temp=0,seed=1/42/12345/-1 | 4 | 全同 `sha1=7b20a575a5` |
| ⑨ steps 递增 | temp=0,仅 steps 0..9 变化 | 10 | **9 个不同**(steps 驱动分叉) |

实验 ①②③(temp=0)合计 38 次 bitwise 全同;`temperature=0.8` 时 8 次产生 8 个不同版本。

#### 4.1.1 原始输出

实验 ①(同进程,temp=0,5 次):

```
run 1: len=52 sha1=65434c749a :: {"action":"解释","reason":"循环是指事物以不断重复的方式进行运动或变化的过程。"}
run 2: len=52 sha1=65434c749a :: （同上）
run 3: len=52 sha1=65434c749a :: （同上）
run 4: len=52 sha1=65434c749a :: （同上）
run 5: len=52 sha1=65434c749a :: （同上）
>>> 5 次是否 bitwise 全同: True   不同版本数: 1
```

实验 ②(跨进程,temp=0,3 个独立进程):

```
独立进程 1: sha1=65434c749a :: {"action":"解释","reason":"循环是指事物以不断重复的方式进行运动或变化的过程。"}
独立进程 2: sha1=65434c749a :: （同上）
独立进程 3: sha1=65434c749a :: （同上）
```

实验 ③(高次数,temp=0,30 次,输出过长仅列统计):

```
总调用次数: 30
不同版本数: 1
分布: {'65434c749a': 30}
>>> 30 次是否全部 bitwise 相同: True
```

实验 ④(对照,temperature=0.8,8 次,同一 prompt):

```
run 1: sha1=e5addc4150 :: {"action":"描述一个过程在结束时返回开始的状态或位置。","reason":"这是循环的基本定义。"}
run 2: sha1=22f8ff7a72 :: {"action":"说明循环是指事物以不断重复的方式从某开始回到该点的过程。","reason":"定义循环的基本含义。"}
run 3: sha1=48d58c17ed :: {"action":"说明循环是指在一组事物中，某项事物通过重复回到自身或者回到起点的关系。","reason":"这是对循环这一概念的直接…"}
run 4: sha1=a198687563 :: {"action":"说明循环是事物以不断重复的形式向前发展的过程。","reason":"这是对循环这一概念的基本定义。"}
run 5: sha1=2b11145d58 :: {"action":"解释概念","reason":"循环是指事物在一系列过程中重复返回到原来状态或位置的现象。"}
run 6: sha1=3598598024 :: {"action":"用重复的过程或动作来说明循环。","reason":"循环是指一个过程或动作在相同或相似的条件下重复进行的现象。"}
run 7: sha1=812697991e :: {"action":"解释循环","reason":"循环是指一个过程在结束时返回到开始，形成一个闭合的序列。"}
run 8: sha1=30fa015ad3 :: {"action":"回答问题","reason":"循环是指一个过程或系列中前后相继的重复或连续。"}
>>> 8 次不同版本数: 8
```

#### 4.1.2 补充实测(greedy 机制 / seed 独立性 / steps 分叉)

实验 ⑦(greedy 验证,temp=0,`logits_all=True`,逐 token 检查生成 token 是否为 top-1):

```
step 0..14：chose 与 top1 全部一致（OK）
>>> 每一步都选 top-1（argmax / greedy 行为）：True
```

实验 ⑧(多 seed,temp=0,同一 prompt):

```
seed=1      sha1=7b20a575a5
seed=42     sha1=7b20a575a5
seed=12345  sha1=7b20a575a5
seed=-1     sha1=7b20a575a5
>>> 4 个 seed 是否全同：True
```

实验 ⑨(steps 递增,temp=0,仅 steps 0..9 变化,复现 lesson6 原始现象):

```
steps=0 sha1=7b20a575a5 :: analyze
steps=1 sha1=4a673e995e :: analyze
steps=2 sha1=b9d72c290b :: analyze
steps=3 sha1=de175333c1 :: research
steps=4 sha1=57df7a2fbf :: research
steps=5 sha1=2925227f97 :: research
steps=6 sha1=66691fb8a8 :: summarize
steps=7 sha1=037e95df01 :: summarize
steps=8 sha1=66691fb8a8 :: summarize
steps=9 sha1=934fc35b9c :: summarize
>>> 10 轮不同版本数：9（steps=6 与 8 偶合，其余各异）
```

说明:⑦ 证 temp=0 在本机走 argmax(greedy 行为);⑧ 证 seed 不影响 temp=0 输出,即**证伪 H3**("默认随机 seed 使 temp=0 仍随机"不成立);⑨ 证 steps 变化驱动分叉,**支撑 H4 成立**(复现 lesson6 原始现象)。

### 4.2 服务端实测(DeepSeek API)

OpenAI 兼容接口,`base_url=https://api.deepseek.com`,`model=deepseek-chat`。命令(key 用环境变量,勿写入文件):

```bash
PAYLOAD='{"model":"deepseek-chat","temperature":0,"max_tokens":60,"messages":[{"role":"user","content":"用一句话说明什么是循环。只输出这一句话。"}]}'
for i in 1 2 3 4 5; do
  curl -s https://api.deepseek.com/chat/completions \
    -H "Content-Type: application/json" -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
    -d "$PAYLOAD" | python3 -c "import sys,json,hashlib;d=json.load(sys.stdin);c=d['choices'][0]['message']['content'];print(hashlib.sha1(c.encode()).hexdigest()[:10], d.get('system_fingerprint'), repr(c))"
done
```

| 实验 | 配置 | 次数 | 结果 |
|---|---|---|---|
| ⑤ 服务端 | `deepseek-chat`,temp=0 | 5 | 全同 `sha1=a1f6439c0d` |
| ⑥ 服务端对照 | `deepseek-chat`,temp=1.3 | 5 | 5 个全不同 |

`system_fingerprint` 全程一致:`fp_8b330d02d0_prod0820_fp8_kvcache_20260402`(5+5 次均同 → 同一后端组合)。在此前提下 temp=0 复现、temp=1.3 分叉。

#### 4.2.1 原始输出

实验 ⑤(服务端,temp=0,5 次):

```
run 1: sha1=a1f6439c0d :: '循环是让计算机重复执行同一段代码，直到满足特定条件才停止的过程。'
run 2~5: sha1=a1f6439c0d :: （同上，5 次全同）
```

实验 ⑥(服务端对照,temp=1.3,5 次,fp 全同):

```
run 1: sha1=a0cf89f113 :: '循环是计算机反复执行同一段代码或根据条件重复执行特定动作的过程，直至满足退出条件。'
run 2: sha1=61748e396e :: '循环是重复执行同一组操作，直到满足某个退出条件的过程。'
run 3: sha1=dc757f5513 :: '循环是一种重复执行相同或相似操作直到条件不满足的流程控制结构。'
run 4: sha1=25c4362d35 :: '循环是一种控制结构，它允许重复执行相同的代码块，直到满足指定的条件。'
run 5: sha1=88af6c6df5 :: '循环是一种让同一段代码根据条件反复执行的控制结构。'
```

### 4.3 跨模型 / 跨栈验证(回应"单模型是否足够")

单一模型(qwen2.5-7b)不足以支撑跨模型/跨栈的普适性。为此在**另一个 stack**(Ollama,OpenAI 兼容 `/v1/chat/completions`)上对多个**当前主流模型**复测(temp=0 看确定性、temp>0 看分叉):

| 模型 | stack | temp=0 | temp>0 |
|---|---|---|---|
| qwen2.5-7b-abliterated | 本地 llama-cpp-python | 确定(38 次全同) | 分叉(④ 8 次全不同) |
| qwen2.5-7b-abliterated(**同款**) | Ollama | 确定(6 次全同 `532324aa6f`) | 分叉(3 次全不同) |
| gemma4:e4b(Google) | Ollama | 确定(6 次全同 `10823348bd`) | 分叉 |
| qwen3.5:9b-nvfp4(reasoning,新版) | Ollama | 确定(4 次全同 `00e5f45cff`) | — |

结论:
- **跨 3 个模型家族(qwen2.5 / gemma / qwen3.5)+ 2 个 stack(llama-cpp-python / Ollama),temp=0 一致确定、temp>0 一致分叉。**
- 尤其 **qwen2.5-7b-abliterated 同款模型在本地与 Ollama 两栈都确定**(sha1 各自不同仅因量化 / chat template 不同),隔离了"模型"变量,确认确定性来自"temp=0 走 greedy"而非某一特定实现。
- **已知例外**:2023 年的老模型 vicuna:7b(Ollama)temp=0 首次请求即分叉——归因于老模型 / 旧支持的特例,不代表当前主流模型,故不纳入普适性证据。
- 即:核心结论(temp=0 确定、差异来自输入)在当前主流模型 + 两个本地栈上**稳健成立**;但"确定性"本质仍是实现相关属性(§3.2),旧栈 / 旧模型可能例外,工程上以目标环境实测为准。

> 数据来源:Ollama 实测(2026-06-05)。注:`gemma4:26b` 在该端点返回空输出(疑模板/端点问题),已弃用,改用 `gemma4:e4b`;`qwen3.5` 为 reasoning 模型,需 `max_tokens≥1200` 方得非空最终回答。

### 4.4 复现说明

**环境**(sha1 强依赖以下,换任一项哈希必不同):
- 硬件 Apple M4 Pro / 64GB / macOS;后端 Metal(`n_gpu_layers=-1`)
- 本地栈:llama-cpp-python `0.3.24`;模型 `qwen2.5-7b-instruct-abliterated.gguf`(4683074048 字节 ≈ 4.68 GB);`n_ctx=2048`、`max_tokens=80`
- 另一栈:Ollama(`/v1/chat/completions`,OpenAI 兼容);服务端 DeepSeek `deepseek-chat`

**各实验复现要点**(以 §4.1 的 LocalLLM 命令为基线,改对应参数):
- ② 跨进程:把 §4.1 脚本作为独立进程多次运行(各自新建 `Llama`)。
- ③ 高次数:循环 N 次比 sha1。
- ④ / ⑥ 对照:`temperature` 改 0.8 / 1.3。
- ⑦ greedy:`Llama(..., logits_all=True)`,生成时传 `logprobs=5`,逐 token 比对生成 token 是否等于该位 top-1。
- ⑧ 多 seed:`Llama(..., seed=s)`,`s ∈ {1, 42, 12345, -1}`,temp=0,比 sha1。
- ⑨ steps 递增:固定其余文本,prompt 内 `steps` 取 0..9,各跑一次比 sha1。
- §4.3 跨栈:Ollama 用 `curl /v1/chat/completions`(见 §4.2 命令,换 `model`)。

**重要**:可复现的是**行为**(temp=0 确定 / temp>0 分叉 / steps 触发分叉),**不是具体 sha1 值**——sha1 随模型量化、stack、硬件而变。例:同款 qwen2.5-7b-abliterated,本地得 `65434c749a`、Ollama 得 `532324aa6f`,二者各自内部都确定,但哈希不同。引用本文 sha1 复现时,应核对"是否全同 / 是否分叉",而非追求相同哈希。

---

## 5 结论

### 5.1 核心结论

> `temperature` 控制随机性:`temperature=0` 取最高概率 token(greedy),`temperature>0` 按概率采样。
> - **本地**(Metal / qwen2.5-7b):temp=0 为**确定性映射**,与进程、调用次数、默认随机 `seed` 无关(实测 38 次全同)。
> - **服务端**(DeepSeek deepseek-chat):temp=0 本次实测亦全同(5 次,`system_fingerprint` 一致),但**不保证逐次确定**(后端配置 / `system_fingerprint` 可变 + 多请求 batch invariance;该 API 未提供 seed)。
> 输出差异来自**输入差异**或**采样**,而非模型自身随机。

### 5.2 逐条回答

1. **为何大概率相同、小概率不同**
   差异源自输入变化(H4)。lesson6 循环每轮将 `steps` 写入 prompt 并 +1,因此每轮输入不同。实验⑨(steps 0..9 递增)实测:10 轮得 9 个不同输出,证实 `steps` 变化确会驱动分叉;同时去除变化项后(实验 ①②③⑤)输出 100% 一致。合起来即"相同输入→相同输出、变化输入→分叉",非模型随机。

2. **去除 steps 等变化项后是否 100% 一致**
   本地:是(实测 38 次全同)。服务端:本次实测亦全同,但不保证逐次确定。

3. **提高调用次数是否改变结论**
   否。确定性映射与调用次数无关(实验 ③:30 次全同)。

4. **LLM 是否天生每次输出不同**
   否。模型本身为确定性计算;随机性来自采样:`temperature=0`(确定,实验⑦ logprobs 验证每步取 argmax)vs `temperature>0`(随机,实验 ④⑥)。常见对话产品默认 `temperature>0`。(此处指本地单请求 / 固定 batch;服务端另有 batch invariance 来源,见 §3.1 / §5.3。)

### 5.3 各解释的适用边界

- GPU 浮点非确定性、batch invariance 缺失:适用于**服务端多请求、CUDA、batch size 波动**场景(§3.1);其外在表现即 DeepSeek 响应中的 `system_fingerprint`(后端配置标识,会随后端变更)。
- 本地单请求、batch=1、Metal:上述因素不触发,实测为确定性。
- 即:H2(浮点 / batch invariance)描述的机制在服务端等环境真实存在,但不适用于本地单请求场景;H3(seed 使 temp=0 随机)在任何环境都不成立——greedy(argmax)不消费 RNG。

### 5.4 "两次运行脚本输出不同"的归因

`temperature=0` 推理确定,两次整体不同必然来自**两次 prompt 不同**(例如 i18n 改动、`system_prompt` / `instructions` 文本调整)。属输入差异,非模型随机。定位方式:diff 两次的 `system_prompt` 与 `agent_step` 的 `instructions`。

### 5.5 本地 vs 服务端对比

| 维度 | 本地(llama.cpp / Metal) | 服务端(DeepSeek API) |
|---|---|---|
| temp=0 确定性 | **实测确定**(黑盒,38 次全同;且 logprobs 验证每步取 argmax,即 greedy 行为) | **本次实测确定**(5 次全同),但不保证逐次确定(`system_fingerprint` 后端可变 + batch invariance) |
| 不确定来源 | 仅输入变化(本场景);batch invariance 不触发 | batch invariance / 后端变更(以 `system_fingerprint` 标识) |
| seed | 默认 -1(随机);greedy 下不影响输出(实验⑧) | API **未文档化 `seed`**;不确定性来自后端(`system_fingerprint`)/ batch invariance |
| temp>0 | 采样,实测全不同(④) | 采样,实测全不同(⑥) |

---

## 6 控制方法与速查表

### 6.1 强制可复现配置

```python
# 本地
Llama(model_path, seed=42, ...)
llm.generate(prompt, temperature=0.0)   # 兜底 n_gpu_layers=0（纯 CPU）
# 注：本仓 shared/llm.py 的 generate() 未透传 top_k；如需 top_k=1 强制 greedy，
#     须先在 generate() 的 kwargs 中接出 top_k，再传给生成调用 self.llm()（即 create_completion，非 Llama() 构造器），否则不生效

# 服务端（DeepSeek）：API 未提供 seed；temperature=0 也不保证逐次确定，
# 比对 system_fingerprint 判断后端是否变更（后端变即可能偏移）
```

### 6.2 速查表

| 问题 | 结论 |
|---|---|
| 同输入循环调用为何大多相同偶尔不同 | 输入随 `steps` 变化(H4),非随机 |
| 去除变化项是否 100% 一致 | 本地是(实测 38 次全同);服务端本次是、不保证逐次确定 |
| 提高次数是否改变 | 否,确定性与次数无关 |
| LLM 是否天生随机 | 否;随机来自采样(`temperature>0`);服务端另有 batch invariance(见 §5.3) |
| GPU 浮点 / 随机 seed 是否本地元凶 | 否(实测排除);属服务端多请求场景因素 |
| 服务端 temp=0 是否保证确定 | 否;后端(`system_fingerprint`)可变 + 多请求 batch invariance(该 API 无 seed) |
| 两次运行脚本结果不同 | 两次 prompt 不同(输入差异) |
| 方法论 | 推理栈行为随库版本/后端而异,结论以目标环境实测为准 |

---

## 7 信源

- [Thinking Machines — Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)(batch invariance;单请求前向确定)
- [llama.cpp #4458](https://github.com/ggml-org/llama.cpp/issues/4458) · [#2838](https://github.com/ggml-org/llama.cpp/issues/2838)
- [llama-cpp-python #972](https://github.com/abetlen/llama-cpp-python/issues/972) · [#890](https://github.com/abetlen/llama-cpp-python/issues/890) · [#1797](https://github.com/abetlen/llama-cpp-python/issues/1797) · [#1809](https://github.com/abetlen/llama-cpp-python/issues/1809)
- [DeepSeek 参数文档](https://api-docs.deepseek.com/quick_start/parameter_settings)(temperature 默认 1.0、按场景建议) · [DeepSeek Create Chat Completion API](https://api-docs.deepseek.com/api/create-chat-completion)(`system_fingerprint` = backend configuration;该页**无 seed 参数**)
- 实测数据:本地见 §4.1(temp=0 共 38 次全同),服务端见 §4.2(temp=0 ×5 全同 `a1f6439c0d`、temp=1.3 ×5 全不同,`fp_8b330d02d0_prod0820_fp8_kvcache_20260402`)。环境:Apple M4 Pro / Metal / qwen2.5-7b-instruct-abliterated.gguf;DeepSeek deepseek-chat。

---

## 8 概念脚注

[^greedy]: **greedy / argmax(贪心解码)**:每一步直接选概率最高的 token,不做随机采样;`temperature=0` 即对应此策略。参见 [Hugging Face — Generation strategies](https://huggingface.co/docs/transformers/generation_strategies)。

[^fp]: **浮点非结合性 / atomic add**:浮点加法不满足结合律,`(a+b)+c ≠ a+(b+c)`;GPU 并行归约(含 atomic add)顺序不固定,会引入末位级数值差异。参见 [Wikipedia — Floating-point arithmetic](https://en.wikipedia.org/wiki/Floating-point_arithmetic)。

[^batch]: **batch invariance(批不变性)**:同一输入的计算结果不随其所在 batch 的大小 / 组成而变;缺失时,云端把请求拼进不同大小的 batch 会使同一输入数值不同——是 LLM 推理服务非确定性的主因。参见 [Thinking Machines — Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)。

[^temp]: **temperature(采样温度)**:缩放 logits 分布的"锐度",`0` = 贪心(确定),越大越随机;DeepSeek 默认 1.0。参见 [DeepSeek 参数文档](https://api-docs.deepseek.com/quick_start/parameter_settings)。

[^sysfp]: **system_fingerprint**:API 响应字段,标识"模型运行所用的后端配置(the backend configuration that the model runs with)";后端变更则该指纹随之改变。参见 [DeepSeek Create Chat Completion API](https://api-docs.deepseek.com/api/create-chat-completion)。

[^logprobs]: **logprobs / logits**:logits 是模型对各候选 token 的原始打分,softmax 后得概率,logprob = log(概率);请求时开启 `logprobs` 可返回每步 top-N token 及其对数概率,用于核验模型实际选了哪个 token。参见 [OpenAI — Using logprobs](https://developers.openai.com/cookbook/examples/using_logprobs)。
