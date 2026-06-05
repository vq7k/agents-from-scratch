# ADR-0004 prompt 中文化策略

> 状态：已采纳 · 来源：历史挖掘（脱敏）

## 决定
prompt **全面中文化**，但**强约束保留英文原文**：stop/格式控制类、ChatML 标记（`<|im_start|>` 等）、结构化输出的 `choices`/选项标识等不译。多段 f-string 拼接**重构为 `textwrap.dedent` + 三引号块**提升可读性（lesson4-10 统一）。只做 i18n，**不改上游原始课程设计**。英文内容在文档中需附中文翻译。

## 背景
zh-cn 分支目标是中文化教学，但模型对格式/控制 token 敏感，乱译会破坏行为。多段字符串拼接可读性差。

## 备选
- 全译（含控制 token）→ 破坏 stop/解析，弃用。
- 保留多段 f-string → 改三引号块，更易读易维护。

## 影响
- 教学可读性提升，行为不变。
- `CRITICAL INSTRUCTIONS` 等需 prompt 文本多处同步对齐（见 `learned-rules` #5）。
