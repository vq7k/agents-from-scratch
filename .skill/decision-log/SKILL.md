# skill: decision-log

决策怎么落。

## 决策分层（决定写哪里）

| 决策类型 | 落地位置 |
|---|---|
| 改 spec 内任何条目（架构 / 技术栈 / 范围 / 协作框架） | spec 末尾 §12 Decision Log 追加一行 |
| 模块级决定（仅影响 `apps/<m>/`） | `apps/<m>/.agent/decisions/<YYYY-MM-DD>-<topic>.md` |
| session 级临时决定（不沉淀） | session 归档 `decisions.md` 即可 |

## 项目级 Decision Log（spec §12）一行格式

```
| # | YYYY-MM-DD | 涉及章节 | 旧版本概要 | 新版本概要 | 更迭原因 |
```

## 模块级 ADR 文件结构（精简版）

```markdown
# <编号>-<主题>

## 决定
[一句话]

## 背景
[为什么要决定]

## 备选与权衡
[考虑过哪些方案]

## 影响
[决定后哪些地方变]
```

## 步骤

1. 判断决策类型（看上表）
2. 写到对应位置
3. 改动相关文档（spec / SOUL / CLAUDE.md 等）
4. 一次 commit 把所有相关改动 + Decision Log/ADR 一起提交
5. commit message 引用 Decision Log 编号

## 反例

- ❌ 改了 spec 但不更新 §12 → 决策无追溯
- ❌ 模块级决定塞到 spec §12 → 污染项目级 log
- ❌ 写决定时不写"为什么" → 未来无法 audit

## 校验

`grep -c "^| [0-9]" docs/superpowers/specs/*.md` 应该单调增长。
