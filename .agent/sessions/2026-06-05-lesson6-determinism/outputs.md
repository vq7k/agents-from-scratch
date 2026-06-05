# 2026-06-05 · lesson6 衍生:LLM 输出确定性实测

## 触发
user 跑 lesson6 `run_loop` 看到"输出大概率相同、小概率不同",连续追问:为什么?LLM 不是该随机吗?没有 steps 会 100% 一致吗?调高次数呢?→ 要求整理成一篇文档。

## 做了什么
- **读实现**:`agent/agent.py:378/400/406`(steps 进 prompt + temp=0 + 每轮 increment)、`shared/llm.py:44`(Llama 无 seed,默认 -1 随机)、`:31`(Metal `n_gpu_layers=-1`)。
- **候选假设判定**:对非确定性来源列 4 个候选(H1 byte-identical / H2 GPU 浮点 / H3 随机 seed / H4 输入随 steps 变化),经调研与实测逐一判定(H1/H4 成立,H2/H3 本机不成立)。
- **联网调研**:Thinking Machines(batch invariance 才是云端非确定性主因,单请求前向确定,推翻浮点说)、Metal 确定性、llama.cpp/llama-cpp-python issues(seed/采样链/版本坑)。
- **本机实测 4 组**:
  - ① 同进程 temp=0 ×5 → 全同 `65434c749a`
  - ② 跨进程 temp=0 ×3 → 全同
  - ③ 高次数 temp=0 ×30 → 全同(1 个版本)
  - ④ 对照 temp=0.8 ×8 → 8 个全不同
  - 合计:temp=0 共 38 次 bitwise 全同;temp>0 立刻多样。
- **服务端实测(DeepSeek deepseek-chat,OpenAI 兼容)**:temp=0 ×5 全同(`a1f6439c0d`)、temp=1.3 ×5 全不同;`system_fingerprint` 5+5 次一致(同后端)。DeepSeek 文档:默认 temp=1.0、编码建议 0.0、seed(Beta);seed/temp=0 为 **best-effort、不保证确定**。
- **安全**:user 在对话明文贴了 DeepSeek API key,仅内存使用、未写入任何文件;已提示轮换。

## 结论
本机 temp=0 = 确定函数;所有"不同"来自输入不同(循环里是 `steps`);GPU 浮点/随机 seed 在本机不成立(是云端 serving 的问题,被我张冠李戴)。随机性只在 `temp>0`(开采样)出现。

## 产出
- `06b-实测-temperature与LLM输出确定性.md`(问题→纠错→调研→实测→准确回答,全留痕)

## 遗留
- user 最初"两次跑脚本不同"未最终定位:既然推理确定,必是两次 prompt 不同(i18n/system_prompt/instructions 改动),可 diff 坐实(未做)。
- `complete_example.py` 仍有 user 在途改动 + 本会话已 i18n lesson_06 的三行 print。
- 未 commit(user 未要求)。
