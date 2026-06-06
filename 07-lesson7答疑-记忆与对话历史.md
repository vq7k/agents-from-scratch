# lesson7 答疑：记忆与对话历史

> 本文沉淀学完 lesson7（memory）后的核心理解与 4 个问题：
> 1. 本节课到底要"理解"什么？（§1）
> 2. 记忆系统的代码长什么样、哪些方法本课真在用？（§2）
> 3. 这一版记忆有哪些局限、各自留给后续课什么？（§3）
> 4. 它和 lesson6 怎么接上？（§4）
>
> 主线：**记忆是对话历史的一种显式替代物**。要让 agent 跨多次交互记住东西，常见做法是把整段对话累积进 context；lesson7 不走这条路——它每次都发一个全新的一次性 prompt，把要记的事实抽成字符串存进一个独立 list，下次再注入。所以这一版 prompt 里没有对话历史，唯一跨轮的东西就是从记忆里取出、拼进指令的那段事实。
>
> 怎么读：只看结论翻文末「§5 速查表」；要原理读对应小节。
> 代码锚点：`agent/agent.py:443 run_with_memory` / `agent/agent.py:60 self.memory = Memory()` / `agent/memory.py Memory` / `complete_example.py:122 lesson_07_memory`。

---

## 0 主线

要让 agent 跨多次交互记住信息，有两条路把"上一轮的东西"带到下一轮：

```
路线 A（多数多轮 chatbot）：累积对话历史
  轮1  prompt = [system, user1, assistant1]
  轮2  prompt = [system, user1, assistant1, user2, assistant2]   ← 整段历史塞回 context，越滚越长
  轮3  prompt = [system, user1, assistant1, ... , user3]
  "记住" = 把所有原始对话原样喂回去，让模型自己从里面找。

路线 B（lesson7）：抽事实 + 独立存储 + 下次注入
  轮1  prompt = system + (指令 + 当前记忆 + user1)
       → 模型回 {"reply": ..., "save_to_memory": "用户的名字是小爱"}
                          └─ 存进 Memory.items（一个独立 list，在 prompt 之外）
  轮2  prompt = system + (指令 + 取出 Memory 全部 + user2)        ← 全新一次性 prompt，不含轮1原始对话
       "记住" = 把抽出来的事实存到 prompt 之外，下次再拼进去。
```

关键：lesson7 的 prompt 里**没有对话历史**，唯一跨轮的东西是从 `Memory` 取出、拼进指令的那段事实字符串（`agent/agent.py:455`、`:507`）。这是本课所有设计的出发点。

---

## 1 本节课的重点理解内容

### 1.1 三个新概念

| 概念 | 是什么 | 代码落点 |
|---|---|---|
| 上下文（Context） | 当前 prompt 里的内容，模型此刻能看到的一切 | `run_with_memory` 拼出的 `prompt`（agent.py:510） |
| 持久化（Persistence） | 把事实跨轮次存下来，下次还在 | `Memory.items` + `memory.add()`（memory.py:22） |
| 检索（Retrieval） | 需要时把相关记忆取出来 | 本课用 `memory.get_all()` 全量取出（memory.py:32） |

文档把这三者讲清了一件事：**模型不能直接访问记忆，它只能看到你放进 prompt 的内容**。记忆要起作用，必须先被取出来、拼进上下文。

### 1.2 主线命题：记忆替代了对话历史

`run_with_memory` 每次调用都从头拼一个 prompt（agent.py:510-514）：system 段是固定的 `self.system_prompt`，user 段是「指令 + 当前记忆 + 本次输入」。**前几轮的原始对话不在里面**。换句话说，这个 agent 根本不保留聊天记录。

跨轮唯一活下来的，是 `save_to_memory` 抽出来、存进 `Memory.items` 的那几条事实。下一轮 `get_all()` 把它们取出来重新注入（agent.py:455）。所以：

- 路线 A 让模型从原始对话里"自己记"——状态藏在 context 里，你看不见、改不了。
- 路线 B 把要记的东西抽成显式数据存在 prompt 之外——你能 `print(agent.memory.get_all())` 看、能手动改、能 `clear()`。

这正接上 lesson6 `state.py` 文件头那句设计原则：**状态不藏在对话历史里**。lesson6 把 `steps`/`done` 显式化，lesson7 把"该记住的事实"也显式化，是同一思路的延续。

### 1.3 "持久化"这个词在本课的实际范围

文档标题写「持久化」，但要清楚它指的范围：`Memory.items` 是一个**进程内的 Python list**（memory.py:20）。它持久的是**跨调用**——同一个 `agent` 对象多次调 `run_with_memory`，list 一直在。它**不**跨进程：程序一退出，list 就没了；重新 `python` 起来，记忆是空的。

真正落盘的持久化（写文件 / 写数据库，重启还在）本课没做。这不是 bug，是本课的范围划定——`Memory` 类注释里写了「未来：加入语义搜索、持久化等」（memory.py:14-15）。读文档时把「持久化」理解成「跨交互、跨这次进程的多轮调用」即可，别误以为已经落盘。

### 1.4 存什么由 LLM 自己决定

记忆里写进什么，不是代码规则定的，是模型在 `save_to_memory` 字段里自己填的（agent.py:522-523）：

```python
if parsed.get("save_to_memory"):
    self.memory.add(parsed["save_to_memory"])
```

好处是灵活——模型自己判断哪句话值得记。代价是这一步的可靠性取决于模型：它可能该记的没记、记错、或把一句话记成和原文不一致的措辞。本课用 `temperature=0.0`（agent.py:517）让同一输入的输出稳定，但这只压住随机性，并不保证抽取正确。而且一旦记错，这条错误事实会被注入之后**每一轮**的 prompt，本课除了整体 `clear()` 没有单条纠正或遗忘的机制。文档「让 agent 控制存储……显式控制能让行为更可预测」说的就是这个权衡。

---

## 2 记忆系统的代码结构

### 2.1 存储与使用是分开的两样东西

和 lesson6「状态机（`run_loop`）与状态数据（`AgentState`）分离」是同一种拆法：

- `Memory`（memory.py）：**存储**。只管存、取、查、清，不知道 agent 怎么用它。
- `run_with_memory`（agent.py:443）：**使用**。决定何时取记忆、怎么拼进 prompt、把模型回的哪个字段存回去。

`Agent.__init__` 里 `self.memory = Memory()`（agent.py:60），记忆挂在 agent 实例上，所以它跟着 agent 对象活着，跨多次 `run_with_memory` 调用持续存在——这就是 §1.3 说的"跨调用"。

### 2.2 Memory 有 5 个方法，本课只用到 2 个

| 方法 | 作用 | 本课用到？ |
|---|---|---|
| `add(item)` | 加一条，**带去重**（见 §2.3） | 用（agent.py:523） |
| `get_all()` | 取出全部（返回 copy） | 用（agent.py:455） |
| `get_recent(n=5)` | 取最近 n 条 | 预留未用 |
| `search(query)` | 子串匹配筛选 | 预留未用 |
| `clear()` | 清空 | 未用 |

`get_recent` / `search` 已经写好但 `run_with_memory` 没调用——和 lesson6 `AgentState` 里预留的 `current_plan`/`last_action` 一样，是上游为后续扩展先放着的方法。本课真正活跃的只有 `add` + `get_all`。

### 2.3 去重是字符串精确匹配

`add` 的去重在这一行（memory.py:29）：

```python
if item and item not in self.items:
    self.items.append(item)
```

`item not in self.items` 是**完全相等**的字符串比较。意味着"用户的名字是小爱"和"用户名字是小爱"会被当成两条不同记忆，都存下来。模型每轮措辞略有差别，同一件事就可能累积出多条。按语义判断"这俩说的是一回事"本课不做。

### 2.4 本课的"检索"就是取出全部

文档把「检索」立成一个新概念，但 `run_with_memory` 里的检索是最朴素的一种——`memory.get_all()`，不管本轮问的是什么，把记忆**全部**倒进 prompt（agent.py:455-461）。`search()` 这种按查询筛选的方法存在、但没接进主流程。文档自己也说明了："简单的检索可能就是「取出全部」。更复杂的检索则会根据当前查询找出相关的记忆。"本课用的是前者。

---

## 3 这一版记忆的局限，及各自留给后续课什么

文档「常见问题」里「记忆变得太大」那段，背后是三条相互独立的局限。把它们摊开，正好对应真实记忆系统要解决的三个方向：

| 局限 | 本课的现状 | 后果 | 真实系统的方向 |
|---|---|---|---|
| 写入不可靠 | 存什么由 LLM 填 `save_to_memory`（§1.4） | 漏存 / 错存 / 错误事实污染后续每轮 | 写入校验、可单条修正与遗忘 |
| 去重靠精确匹配 | 字符串完全相等才算重复（§2.3） | 同义不同措辞反复累积 | 语义去重、合并、摘要 |
| 全量注入 | `get_all` 不管问什么都全倒（§2.4） | 记忆越多 prompt 越长，迟早撑爆 context window | 按相关性检索，只取本轮需要的几条 |

第三条是最硬的约束：上下文窗口有限，而 `get_all` 随记忆无上限增长。这正是检索增强生成（RAG）/ 向量检索 / 摘要这一整类技术存在的原因——把"全量倒出"换成"按相关性取若干条"。本课故意先不碰它，留一个能跑的最小版（文档：「更复杂的检索可以放到后面，而这套基础已经能用了」）。延伸方向见附录 A。

---

## 4 和 lesson6 怎么接上

lesson6 答疑（`06a` §1.3）讲过：那一版的"连续性"很弱——`run_loop` 每步只把 `steps`/`done` 回灌进 prompt，**前几步的动作结果根本没回灌**，所以前几轮容易重复。当时就说了"把上一步结果喂回去 = lesson7 才补"。

lesson7 补的就是这个跨轮回灌，但走的是记忆这条显式通道，而不是把对话历史塞回去：

| | lesson6（agent loop） | lesson7（memory） |
|---|---|---|
| 跨轮带回什么 | 只有 `steps` / `done` 两个值 | 模型抽出的事实字符串 |
| 存在哪 | `AgentState`（状态容器） | `Memory.items`（记忆 list） |
| 活多久 | 一次 `run_loop` 内，循环结束 `reset()` 清掉 | 跨多次 `run_with_memory` 调用（同一进程） |
| 谁决定内容 | 框架（`increment_step`/`mark_done`） | LLM（`save_to_memory` 字段） |

一句话：lesson6 让状态跨**步**活着，lesson7 让事实跨**交互**活着；两者都是把该记的东西做成显式数据，而不是让模型从对话历史里自己捞。

---

## 5 速查表

| 问题 | 一句话结论 |
|---|---|
| 本课要 get 什么 | 记忆是对话历史的显式替代：抽事实存进独立 list，下次注入，prompt 里不留对话历史 |
| 记忆和上下文什么关系 | 模型只看得到 prompt；记忆必须先被取出、拼进上下文才起作用 |
| "持久化"持到哪 | 跨调用、跨本次进程的多轮调用；不跨进程，重启即空，未落盘 |
| 存什么谁决定 | LLM 填 `save_to_memory`；灵活但可能漏存/错存，错误会污染后续每轮 |
| 本课的检索 | `get_all` 全量倒出；`search`/`get_recent` 写了但没接进主流程 |
| 去重怎么做 | 字符串精确匹配，同义不同措辞会重复累积 |
| 最硬的局限 | 全量注入随记忆增长撑爆 context window —— 这是 RAG/向量检索存在的原因 |
| 和 lesson6 的关系 | lesson6 状态跨步、lesson7 事实跨交互；都是显式数据，不靠对话历史 |

---

## 附录 A：本课的 list ↔ 真实记忆系统（选读）

本课的 `Memory` 是最朴素的记忆后端：一个 list，写入靠 `append`，读取靠 `get_all` 全量倒出。真实系统在不改变"记忆 = prompt 之外的显式存储"这个骨干的前提下，主要替换其中两步：

- **读取**：把"全量倒出"换成"按相关性取若干条"。做法是给每条记忆算一个向量（embedding），用本轮查询的向量做相似度检索，只取最相关的几条注入。这样记忆库可以很大，但每轮注入的量受控。
- **写入**：加校验、去重（语义层面而非字符串）、摘要压缩，以及对错误记忆的修正与遗忘。

这一整套思路的代表是检索增强生成（Retrieval-Augmented Generation, RAG）：用非参数化的检索（外部记忆）补充参数化的生成（模型权重里的知识），论文明确把"知识可溯源、可检视、可更新"作为动机——和本课「记忆是可查看、可修改的显式数据」是同一主张，只是把全量注入换成了相似度检索。

信源：Patrick Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020。[NeurIPS 论文 PDF](https://proceedings.neurips.cc/paper_files/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf) · [dblp 收录](https://dblp.org/rec/conf/nips/LewisPPPKGKLYR020.html)

---

**核心要点：** 记忆 = 对话历史的显式替代。本课把"该记住的事实"抽成字符串、存进 prompt 之外的一个 list，下次再注入——你能看、能改、能清。它刻意停在最朴素的一版（全量取出、字符串去重、LLM 自填写入），把语义检索和落盘留给后续。
