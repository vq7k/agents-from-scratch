# skill: catch-up

新 session 启动时怎么了解当前状态。

## 触发

任何新 session 启动（你刚被启动，不记得之前发生过什么）。

## 第一步：确认角色

看 cwd（当前工作目录），对照 `PROJECT.md` 的「cwd → 角色」表：

| cwd | 你的角色 |
|---|---|
| 仓库根 | 教程主理（当前唯一角色） |

> 单 agent 阶段仅此一角；未来按裂变阶梯（见 `.skill/init-agent-teams`）新增 Worker 时在此补行。

## 第二步：按当前位置读 CLAUDE.md

```bash
cat CLAUDE.md  # 自动指明必读链路
```

它会告诉你接着读哪些文件。

## 第三步：必读链路

1. `.agent/SOUL.md` — 你是谁
2. `.agent/STATUS.md` — 上一次 session 留下什么状态 + sessions/ 归档路径
3. 上一 session 归档（`.agent/sessions/<date>-<topic>/outputs.md`）— 上一次具体产出了什么
4. `.agent/TODO.md` — 下一步该做什么

## 第四步：自检 + **自报角色边界**（强制输出）

读完 SOUL.md 后**必须**显式 echo 一段（不许跳过）：

```
我是 <角色>（cwd = <path>）。
我**不做**：
1. <SOUL "我不做" 第 1 条 — 用谁来做替代>
2. <SOUL "我不做" 第 2 条 — 用谁来做替代>
3. <SOUL "我不做" 第 3 条>
4. ...
```

目的：把"内化"变成显式发声。未自报 = catch-up 未完成，**不可开干**。

再自检 3 问：
- 我知道我是谁、能改什么、不能改什么？（上面 echo 应已覆盖）
- 我知道上一次做了什么、产出在哪？
- 我知道下一步该做什么、依据是什么？

任何"不知道"→ catch up 不完整，回去补读文件，**不要直接开干**。

## 第五步：**判 STATUS actionable** + 开始工作 / 升级

读 STATUS.md 后**必须**回答：

> 当前 STATUS 是否含**明确 actionable 下一步**？（"当前阶段" / "下一步" 段是否说清现在要做什么 / 谁负责 / 入口）

- **有明确 actionable** → 按 TODO 开始
- **没有 actionable / STATUS 全是历史**（V0.x 闭环 / 各 milestone 完工…无当前任务）→ **强制升级 user 问 "现在该做什么"**，不允许自己推断或默认 "无任务 = 关 session"

判定标准：如果你需要"猜"或"推断"出下一步，那就是 STATUS 不够 actionable，必须升级。

## 第六步：开干

仅在第四步自报 + 第五步判 actionable 都通过后开干。

## 校验

能在 3 句话内回答："我是谁 / 上次做了什么 / 下一步做什么"。
