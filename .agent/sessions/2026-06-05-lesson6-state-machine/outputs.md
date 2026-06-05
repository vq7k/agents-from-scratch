# 2026-06-05 · lesson6 agent 循环 + 状态机答疑笔记

## 触发
user 启动 lesson6 → 读文档找重点 → 追问 `AgentState` 是不是状态机 / 状态机是什么怎么应用 / 订单状态机设计方案 → "沉淀"。

## 做了什么
- 读 `lessons/06_agent_loop.md`，对照 `agent/agent.py:340 agent_step` / `:411 run_loop` + `agent/state.py`，确认**文档与实现完全一致**（ChatML 当前启用，旧 Vicuna 版以注释保留对照）。
- 提炼本课重点：Agent = 循环 + 状态；关键洞见「这一版连续性刻意很弱」（每步喂同一 input，状态只回灌 steps/done，temp=0 → 重复正常，历史回灌留到 lesson7）。
- 讲清 `AgentState` **不是 FSM 而是显式状态容器**；那台两态机在 `run_loop`（机与数据分离）。
- 联网交叉验证：FSM 理论（五元组 / McCulloch-Pitts·Mealy·Moore·Kleene 起源 / turnstile / TCP RFC 9293 / LangGraph StateGraph）+ 订单状态机工程实践（幂等 / 乐观锁 CAS / 延迟消息超时 / 退款子状态机 / Saga 补偿 / 选型）——全部附信源。

## 产出
- `06a-lesson6答疑-agent循环与状态管理.md`（本课重点 + AgentState 状态管理）
- `06c-状态机-从概念到订单流转设计.md`（FSM 概念→应用→电商订单状态机完整设计方案 + 信源）

## 遗留
- `complete_example.py` 仍有 user 在途改动（demo 已切到 `lesson_06_agent_loop()`，未碰，保持未暂存）。
- 答疑笔记进度：正文中文化已到 lesson10，答疑笔记现到 lesson6 / 共 12 课。
- 未 commit（user 未要求）。
