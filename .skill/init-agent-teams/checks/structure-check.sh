#!/usr/bin/env bash
# init-agent-teams check 模式 B1：结构完整性硬校验
# 用法：bash structure-check.sh <目标项目根>
set -uo pipefail
ROOT="${1:?用法: structure-check.sh <目标项目根>}"
cd "$ROOT" || { echo "FAIL: 无法进入 $ROOT"; exit 2; }

fail=0
chk() { # chk <描述> <test 命令...>
  if eval "${@:2}" >/dev/null 2>&1; then echo "PASS: $1"; else echo "FAIL: $1"; fail=1; fi
}

echo "== B2-1 结构完整性 =="
chk ".agent/SOUL.md 存在"   "test -f .agent/SOUL.md"
chk ".agent/STATUS.md 存在" "test -f .agent/STATUS.md"
chk ".agent/TODO.md 存在"   "test -f .agent/TODO.md"
chk "PROJECT.md 存在"       "test -f PROJECT.md"
chk "CLAUDE.md 存在"        "test -f CLAUDE.md"
chk "AGENTS.md 存在"        "test -f AGENTS.md"
chk ".skill/catch-up 存在"  "test -f .skill/catch-up/SKILL.md"
chk ".skill/status-update 存在" "test -f .skill/status-update/SKILL.md"
chk "CLAUDE.md → PROJECT.md 互指" "grep -q 'PROJECT.md' CLAUDE.md"
chk "PROJECT.md → SOUL/catch-up 互指" "grep -qE 'SOUL.md|catch-up' PROJECT.md"

echo "== B2-1 SOUL 四段齐 =="
chk "SOUL 含『我是谁』" "grep -q '## 我是谁' .agent/SOUL.md"
chk "SOUL 含『我不做』" "grep -q '## 我不做' .agent/SOUL.md"
chk "SOUL 含『我做』"   "grep -q '## 我做' .agent/SOUL.md"
chk "SOUL 含『我的边界』" "grep -q '## 我的边界' .agent/SOUL.md"

echo "== B2-2 STATUS 结构（不强求固定段名，宿主既有命名优先） =="
total=$(grep -cE '^## ' .agent/STATUS.md 2>/dev/null || echo 0)
chk "STATUS 分段 ≥4（实得 ${total}）" "test \"$total\" -ge 4"
chk "STATUS 含 catch-up readiness 锚点段" "grep -qiE '^## .*(actionable|当前|下一步|next|current|现在|now|todo)' .agent/STATUS.md"

echo "----"
if [ "$fail" -eq 0 ]; then echo "✅ structure-check 全 PASS"; else echo "❌ structure-check 有 FAIL（见上，按 SKILL.md B3 出待修复动作）"; fi
exit "$fail"
