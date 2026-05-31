# 从零构建 AI Agent

一份温和、本地优先的 AI Agent 入门教程。

本仓库通过从一次本地 LLM 调用出发、一步步构建**一个 Agent**,来讲清 AI Agent 究竟是如何工作的。

**无框架。无云端 API。无隐藏的推理。无魔法。**


## 相关项目

### [从零构建 AI 产品](https://github.com/pguso/ai-product-from-scratch)

[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-339933?logo=node.js&logoColor=white)](https://nodejs.org/)

用本地 LLM 学习 AI 产品开发的基础。通过 10 节内容详尽、配有可视化图示的课程,覆盖 prompt 工程、结构化输出、多步推理、API 设计与前端集成。

### [用 JavaScript 从零构建 AI Agent](https://github.com/pguso/ai-agents-from-scratch) 

![Python](https://img.shields.io/badge/JavaScript-3776AB?logo=javascript&logoColor=yellow)

![Agent 架构](diagrams/agent-architecture.png)

## 理念

Agent 不是人格。它们是循环、状态和约束。

如果某个东西让你觉得像魔法,那就打开对应的文件看看——本仓库里没有任何隐藏的逻辑。

## 你将学到什么

本仓库用 12 节课构建一个持续演进的 Agent:

| 课程 | 新增能力 | 链接 |
|--------|------------------|------|
| 01 | 文本输入 / 文本输出 | [lessons/01_basic_llm_chat.md](lessons/01_basic_llm_chat.md) |
| 02 | 角色与行为(system prompt) | [lessons/02_system_prompt.md](lessons/02_system_prompt.md) |
| 03 | 结构化输出(JSON 契约) | [lessons/03_structured_output.md](lessons/03_structured_output.md) |
| 04 | 决策(路由逻辑) | [lessons/04_decision_making.md](lessons/04_decision_making.md) |
| 05 | 工具(外部能力) | [lessons/05_tools.md](lessons/05_tools.md) |
| 06 | agent loop(观察 → 决策 → 行动) | [lessons/06_agent_loop.md](lessons/06_agent_loop.md) |
| 07 | 记忆(短期与长期) | [lessons/07_memory.md](lessons/07_memory.md) |
| 08 | 规划(作为数据,而非思考) | [lessons/08_planning.md](lessons/08_planning.md) |
| 09 | 原子动作(安全执行) | [lessons/09_atomic_actions.md](lessons/09_atomic_actions.md) |
| 10 | AoT —— Atom of Thought(依赖图) | [lessons/10_atom_of_thought.md](lessons/10_atom_of_thought.md) |
| 11 | 评估(回归测试) | [lessons/11_evals.md](lessons/11_evals.md) |
| 12 | 遥测(运行时可观测性) | [lessons/12_telemetry.md](lessons/12_telemetry.md) |

## 适合谁阅读

**本仓库适合:**
- 会写代码、但面对 Agent 却无从下手的开发者
- 厌倦了「直接用 LangChain 就行」这种说法的人
- 想用本地模型的学习者
- 想要从机制层面理解 Agent 的工程师
- 想要一套清晰心智模型的教育者

**本仓库不适合:**
- 想要最快跑出 demo 的人
- 想要一套 SaaS 启动模板的人
- 相信 Agent 会「思考」的人
- 想要隐藏式思维链(chain-of-thought)的人

## 快速开始(Quick Start)

**详细的安装步骤请参见 [QUICKSTART.md](QUICKSTART.md)**

简而言之:
1. 安装依赖:`pip install -r requirements.txt`
2. 下载一个 GGUF 模型到 `models/` 文件夹
3. 运行:`python complete_example.py`

**注意:** `complete_example.py` 文件包含可执行的代码示例,演示了全部 12 节课的内容。你可以把它当作参考,看清所有概念是如何拼合到一起的。

## 仓库结构

```
ai-agents-from-scratch/
├─ README.md              # 你正在看的这个文件
├─ philosophy.md          # 本仓库存在的意义
├─ QUICKSTART.md          # 详细的安装指南
├─ complete_example.py    # 全部 12 节课的演示
├─ requirements.txt       # Python 依赖
│
├─ models/                # 把 GGUF 模型放在这里
├─ shared/                # 可复用的工具(LLM、prompt、各类辅助函数)
├─ agent/                 # 持续演进的 Agent 实现
│  ├─ agent.py             # 主 Agent 类 
│  ├─ memory.py            # 记忆系统
│  ├─ planner.py           # 规划与原子动作
│  ├─ state.py             # Agent 状态管理
│  ├─ tools.py             # 工具定义
│  ├─ evals.py             # 评估框架(第 11 课)
│  └─ telemetry.py         # 遥测系统(第 12 课)
├─ evals/                 # 用于测试的黄金数据集
│  └─ golden_datasets.py   # 已知正确的测试用例
└─ lessons/               # 逐步讲解(01-12)
```

### 关键文件说明

**`agent/agent.py`** —— 本仓库的核心
- 包含贯穿全部 12 节课不断演进的 `Agent` 类
- 每节课都在这同一个类上新增方法和能力
- 这是你在学习过程中需要研读和修改的对象

**`complete_example.py`** —— 学习参考
- 包含 12 个独立函数,每节课对应一个
- 每个函数都单独演示了该课的概念
- 用它在组合之前先看清每节课各自是如何工作的
- 运行:`python complete_example.py`

**`agent/evals.py`** —— 回归测试(第 11 课)
- 用已知正确的用例测试你的 Agent
- 在部署前捕捉 prompt 的回退退化

**`agent/telemetry.py`** —— 运行时可观测性(第 12 课)
- 用于调试的结构化日志
- 跟踪延迟、成功率和调用链路(trace)

**两者的关系:** 
- `agent/agent.py` = 你正在学习的代码(实现本身)
- `complete_example.py` = 每节课的独立示例(用于学习和实验)

## 本仓库不是什么

- 这**不是一个框架**
- 这**不是一个聊天机器人 demo**
- 它**不声称模型会思考**
- 它**不暴露思维链(chain-of-thought)**
- 它**不需要 OpenAI 或任何云端 API**

## 核心原则

1. **一个 Agent,多个阶段** —— 同一个 `agent.py` 文件随课程不断成长
2. **显式优于隐式** —— 没有隐藏逻辑,没有魔法般的抽象
3. **结构优于 prompt** —— 可靠性来自约束,而非巧妙的措辞
4. **本地优先** —— 没有 API key,没有速率限制,不依赖云端
5. **面向教学,而非生产** —— 这里教的是基本原理,不是生产环境的最佳实践

## 学习路径

每节课都建立在上一节之上。**不要跳着学。**

整套课程的设计目标是让理解逐步累积:
- 第 1-3 课:基础(LLM 基础)
- 第 4-6 课:能动性(决策、工具、循环)
- 第 7-10 课:智能(记忆、规划、执行)
- 第 11-12 课:可观测性(评估、遥测)

## 贡献

这是一个面向教学的仓库。贡献应当:
- 保持温和、循序渐进的学习风格
- 让代码保持可读,而非追求巧妙
- 增加讲解,而不只是增加功能
- 守住「无框架」的理念

## 许可证

MIT License —— 详见 LICENSE 文件

## 致谢

本仓库汲取了现代 Agent 开发的诸多最佳实践,同时刻意避开那些会妨碍理解的复杂性。

---

**如果你觉得本仓库有用,欢迎给它点个 star,并分享给其他正在学习 AI Agent 的人。**
