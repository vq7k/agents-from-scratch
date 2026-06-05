# STATUS

## 当前 actionable（catch-up 强制读这段判 ready 与否）
lesson6 已沉淀 3 篇笔记:`06a-lesson6答疑`(agent 循环与状态管理)/ `06b-实测`(temperature 与输出确定性)/ `06c-状态机`(状态机与订单流转)。**下一步候选、无 user 明示** → catch-up 见此**必须升级 user 确认走哪条**:①进 lesson7(memory,`lessons/07_memory.md` + `agent/agent.py:443 run_with_memory`);②收尾 lesson4-5 调试 print / demo 切换点;③定位 user 最初"两次跑脚本输出不同"(diff 两次 prompt,确认是输入差异)。

## 当前阶段
lesson 答疑笔记推进中:正文中文化已到 lesson10,答疑笔记已到 lesson6(含 1 篇确定性实测)/ 共 12 课,分支 zh-cn。

## 最近一次 session
2026-06-05 · lesson6 衍生「LLM 输出确定性」实测:从"输出大概率相同小概率不同"出发,对非确定性来源列 4 个候选假设(byte-identical/GPU浮点/随机seed/输入随steps变化)经调研+实测判定,联网调研 + 本机实测 4 组(temp=0 共 38 次全同、temp=0.8 ×8 全不同)+ 服务端实测(DeepSeek:temp=0 ×5 全同、temp=1.3 ×5 全不同,官方 best-effort 不保证),沉淀 `06b-实测-temperature与LLM输出确定性.md`。归档 `.agent/sessions/2026-06-05-lesson6-determinism/outputs.md`。
更早(同日):lesson6 agent 循环 + 状态机两篇答疑(`.agent/sessions/2026-06-05-lesson6-state-machine/`);`init-agent-teams` 治理层 commit `39f9405`(`.agent/sessions/2026-06-05-init-agent-teams/`)。

## 阻塞
无。

## 下一步（actionable 的展开 / 候选）
- 候选①:进 lesson7 memory —— `lessons/07_memory.md` + `agent/agent.py:443 run_with_memory`(lesson6 已点明「历史回灌在 lesson7 补」)
- 候选②:收尾 lesson4-5 调试 print / `complete_example.py` demo 切换点
- 候选③:diff 两次脚本,定位 user 最初"两次输出不同"的确切输入改动
- 皆需 user 拍板优先级

## 待提交（未 commit,user 未要求）
- 新增:`06a-lesson6答疑-*.md` / `06b-实测-temperature*.md` / `06c-状态机-*.md` 三篇 + 对应 sessions 归档
- 改动:`complete_example.py`(lesson_06 三行 print 已 i18n)+ user 在途 demo 切换
