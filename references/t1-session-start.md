# T1 · Session Start / 会话启动

**Required**. Trigger: new session begins. Hook or Agent self-trigger.
All paths below are relative to `$PROJECT_ROOT/.claude/`.

## Input Files / 输入文件
- `.session_active` — old marker (crash detection / 崩溃检测)
- `memory/_phase1_inbox.md` — last 50 lines (annotation stream / 会话输出流)
- `HEALTH_REPORT.md` — summary line, violation counts
- `projects/<slug>.md` — current project (match by working directory or read most-recently-modified)

## 5-Step Protocol / 五步启动协议

### Step 1: Crash Detection / 崩溃检测
Check `.session_active` exists. YES → prior session crashed. Check inbox for any unsaved annotations. Also check for platform transcript JSONL (F4 recovery / F4恢复). Warn user of detected crash and recovery options.

### Step 2: T2 Completion Guard / T2完成检测
Compare `memory/_phase1_inbox.md` mtime vs `.session_active` mtime. If inbox modified after session marker → T2 may not have completed → warn user.

### Step 3: Inbox Drain / 收件箱排空
**Always execute** — classification (分类) and storage (存储) are NOT gated by cold start. Only pattern extraction (模式提取) is gated.

1. Read last 50 lines of `memory/_phase1_inbox.md`
2. Extract `[DECISION:]` and `[ERROR:]` annotations
3. Run MECE classifier (互斥穷尽分类器):
   - Is it an error/trap? → `memory/pitfalls/<slug>.md`
   - Is it a technical decision? → `memory/decisions/<slug>.md`
   - Is it a user preference? → `memory/preferences/<slug>.md`
   - Is it a factual reference? → `memory/reference/<slug>.md`
   - Tiebreaker: pitfalls > decisions > preferences > reference
4. Write mandatory cross-references (强制交叉引用): If classified to `pitfalls/` AND mentions a decision → link `memory/decisions/<slug>.md`. If `decisions/` AND mentions an error → link `memory/pitfalls/<slug>.md`. Format: `— <为何相关 / one-line relevance>` (summary+link, preserves Single Home).
5. Read cold-start counter (冷启动计数器) from `memory/_phase1_inbox.md` YAML frontmatter.
6. **Mark classified entries** (标记已分类): After successfully writing an annotation to a memory/ file, append `<!-- classified:YYYY-MM-DD -->` to that annotation line in the inbox. On next T1, scan inbox for lines WITHOUT this marker — prevents duplicate classification. / 分类完成后在 inbox 中标记，下次 T1 跳过已分类行。
7. **`total_annotations` is automatic** — `session_start.py` counts files in `memory/` subdirectories at each session start. No manual increment needed. After MECE classification, the script will pick up the new count next session. / total_annotations 由脚本自动从文件系统计数，无需手动递增。
8. Check mode transition: If `total_annotations >= 20 AND sessions_observed >= 3` → switch `mode: active`, announce "Memory engine entering active mode — pattern extraction enabled." If still `cold_start`, tell user current progress: "N/20 lessons stored across M sessions."

### Step 4: Health Summary / 健康摘要
Read `HEALTH_REPORT.md` summary. If violations exist → include in briefing. If `last_check` > 7 days ago → remind user to run T3 health check.

### Step 5: Project Briefing / 项目简报
Read `projects/<slug>.md` Current Status + Blockers. Output ≤30 line bilingual briefing. Write new `.session_active` marker.

## Output / 输出
- New `.session_active` marker (timestamp)
- ≤30 line bilingual briefing injected into context
- Possible `memory/` writes (MECE-classified annotations) + updated cold-start counters in `_phase1_inbox.md` frontmatter

## Failure Modes / 失败模式
- Agent skips protocol → briefing missing → next T1 or T3 detects gap
- `_phase1_inbox.md` unreadable → skip Step 3, do not block session start
- Crash with no F3 checkpoints and no transcript → report unrecoverable loss (F4 data dependency matrix)

## Platform Notes / 平台说明
- **Claude Code**: `SessionStart` hook → `session_start.py`
- **No-hook**: Agent reads SKILL.md → self-executes this protocol
