# skill: init-agent-teams

> version: v0.2.2 · status: 成长中（持续修复，非累加）
> ⚠️ 本 SOP 仍在迭代。**用前先读 §已知问题；用后必按 §回写闭环 回写。**

把一套验证过的「多 Agent 协作骨架」装到**已存在的项目**里（init），并按需体检（check）。
**自包含**：所有模板在 `templates/`，离线可抄，不依赖来源仓库。

## 何时用
- **init**：一个已在跑的项目想要 Agent teams 治理层
- **check**：init 后验收，或 human 想给现有 Agent teams 体检

## 不做（边界）
- ❌ 空项目 scaffold（只做 brownfield 嵌入）
- ❌ 自动巡检 / 主动提醒（**监控归 human**）
- ❌ 碰业务代码 / 覆盖目标项目原有文件

---

## 模式 A：init（初始化）

> 信条：**没有可分工的活就不该有子 Agent**。默认产出是**单 agent**，角色按需长（§裂变阶梯）。

### A1 静态侦察
读目标项目：`README` · 包清单（`package.json`/`pom.xml`/`pyproject.toml`…）· 目录结构 · **已有的 `CLAUDE.md`/`AGENTS.md`**。得一份初步「项目画像」骨架。

### A2 runtime 历史对话挖掘
按 [`history-mining.md`](./history-mining.md) 加载分析 Claude Code/Codex 历史 → 项目真实画像 + 决策 + 踩坑 + 当前状态（**已脱敏**）。
**无历史** → 跳过，仅用 A1。

### A3 角色裁剪（默认单 agent，human 拍板）
按 §裂变阶梯，结合 A1+A2 证据。**默认单 agent 起步**；仅当静态 + 历史共同显示已有多个成熟独立模块才裂 Worker。三问 human：
1. 有几个能独立迭代/部署的模块？→ Worker 数（可为 0）
2. 有没有独立运维面（Docker/CI/服务器）？→ 要不要 infra 顶层
3. 视觉品位是核心卖点吗？→ 要不要 design Worker

### A4 嵌入骨架（不覆盖原有）
按裁剪结果从 `templates/` 取模板，**填 A1+A2 真实画像**（真模块名/栈/续接状态，不留占位符），落地目标项目：
- Core 必产：`.agent/{SOUL,STATUS,TODO}.md` + `PROJECT.md` + `CLAUDE.md`+`AGENTS.md` + `.skill/{catch-up,status-update}/SKILL.md`
- 已有 `CLAUDE.md` → **追加**指向 PROJECT.md 的链路，**不覆盖**；冲突项标出让 human 裁
- 已有 `catch-up`/`status-update` 等**同族脚手架**（旧 init / 模板遗留）→ **不整体覆盖**：保留更完整者，仅**定点修**与真实结构冲突的项（如角色表写 `Orchestrator`/`apps/<m>` 但宿主无此结构），冲突标出让 human 裁
- 绝不动业务代码、不删原有文件

### A5 产出清单 + 提示 Optional
列已产 Core + 可按需加挂的 Optional（裂变后的 `delegate-worker`/`worker-summary`、`.eval/`、隐私五层、由历史提炼的 `decisions`/`learned-rules`…），交 human 决定何时加。

### 裂变阶梯（A3 依据）
| 档 | 何时 | 建什么 |
|---|---|---|
| ① 单 agent（默认） | 没有可分工的活 | 一个 agent 包圆，`.agent/` 自交接 |
| ② 临时 SubAgent | 有独立活但**一次性** | 开 SubAgent 跑完即弃，**不立角色** |
| ③ 常驻 Worker | 一块活是**持续迭代领域**（独立栈/文件域） | 建它的 `.agent/` + 写 SOUL + 纳入派活/汇报 |

**①→③ 四判据**（够才裂）：边界清晰（能独立验收）· 会反复（非一次修）· 上下文该隔离（栈/文件域分开）· 值得并行。不够 → 留 ① 或走 ②。

---

## 模式 B：check（自检，human 发起）

> check 是**给 human 的体检仪**：agent 只递报告，**裁决在 human**。

### B1 程序化硬校验
`bash <此 skill>/checks/structure-check.sh <目标项目根>` → 结构完整性硬检查（文件存在 / 互指对 / 段齐）。

### B2 健康判据五组（单一来源，init 也按它搭）
1. **结构完整性**：`.agent/` 三件套在 · 三入口在且**互指对**（CLAUDE/AGENTS→PROJECT→SOUL）· SOUL 四段齐。
2. **自洽性**：角色边界**无重叠、无真空**（每职责唯一 owner）· catch-up 能 3 句话答「我是谁/上次/下一步」· STATUS 分段合理（≥4 段 + 含 actionable 锚点，宿主既有命名优先）。
3. **brownfield 兼容**：不与原有 `CLAUDE.md`/约定冲突 · 没覆盖/删原有文件。
4. **裂变 & 分层**（出报告给 human，**不自动改**）：单 agent 上是否堆 ≥2 块独立并行活（**该裂变**）· 已建 Worker 是否真有持续领域（**过度裂变**）· 规模 vs 已挂设施是否匹配（多 Worker 却无 decision-log = 缺口）。
5. **成长型**：本地快照 `version` vs 母版 · 已知问题是否积压未清。

### B3 出体检报告
每条 pass/fail + **不过项修法**；fail → **待修复动作，修完即清**（非累加）。第 4 组裂变/分层仅作**建议**呈现，human 裁。

---

## 成长型自进化

### 回写闭环（用完必做）
```
用 SOP 搭完/体检完 → 自检"哪步卡了/哪个模板别扭/哪条判据模糊"
   → 修进下方 §演进记录 / §已知问题 → bump version
   → 下个使用者进来先读到 → 避坑 / 接着改进
```
**持续修复非累加**：§已知问题是**待清零队列**（修进 changelog），不是越堆越长的告警墙。理想态：经常是空的。

### 母版 vs 快照
本文件是**母版**（single source）；带到新项目的是某 `version` 的**快照**。check B2 第 5 组据此比对「是否落后 / 有无新增已知问题」——提醒是 use-time、给 human 读，**非 agent 主动弹**。

## 演进记录（changelog）
- **v0.1（2026-06-04）** 初版：init/check 两阶段 + 历史挖掘 + 自包含模板 + 裂变阶梯 + 成长型。
- **dry-run（2026-06-04）** 跨样例项目只读验证 A1 侦察 + A2 历史 map（脱敏）走通；暴露 structure-check 的 STATUS 段校验对 brownfield 宿主命名过严，记入下方 §已知问题（见 `dry-run.md`）。
- **v0.2（2026-06-04）** 修复上述：structure-check B2-2 STATUS 校验改为「分段 ≥4 + 含 actionable readiness 锚点（不强求固定段名）」，status-update / B2 措辞同步软化；母仓自身 self-check 由 14/15 → 全 PASS。已知问题清零。
- **v0.2.1（2026-06-04）** 首个真实项目实战落地（brownfield 单 agent 内容仓，替换已废弃的 `.agent-teams/` 遗留路由）。修复 structure-check B2-2 在 macOS bash 3.2 + `set -u` 下报 `total: unbound variable`：根因是 v0.2 新增的描述串 `（实得 $total）` 里 `$total` 紧邻全角括号 `）`，老 bash 把 `）` 的高位字节并入变量名 → 改 `${total}` 花括号定界。实战目标项目复测全 PASS / exit=0。已知问题清零。
- **v0.2.2（2026-06-05）** 第二次实战落地（brownfield 单 agent 教学仓 `agents-from-scratch`，含丰富 Claude Code+Codex 历史，map-reduce 6 个 miner 走通）。暴露 A4 盲区：宿主**已存在同族但更旧/泛化的 `catch-up`/`status-update` 脚手架**，其角色表写 `Orchestrator`/`apps/<m>` 而宿主无此结构 —— 旧 SOP 只规定了「已有 CLAUDE.md→追加不覆盖」，未覆盖「已有 skill 脚手架冲突」。修复：A4 加一条「同族脚手架不整体覆盖、仅定点修冲突项」。本次据此仅改 catch-up 角色表、status-update 原样保留，structure-check 全 PASS / exit=0。已知问题清零。

## 已知问题 · 待清零
（空 —— 理想态。发现即修，修进 changelog。）
