# skill: status-update

更新 `.agent/STATUS.md`。

## 何时用
完成一段工作后、session 结束前。让下一次 session 仅靠此文件 catch up。

## STATUS.md 字段（新建用 5 段；brownfield 保留既有命名亦可）
见 `templates/STATUS.template.md`。关键区分：
- **当前 actionable** = catch-up 后**立刻能开干**的下一步（必须明示，否则触发升级）
- **下一步** = actionable 的展开 / 多候选 / 长期路线（容许模糊）

## 步骤
1. 打开对应 `.agent/STATUS.md`
2. 替换上一次内容（**不堆历史**，历史在 `sessions/`）
3. 5 段全填（新建）；brownfield 保留既有命名亦可
4. commit message 写明更新原因

## 反例
- ❌ 「未启动」/「进行中」— 信息密度太低
- ❌ 长篇叙事 — STATUS 是状态快照不是日志
- ❌ 引用对话历史 — 下一 session 没有对话历史

## 校验
新建用本模板 = 5 段。`structure-check.sh` 不强求固定段名（宿主既有命名优先），只验「分段 ≥4 + 含 actionable readiness 锚点」。
