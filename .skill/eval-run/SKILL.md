# skill: eval-run

跑一次 `.eval/` 系统验证。按业界 minimal viable eval 标准。

## 何时用

- spec 关键改动后
- 新 runtime 引入后
- 怀疑 SOP 失效时

## 设计原则（不可违反）

1. **判分者跨 family**：判 Claude 用 Codex / Gemini；判 Codex 用 Claude。**绝对不**自评。
2. **Rubric 隐藏**：agent prompt **只含任务**，不含"应该这样做"/"考点是 X"。Rubric 仅 judge 可见。
3. **Negative case 必有**：故意做错的 trace，judge 必须能打死。无 negative 的 eval 是单边的。
4. **Pass^3**：同 case 跑 3 次，全过才算过。报 pass^3 + pass@1。
5. **Programmatic check 优先**：能 `grep` / `diff` / `test -f` 的，绝不用 LLM judge。

## 步骤

### 0. Prefer V3 suite entrypoints when available

For V3 suites, start with:

```bash
bash .eval/harness/run-suite.sh <suite-id> --dry-run
# example: bash .eval/harness/run-suite.sh full-pass3 --dry-run
```

Use the dry-run output to verify case count, trial count, checks, and judge policy before starting expensive agent/judge work.

When transcripts already exist, run deterministic checks through the V3 harness:

```bash
bash .eval/harness/run-suite.sh <suite-id> --programmatic-only <run-id> <trial-root>
# <trial-root>/<case-id>/trial-<n>.md
```

This copies transcripts into `.eval/runs/<run-id>/`, writes `SUMMARY.md` and
`programmatic-checks.md`, and stops before LLM judge.

Legacy V2 manual flow below remains valid for cases not migrated to `.eval/cases/` yet.

### 1. 选 scenarios

从 `.eval/scenarios/{normal,boundary,negative}/` 选当前要验证的（不要全跑，按 trigger 选）。

### 2. 准备 rubrics

每个 scenario 对应 `.eval/rubrics/<scenario-name>-rubric.md`。**rubric 不进 agent prompt**。

### 3. 跑 agent (n=3)

每个 scenario 跑 3 次（不同 SubAgent / Codex session 实例）。Agent prompt 只含 scenario 的 `input`，**不含考点 / rubric**。

### 4. Programmatic checks 先跑

对每个 trial 跑 `.eval/tools/*.sh` 校验文件 / state。能 fail 的 trial **不需要 LLM judge**，直接 fail。

### 5. LLM judge 兜底

剩余 trial 用 **PI 跨 family judge**（详见 `.tool/runtimes/pi.md`）：

```bash
bash .eval/tools/run-judge.sh <trial> <rubric> <run-dir>
# 默认 provider=google (Gemini)，env JUDGE_PROVIDER 覆盖
```

跨 family 原则：
- 判 Claude 输出 → `JUDGE_PROVIDER=google` 或 `openai`
- 判 OpenAI 输出 → `JUDGE_PROVIDER=anthropic` 或 `google`
- 判 Gemini 输出 → `JUDGE_PROVIDER=anthropic` 或 `openai`

Judge prompt 含 rubric + trial transcript，不告诉 judge 这是 self-test。Judge 输出多维离散分（每维 0/1/2）+ pass/fail + 结构化 marker（`=== SCORE: N/M ===` + `=== VERDICT: PASS|FAIL ===`）。

### 6. 综合 + 归档

`.eval/runs/<YYYY-MM-DD>-<topic>/` 含：

```
trial-N.md         # 每次跑的 agent transcript
judge-report.md    # judge 评分汇总（pass^3 / 各 case 分布）
findings.md        # 综合发现 + 改进项
*.html             # render-html.sh 生成（gitignored），本地浏览器看
```

`run-judge.sh` 跑完自动调 `render-html.sh --run-dir <run-dir>` 把整个 run 的 `*.md` 全渲染为 `*.html`（要求 `pandoc`，`brew install pandoc`）。手动渲染单文件：

```bash
bash .eval/tools/render-html.sh <md-file>          # 单文件
bash .eval/tools/render-html.sh --run-dir <dir>    # 整个 run dir
```

## 反例

- ❌ Self-judge（agent 评自己）→ self-enhancement bias 全套
- ❌ Rubric 进 agent prompt → 考点暴露 gameable
- ❌ 只跑正常 case → 单边 eval，无法证伪
- ❌ pass@1 报"通过"→ τ-bench 数据：单次成功不可靠
- ❌ 编造 trials → `.skill/learned-rules` 反例同款
- ❌ Trial 保留 sanitization 元注释（如 "原 trial 含 sensitive-word"）→ judge 会把 meta-info 当 leak 证据误判（实证：`runs/2026-05-27-pi-full` trial-2 6/8 FAIL，清掉注释 + 改 placeholder 后 8/8 PASS）。**若 trial 需脱敏，完全重写涉敏段，不留 meta-info**

## 校验

- `ls .eval/runs/<date>-<topic>/findings.md` 存在
- `findings.md` 含 pass^3 数字 + pass@1 数字 + judge transcript 引用
- judge 不是同 family 的 LLM

## 回归触发场景（合并自 .skill/regression-eval/）

PROJECT.md / 根 SOUL.md / spec §0-§7 改动后必跑 full-pass3 regression：
- **触发条件**：架构级 change（新角色 / 新模块 / 边界调整 / SOP 大改）
- **跑法**：`bash .eval/tools/run-judge.sh full-pass3 <date>-<topic>-regression`（如 LLM judge 端到端 12-72 min，可先跑 programmatic-only 子集 24 trial 验底线）
- **DoD**：≥ baseline pass^3（如 5/8 / 24 trial 综合 PASS）
- **沉淀**：写 `.eval/runs/<date>-<topic>/SUMMARY.md` 含 baseline 对比

历史参考：[`/.eval/runs/2026-05-28-opus-bootstrap-regression/`](../../.eval/runs/2026-05-28-opus-bootstrap-regression/) — opus bootstrap T1-T12 后跑（24/24 programmatic PASS / baseline 改善）。
