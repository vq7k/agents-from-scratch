# STATUS

## 当前 actionable（catch-up 强制读这段判 ready 与否）
新增一篇 1–10 横向串讲 `lessons横向串讲-从映射看1-10.md`（**未 commit**）：经多轮对话把"从映射看 1–10"的逻辑聊透后落笔，六节因果链（总论·映射命题 → §1 机制/三处可变项 → §2 能动性递进 → §3 可靠性边界 → §4 建映射vs守映射 → §5 用1–10搭学习版最小Agent四步 → §6 接业界坐标）。已请 user 审三处替他拍板的点（§5 边界线力度 / §6 memory engineering 定性 / §3 名实落差直白度）。**下一步无 user 明示** → catch-up 见此**必须升级 user 确认走哪条**：①按 user 审阅反馈改这篇串讲；②commit（串讲 + 07–10 答疑 + 早先在途 complete_example.py/shared/llm.py，范围需 user 拍）；③写 lesson11/12 答疑（`agent/evals.py` / `agent/telemetry.py`）。

## 当前阶段
lesson 答疑笔记 + 横向串讲推进中：答疑覆盖 lesson1–10（余 11/12），另有 1 篇 1–10 横向串讲已成稿 / 共 12 课，分支 zh-cn。

## 最近一次 session
2026-06-06 续 · 横向串讲。这一段是长对话推演，逐步立起贯穿主线：**Agent 工程 = 在「不可信 LLM 输出」和「真实业务/执行」间建一层受约束(schema)+可校验(校验)+接回动作(校验后动作)的映射；1–10 共享同骨架只在这三处可变项不同**。期间被 user 校正两处并已吸收：(a) 措辞禁比喻——"旋钮/拧法"等作废，统一用"三处可变项"；(b) 修正"11/12 守映射无条件必须"为"可选、要走出学习阶段才需要"，§5 实践明确按学习项目（非生产）设计、不上工程配套，呼应 PHILOSOPHY 反过度工程。§6 业界方法论成熟度已联网核实给信源（context engineering 2025年中才 settled，Lütke/Karpathy/Anthropic）。本篇未单独归档 sessions 目录。

## 阻塞
无。

## 下一步（actionable 的展开 / 候选）
- 候选①：按 user 审阅反馈改横向串讲（重点 §3/§5/§6 三处）
- 候选②：commit 本批产物（横向串讲 + 07/08/09/10 答疑；是否带 complete_example.py/shared/llm.py 待 user 拍）
- 候选③：lesson11 答疑 —— evals，`lessons/11_evals.md` + `agent/evals.py`
- 候选④：lesson12 答疑 —— telemetry，`lessons/12_telemetry.md` + `agent/telemetry.py`（`agent_telemetry.jsonl` 现为空文件）
- 旧遗留（06a）：(a) §2.1 ASCII 图删/留；(b) 全局图表规则补「少用 `<details>`」
- 皆需 user 拍板优先级

## 待提交（未 commit，user 未要求）
- `lessons横向串讲-从映射看1-10.md`：本次新增（untracked）。
- `07-…记忆与对话历史.md` / `08-…规划即数据生成.md` / `09-…原子动作.md` / `10-…AoT依赖图.md`：前序新增（untracked）。
- `complete_example.py` / `shared/llm.py`：早先在途改动（M），user 调试 print 等，非本系列主理改动，未碰。
