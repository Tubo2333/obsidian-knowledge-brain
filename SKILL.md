# Obsidian Knowledge Brain v3.0 / Obsidian 知识大脑 v3.0

**Schema**: 3.0 | **Lines**: ≤200 | **Load**: Always (if skill active)
**Platforms**: **Claude Code** — full auto (hooks + cron). **Cursor / Gemini CLI / Codex** — manual trigger (type "收尾" to save, "诊断" to bootstrap). Requires an AI Agent with file read/write. Not designed for plain-terminal or Agent-free use. / CC 全自动，其他平台需手动输入口令触发。

**Upgrade from v2.0**: zero vault dependency (无 vault 依赖), project-local `.claude/` storage. Obsidian is now optional — open your project folder as a vault for knowledge graph visualization. / Obsidian 现为可选——将项目文件夹作为 vault 打开即可获得知识图谱可视化。

**What this does / 它做什么**: Every time you debug an error or make a technical decision with an AI agent, that knowledge vanishes when the session ends. This skill **remembers** — it captures your decisions and error fixes across sessions, builds a searchable knowledge base, and evolves project rules automatically. A personal project librarian that learns from every conversation. / 每次和 AI 编程解决了 bug、做了技术决策，下次对话就忘了。这个 Skill 帮你**记住**——自动捕获每次会话的决策和错误，构建可检索的知识库，持续进化项目规则。一个从每次对话中学习的项目图书管理员。

**Obsidian?** Not required. v3.0 stores knowledge as `.md` files in `.claude/`. Open your project as an Obsidian vault to browse the knowledge graph — purely optional. See §0a. / 非必需。用 Obsidian 打开项目文件夹即可浏览知识图谱——完全可选。

→ **First time?** See `references/quickstart.md` (5-minute walkthrough / 5分钟上手).

## 0. Critical Rule / 关键规则 (Priority 0)

**At session end, extract knowledge. / 会话结束时提取知识。** Do NOT interrupt your work to write annotations mid-session — that breaks your flow. Work normally. At session end (T2 "收尾"), review the session transcript and extract ALL technical decisions and resolved errors into `[DECISION:]` / `[ERROR:]` format. This is a memory system — it learns from completed experiences, not live interruptions. / 这是记忆系统——它从已完成的经验中学习，不是从进行中的打断中学习。

Format: `[DECISION: <summary> | context: <why> | project: <slug> | scope: project|cross-project]` and `[ERROR: type=<from-taxonomy> | resolution=<fix> | project: <slug>]`. Missing required fields → mark `# MVA_FAIL:<field>` and leave in inbox.

## 0a. Prerequisites / 环境要求

**Required / 必需**: An AI Agent platform (Claude Code, Cursor, Gemini CLI, Codex) with file read/write capability + a project directory. / 一个有文件读写能力的 AI Agent 平台 + 一个项目目录。

**Recommended / 推荐**: Python 3.x (for hook scripts; all protocols work manually without it) + Git (version-control your knowledge base). / Python 3.x（钩子脚本）+ Git（版本控制）。

**Obsidian?** Not required. v3.0 stores knowledge as plain `.md` in `.claude/`. Open your project folder as an Obsidian vault to browse the knowledge graph — purely optional. v2.0 users: old vault data preserved in `archive/`, `.claude/memory/` is the new home. / 非必需。v3.0 用纯 `.md` 存储，用 Obsidian 打开项目文件夹即可浏览知识图谱——完全可选。

## 0b. Execution Model / 执行模型

This skill needs **file read + write permissions** in your project. It will: scan your directory structure (read), create `.claude/` skeleton files (write), and optionally move old files to `archive/` (write). **Nothing outside `<project>/.claude/` and `<project>/archive/` is ever modified.** / 此 Skill 需要项目内的文件读写权限。仅触碰 `.claude/` 和 `archive/`，绝不修改项目其他文件。

**Phase A is TWO-PASS / 两遍执行**:
1. **Diagnose & Plan (READ-ONLY / 只读)**: Agent scans your project, calculates chaos score, produces a plan: "I will create N files, move M files to archive/. Proceed?" No writes happen yet. Use T4 command `"诊断" / "diagnose"` to run only this pass.
2. **Execute (WRITE / 写入)**: After you approve the plan, Agent creates the skeleton, migrates files, validates. Use T4 `"整理项目" / "bootstrap"` for full execution.

**Interrupted? / 中断了？** If Phase A is interrupted (permission denied, session ended), re-run `"整理项目" / "bootstrap"`. Agent reads `PHASE_A_COMPLETE` marker state and resumes from where it left off. Files already created are skipped (idempotent). / 中断后重新运行即可，已创建的文件自动跳过。

**First run in a project?** Run `"诊断" / "diagnose"` first to see what Phase A will do before approving any writes. / 新项目先跑 `"诊断"` 看计划，再跑 `"整理项目"` 执行。

## 1. Phase Detection / 相位检测 (Execute FIRST)

Check `.claude/PHASE_A_COMPLETE`:
- Exists + `status: complete` + `bootstrap_date` ≤90 days → Phase B (skip bootstrap)
- Exists + `status: complete` + >90 days → re-validate 6 checklist items; pass→refresh date; fail→re-diagnose
- Exists + `status: in_progress` → re-run all 6 checks (marker only stores overall result, no per-item state)
- Corrupt YAML / missing fields → re-diagnose

3-axis check: `.claude/rules/` (≥8 valid-frontmatter files?) + `.claude/projects/` (≥1?) + `.claude/memory/` (pitfalls/ decisions/ preferences/ reference/ subdirs?). 3 green → Phase B. Any yellow/red → Phase A incremental. 2+ red → Phase A full bootstrap.

## 2. Phase A · Framework Bootstrap / 框架播种

→ Full instructions: `references/phase-a-bootstrap.md`

Summary: Diagnose chaos score (混沌度 0-12) → legacy automation audit (遗留自动化审计, reduced if chaos≤3) → classify raw content (parallel 3-tag labeling: IS_RULE/IS_PROJECT/IS_MEMORY) → build skeleton (CLAUDE.md + rules/ + projects/ + memory/) → migrate originals to archive/ → validate 6-item checklist → create `PHASE_A_COMPLETE` marker.

## 3. T1-T4 Trigger Contracts / 触发契约

### T1 · Session Start / 会话启动 (Required)
→ `references/t1-session-start.md`

5-step protocol: crash detection → T2 completion guard → inbox drain (MECE classify ALL annotations, always; pattern extraction gated by cold-start counter) → health summary → project briefing (≤30 lines, bilingual). Writes `.session_active` new marker.

### T2 · Session End / 会话结束 (Required)
→ `references/t2-session-end.md`

Safety net: F2 PRIMARY (user says "收尾" — the ONLY guarantee on all platforms). F1 auto on CC only. F4 catches crashes from inbox residue. No F3 (auto-checkpoint has no implementation — LLMs cannot count their own tool calls). Phase 1 quick close (① decisions ② errors ③ status ④ rule trigger update ⑤ ceiling check). Phase 2 deferred (⑥ rules created ⑦ rules outdated). MVA check before write. Anti-pollution. Delete `.session_active`. Emit `[SESSION_SUMMARY]`.

### T3 · Periodic Health Check / 定期健康检查 (Recommended)
→ `references/t3-periodic-check.md`

Trigger: L1 cron / L2 T1 detects >7 days / L3 user口令. Concurrent guard: skip if `.session_active` present. 7-dim scan (hard ceiling, contradiction, orphan, GC, pattern extraction Tier 1→2→3, index rebuild, legacy back-pressure). Tier 2 default OFF. ROI tracking: `hit_rate = 0` × 30 days → auto-degrade to cold-start.

### T4 · Manual Invoke / 手动调用 (On-demand)

| 中文 / English | Agent Action |
|---|---|
| "诊断" / "diagnose" | Phase A Pass 1 (READ-ONLY): scan project → chaos score + plan. No files modified. |
| "整理项目" / "bootstrap" | Phase A full: diagnose → plan → [confirm] → build → migrate → validate |
| "继续播种" / "resume bootstrap" | Resume interrupted Phase A from last checkpoint |
| "收尾" / "wrap up" | T2 F2: Phase 1 quick close (3-step) → write memory → [SESSION_SUMMARY] |
| "健康检查" / "health check" | T3 full 7-dim scan → HEALTH_REPORT.md |
| "规则审计" / "rule audit" | Rules-only: contradiction, staleness, ceiling, GC |
| "记忆整理" / "memory cleanup" | MECE re-classify inbox → memory/ + dedup merge |
| "重建索引" / "rebuild index" | Rebuild _keyword_index.json + CLAUDE.md index tables |
| "Skill 状态" / "skill status" | Output: Phase A/B state, inbox backlog, last health check, cold-start progress |

## 4. Annotation MVA Standards / 标注最低可行标准

| Annotation | Required Fields | Missing → |
|-----------|----------------|-----------|
| `[DECISION:]` | summary + context + project | `# MVA_FAIL:<field>`, stay in inbox |
| `[ERROR:]` | type (from error-taxonomy) + resolution + project | same |
| `[SESSION_SUMMARY]` | decisions + errors + rules_triggered | same |

Quality target: ≥90% field completeness. 3 consecutive sessions <90% → T3 warns.

**Anti-pollution (反污染)**: ① [DECISION:] store only FINAL adopted solutions, never dead-end explorations. ② [ERROR:] only FIXED errors; UNRESOLVED → inbox. ③ No intermediate states (不存中间态): temporary judgments, unverified hypotheses → do NOT annotate. ④ No duplicates: same type+root_cause_id → increment `sessions_observed` counter, no new file.

## 5. Cold Start Protocol / 冷启动协议

`memory/` empty or `mode: cold_start`: classify+store only, no pattern extraction. Counter in `_phase1_inbox.md` YAML frontmatter (`cold_start: {total_annotations, sessions_observed, threshold: 20, mode}`). ≥20 annotations AND ≥3 sessions → switch `mode: active`, announce transition.

## 6. File Manifest / 文件清单

```
<templates/> 4 files     → Agent uses these to create rules/projects/pitfalls/decisions
<references/> 10 files   → Agent loads on-demand per trigger/phase (each ≤80 lines)
  ├── Seed data:    error-taxonomy.md, root-cause-kb.md, domain-registry.md
  ├── Protocols:    t1-session-start.md, t2-session-end.md, t3-periodic-check.md
  ├── Bootstrap:    phase-a-bootstrap.md
  ├── User guides:  quickstart.md, platform-guide.md, troubleshooting.md
SKILL.md                 → Always loaded (≤200 lines)
```

## 7. Install & Config / 安装与配置

### Where to put files / 文件放哪里
Copy `obsidian-knowledge-brain/` into `<project>/.claude/skills/`. For non-Claude-Code platforms, run: `python scripts/install.py --platform cursor` (or `gemini`, `codex`). This replaces all `.claude/` paths with your platform's base directory. / 复制到 skill 目录后，非 CC 平台运行 `python scripts/install.py --platform cursor` 一键替换路径。

### Hook config (Claude Code only, optional) / 钩子配置
Claude Code `settings.json`:
- `SessionStart` → `session_start.py` (T1)
- `Stop` → `session_close.py --prompt` (T2)
- `CronCreate` weekly → `maintainer.py --health-check` (T3)

### No-hook / no-Agent fallback / 无钩子降级
If your platform has no hooks or no Agent: T1 via manually reading SKILL.md §0. T2 via typing "收尾" / "wrap up". T3 via typing "健康检查" / "health check". F3 auto-checkpoints still work if your Agent supports them. Core knowledge capture works even without hooks. / 即使没有钩子，核心知识捕获仍可通过口令手动触发。

### English-only users / 纯英语用户
All labels and headings are bilingual (Chinese + English). If you read only English, the `/ 中文` suffix is a term annotation — you can ignore it. The body text is English-primary. See §8 for term translations if curious. / 所有标签中英双语，纯英语读者可忽略 `/ 中文` 后缀，正文以英语为主。

## 8. FAQ / 常见问题

**Q: Nothing happens when I install. / 安装后没反应。** A: Agent auto-loads and runs §1. No Agent → manually follow §0 and §3. The skill is a protocol, not a daemon. More recovery scenarios: `references/troubleshooting.md`.

**Q: Why `.claude/`? I use Cursor. / 为什么是 `.claude/`？** A: Replace with `.cursor/` (see `references/platform-guide.md`). The folder name is convention — structure works on any platform.

**Q: How long until useful? / 多久见效？** A: ~3 sessions × ~7 annotations → 20 total → pattern extraction activates. Before that, everything is still stored — just no auto-detection yet.

**Q: Can I use this without any Agent? / 没 Agent 能用？** A: No. This skill requires an AI Agent to execute MECE classification, cold-start counting, and pattern extraction. Without an Agent, you have empty directories and unused templates — not a functioning knowledge system. See `references/platform-guide.md` for supported platforms. / 不行，此 Skill 需要 AI Agent 执行协议。

## 9. Bilingual Terminology / 中英术语对照

| English | 中文 | English | 中文 |
|---------|------|---------|------|
| Framework Skeleton | 框架骨架 | Memory Engine | 记忆引擎 |
| Trigger Contract | 触发契约 | Annotation | 标注 |
| Chaos Score | 混沌度 | Cold Start | 冷启动 |
| MECE Classification | 互斥穷尽分类 | Pattern Extraction | 模式提取 |
| Root Cause KB | 根因知识库 | Error Taxonomy | 错误分类法 |
| Pitfall | 陷阱 | Decision | 决策 |
| Health Check | 健康检查 | Bootstrap | 播种/减负 |
| Deferred Audit | 延迟审计 | Safety Net | 兜底/安全网 |
