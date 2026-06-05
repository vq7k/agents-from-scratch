# STATUS

## 当前 actionable（catch-up 强制读这段判 ready 与否）
lesson6 答疑已深化：06a §2 重写为「最小 FSM 状态机入门案例」（Mermaid flowchart 直角图 + 转移表 + 机与数据分离 + 与 06c 订单对照；去理论符号、五元组挪文末附录 A），已 commit `5d5094b` + push `origin/zh-cn`。**下一步无 user 明示** → catch-up 见此**必须升级 user 确认走哪条**：①进 lesson7 memory（`lessons/07_memory.md` + `agent/agent.py:443 run_with_memory`）；②收尾 lesson4-5 调试 print / demo 切换；③diff 两次脚本定位最初"输出不同"。另有 2 个本次小遗留待 user 拍（见「下一步」）。

## 当前阶段
lesson 答疑笔记推进中：正文中文化到 lesson10，答疑笔记到 lesson6（06a 已重写为 FSM 入门案例 / 06b 确定性实测 / 06c 订单状态机）/ 共 12 课，分支 zh-cn。

## 最近一次 session
2026-06-05 · lesson6 06a §2 重写为 FSM 状态机入门案例：辨析改正面入门案例，状态图三轮迭代定稿 Mermaid **flowchart**（查官方语法：`curve: step` 直角 + `nodeSpacing`/`rankSpacing` 拉开 + `LR` + 菱形 + 配色），去理论符号（δ/Q/Σ→工程措辞）、五元组挪文末附录 A（因 `<details>` 折叠在 user 渲染器不生效）；答疑 Python 状态机框架 / 自动机理论 vs SE 课程 / 理论 FSM vs Java 八股；全局记「图表默认 flowchart」规则；commit `5d5094b` push。归档 `.agent/sessions/2026-06-05-lesson6-06a-fsm-rewrite/`。

## 阻塞
无。

## 下一步（actionable 的展开 / 候选）
- 候选①：进 lesson7 memory —— `lessons/07_memory.md` + `agent/agent.py:443 run_with_memory`（lesson6 已点明历史回灌在 lesson7 补）
- 候选②：收尾 lesson4-5 调试 print / `complete_example.py` demo 切换点
- 候选③：diff 两次脚本，定位 user 最初"两次输出不同"的确切输入改动
- 本次小遗留（轻量，可顺带）：(a) 06a §2.1 ASCII 图删 / 留（现仍在不生效的 `<details>` 内）；(b) 是否把「少用 `<details>`、改文末附录 / 选读」补进全局图表规则
- 皆需 user 拍板优先级

## 待提交（未 commit，user 未要求）
- `shared/llm.py`：user 在途调试 print（`原始prompt` / `原始response` 两行注释），非主理改动，未碰。
