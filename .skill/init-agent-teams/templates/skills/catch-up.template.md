# skill: catch-up

新 session 启动时怎么了解当前状态。

## 触发
任何新 session 启动（你刚被启动，不记得之前发生过什么）。

## 第一步：确认角色
看 cwd → 对照 `PROJECT.md` 的「cwd → 角色」表。

## 第二步：读 CLAUDE.md
`cat CLAUDE.md` — 它指明接着读哪些文件。

## 第三步：必读链路
1. `.agent/SOUL.md` — 你是谁
2. `.agent/STATUS.md` — 上次留下的状态 + sessions/ 归档路径
3. 上一 session 归档 `.agent/sessions/<date>-<topic>/outputs.md`（如有）
4. `.agent/TODO.md` — 下一步

## 第四步：自检 + 自报角色边界（强制输出）
读完 SOUL 后**必须** echo：
```
我是 <角色>（cwd = <path>）。我不做：1.<…> 2.<…> …
```
未自报 = catch-up 未完成，**不可开干**。

## 第五步：判 STATUS actionable
- 有明确 actionable → 按 TODO 开干
- 无 actionable / 全是历史 → **强制升级 user 问「现在该做什么」**，不许自己推断或默认关 session

## 校验
能 3 句话回答：「我是谁 / 上次做了什么 / 下一步做什么」。
