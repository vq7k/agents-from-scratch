# ADR-0002 对话格式与结束符统一为 ChatML

> 状态：已采纳 · 来源：历史挖掘（脱敏）

## 决定
prompt 拼接统一 **ChatML**（`<|im_start|>` / `<|im_end|>`），废弃 Vicuna 风 `User:/Assistant:` 与 Llama-3 模板；**stop 用 `["<|im_end|>"]`**；对话格式与 stop **统一在 LocalLLM 封装层处理**。旧实现以**注释保留作对照**（标注风格来源），不删。

## 背景
`generate` 走 `create_completion`（文本补全）不自动套对话模板。Qwen2.5 训练用 ChatML，裸文本/Vicuna 格式下模型不识别 assistant 回合边界、不生成 `<|im_end|>`，导致设了 stop 仍不停、返回多句、跑到 `max_tokens`。这是反复纠正的核心技术点（见 `learned-rules` #1）。

## 备选
- 沿用 Vicuna/Llama-3 stop（`\n\n`/`User:`/`Assistant:`）→ 与 qwen 真身不匹配，弃用。
- 直接删旧实现 → 改为注释保留，便于教学对照不同模板风格。

## 影响
- stop 可靠触发，输出回合边界正确。
- lesson1-2 据此勘误并产出答疑笔记。
- 多行 prompt/schema 配合三引号重构（见 ADR-0004）。
