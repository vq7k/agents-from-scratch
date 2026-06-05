# worker-review — Worker 交付独立 review

## 何时调用

- Worker 自报"完成" 前
- Worker push 分支 / 合 main 前
- 主 session 看到大块 Worker diff 需要独立信号时

## 核心原则（5 条，全部不可省）

1. **跨 family judge**：被测 Worker 是 Claude → judge 用 PI Agent (default underlying = openai-codex)。**绝不同 family 评同 family**（self-enhancement bias，参考 .eval/ Decision Log #11）
2. **Rubric 隐藏**：Worker 写 diff 时**绝不能见 rubric**，rubric 仅 judge prompt 内出现
3. **独立 session**：主 Orchestrator session **不评**，必须派 PI 独立 tmux session
4. **Hard gate 先跑**：leak / cross-module write 等确定性检查先跑（FP ≈ 0），通过的再上 LLM judge
5. **结构化 marker**：judge 输出强制 `=== SCORE / === VERDICT / === ISSUES`，便于 machine 解析

## SOP

### 1. 收集 diff

**⚠️ 关键：必须用 milestone-start 起点（不是单 commit 增量），否则 PI 看不到完整上下文。**

实证：2026-05-28 web smoke-skill review，v3/v4 用 `git show <smoke commit>` 只含 smoke 4 个 commit → PI 看不到 V0.2 工作台壳 TabBar/ToolTabBar 源码 → 误判 reuse-first=2；v5 改 `git diff <V0.2 起点>~1..HEAD` 后立刻抓到 100 行造轮子。

按 Worker 类型选 base / head：

```bash
# A. 已 commit + 跨多 task（推荐：milestone 完结时用）
MILESTONE_START=<v0.2-T1-commit-sha>          # 当前 milestone 第一个 commit
git diff ${MILESTONE_START}~1..HEAD -- apps/<m> > <run-dir>/<worker>-diff.md

# B. 已 commit + 单 task（只 review 单 commit 时用，知道范围窄）
git show <commit-sha> > <run-dir>/<worker>-diff.md

# C. 未 commit working tree（如 Biz/AI Worker 还没 commit）
git diff HEAD > <run-dir>/<worker>-diff.md
git status --short | awk '/^\?\?/{print $2}' | xargs -I{} sh -c 'echo "=== NEW FILE: {} ==="; cat {}' >> <run-dir>/<worker>-diff.md
```

**评 rubric v2 维度 5（reuse-first）必须 append 上下文**，否则 PI 不知道项目装了什么：

```bash
cat >> <run-dir>/<worker>-diff.md <<EOF

---

## Context for rubric v2 reuse-first

### package.json
\`\`\`json
$(cat apps/<m>/package.json)
\`\`\`

### components/ui/（shadcn 已装清单，若 web）
$(ls apps/<m>/components/ui/ 2>/dev/null)

### 第三方库 root exports（按需，如 @base-ui/react）
$(node -e "console.log(Object.keys(require('@base-ui/react')).join('\n'))" 2>/dev/null)
EOF
```

### 2. Hard gate 检查（按 Worker 类型）

```bash
# 所有 Worker
bash .eval/tools/check-no-leaks.sh <run-dir>/<worker>-diff.md

# Worker 是 web/biz/ai → 检查跨模块
bash .eval/tools/check-no-cross-write.sh <run-dir>/<worker>-diff.md <module>
```

任一 FAIL → 直接拒绝，无需 LLM judge。

### 3. 派 PI judge

```bash
bash .eval/tools/run-pr-judge.sh \
  <run-dir>/<worker>-diff.md \
  .eval/rubrics/pr-review-rubric.md \
  <run-dir> \
  <worker>
```

观察：`tmux attach -t eval-pr-judge-<worker>-<TS>` 或 `tail -f <run-dir>/pr-judge-<worker>.log`，等 `=== DONE ===`。

### 4. 解析结果

```bash
grep -E '=== SCORE|=== VERDICT|=== ISSUES' <run-dir>/pr-judge-<worker>.log
```

### 5. 决策路径

- **PASS** →
  1. commit run dir 证据：`git commit -- <run-dir>/<worker>-diff.md <run-dir>/pr-judge-<worker>.log -m "test(eval): <worker> worker-review N/8 PASS"`（HTML 已 .gitignore）
  2. 报 user 准备 merge（user 拍板 merge 时机）
- **FAIL** → 把 ISSUES 列表给 Worker，让 Worker 修，修完重跑步骤 1-4
- **judge timeout / 异常** → 看 log，调 timeout 重跑（默认 180s）
- **judge log 无 SCORE marker（PI 空跑）** → `run-pr-judge.sh` 内置 1 次 auto-retry；仍无 → log 标 `=== ERROR: retry also produced no SCORE ===`，**视为机制故障**而非 Worker FAIL，需人工排查（看 prompt 大小 / PI rate limit / tmux pane 实时输出）

## 多 Worker 并行 review

3 个 Worker 同时 review 时，启 3 个独立 tmux session（每个 LABEL 不同 → LOG_FILE 不撞）：

```bash
for w in web biz ai; do
  bash .eval/tools/run-pr-judge.sh runs/<run>/${w}-diff.md \
    .eval/rubrics/pr-review-rubric.md runs/<run> ${w}
done
# wait until all 3 logs 含 === DONE ===
```

## 反例

- ❌ 主 session 自评 Worker diff → self-enhancement bias
- ❌ Rubric 提前给 Worker → gameable
- ❌ Worker 自报 PASS 直接合 → 无独立信号
- ❌ 跳 hard gate 直接 LLM judge → 错过确定性问题（leak / 跨模块）
- ❌ 没 SCORE/VERDICT marker → 无法 machine 解析，每次手动看 log

## 与其它 skill / tool 的关系

- `.eval/tools/run-pr-judge.sh` — judge 主力
- `.eval/rubrics/pr-review-rubric.md` — 唯一 rubric
- `.eval/tools/check-no-leaks.sh` / `check-no-cross-write.sh` / `check-no-app-code-write.sh` — hard gate
- `.tool/runtimes/pi.md` — PI Agent 配置参考
- `.skill/eval-run/SKILL.md` — 跑 eval 流程参考（pass^3 / cross-family / programmatic check）
