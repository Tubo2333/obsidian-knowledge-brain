# T2 · Session End / 会话结束

**Required**. Trigger: session about to end.

## Detection Layers / 检测层 (3 real layers + 1 aspirational note)

| Layer | Mechanism | Reality |
|-------|-----------|---------|
| **F2** | User口令: "收尾" / "wrap up" / "结束" | **PRIMARY** — the only layer that works on ALL platforms. You must type this before closing. |
| **F1** | Platform hook (Stop hook / 平台钩子) | **Auto on CC only** — fires session_close.py automatically. Does NOT exist on Cursor/Gemini/Codex. |
| **F4** | Next T1 recovery (下次T1补收割): detect `.session_active` residue → recover from inbox content | **Last resort** — catches crashes. Reads whatever is in the inbox (annotations, partial F3 dumps if any). |

**F2 is the only guarantee.** F1 is a convenience on one platform. There is no F3 — the "auto-checkpoint every ~10 tool calls" mechanism has no implementation (LLMs cannot count their own tool calls). If the Agent happens to write mid-session annotations to the inbox, F4 will recover them. But never rely on this. **Say "收尾" before every session end.** / F2 是唯一的保证。每次会话结束前必须说"收尾"。

## Phase 1 — Quick Close / 快速关闭 (MUST execute)

**Before you start**: Review the session transcript. Scan the conversation for: (a) technical decisions — moments where you chose between alternatives, (b) resolved errors — bugs you fixed or workarounds you found, (c) user preferences — explicit style/tool choices the user made. Extract these into annotations NOW. Do NOT rely on having written them mid-session — you were focused on work, not on note-taking. The transcript is your raw material. / 回顾会话 transcript，从中提取所有决策、错误修复、用户偏好。不要依赖会话中途的笔记——你当时在专注工作，不是在做笔记。

### ① Decisions / 技术决策
- Project-scoped → append to `projects/<slug>.md` Recent Milestones
- Cross-project → `memory/decisions/<slug>.md` (new or append)
- Fallback → `memory/_phase1_inbox.md`
- Format: `[DECISION: <summary> | context: <why> | project: <slug> | scope: project|cross-project]`

### ② Errors / 错误及方案
- Phase 2 → `memory/pitfalls/<slug>.md` (new or append)
- Fallback → `memory/_phase1_inbox.md`
- Format: `[ERROR: type=<from-taxonomy> | resolution=<fix> | project: <slug>]`
- **Anti-pollution (反污染)**: Only store FIXED errors. If unresolved → mark `resolution: UNRESOLVED` → leave in inbox. If `error_type + root_cause_id` matches existing pitfall → update `sessions_observed` counter only, do NOT create duplicate file.

### ②b. Cross-Project Promotion Detection / 跨项目晋升检测 (v4.0)

For each `[ERROR:]` annotation in this session:

1. **Compute root_cause_id**:
   - Exact match: error `type` found in `references/error-taxonomy.md` → use the same `root_cause_id` as prior occurrences
   - Fuzzy match (type not in taxonomy): compare resolution patterns against existing errors in `memory/pitfalls/` → Agent detects same root cause → human confirms → same ID
   - New error type → assign `root_cause_id = <error_type>` (first occurrence, project-local only)

2. **Check for cross-project recurrence**:
   - Read `~/.obsidian-knowledge-brain/atoms.json`
   - Search for existing atom where `project_origin` contains ≥1 project NOT the current project AND the atom ID matches (same root_cause_id + type hash)
   - Same root_cause_id under different project → **cross-project match → promotion candidate**

3. **First occurrence handling**:
   - root_cause_id NOT in any atom → store locally in current project's `memory/pitfalls/` (NOT promoted)
   - Generate keyword entries in local `_keyword_index.json` only

4. **Promotion candidate → present to user**:
   ```
   Error type "<type>" has now occurred in projects: [A, B].
   This is a cross-project pitfall. Promote to global atom table?
   [y/N]
   ```

5. **If user confirms (y)**:
   - Generate trigger keywords (1-5) from the error's resolution field and type
   - Extract function/library/tool names (e.g. "python-docx", "pandoc", "sva::ComBat")
   - Agent proposes keywords → user confirms or edits
   - Compute atom ID: `{DOMAIN}-{SHA256(root_cause_id + type)[:8]}`
     - DOMAIN from `references/domain-registry.md` atom_prefix mapping
   - Run promotion via `python scripts/global_atoms.py --promote` with atom data
   - Update local `_keyword_index.json` via safe-merge sync

6. **If user declines (N or timeout)**:
   - Store as project-local pitfall in `memory/pitfalls/`
   - Do NOT add to global atom table

### ③ Project Status / 项目状态
Update `projects/<slug>.md` frontmatter: `updated: <today>`. If `status` enum changed → update `status` too.

### ④ Rule Trigger Update / 规则触发更新 (CRITICAL — do now, not deferred)
Search `rules/*.md` by `domain` field in YAML frontmatter → update `last_triggered: <today>`. Not found → write to inbox for manual review. This MUST happen in Phase 1, not Phase 2 — deferred audit may never run on non-CC platforms.

### ⑤ Hard Ceiling Check / 硬上限检查 (CRITICAL — do now)
Check `rules/*.md` ≤80 lines, `projects/*.md` ≤60, root `CLAUDE.md` ≤100. If any file exceeds ceiling → flag in `[SESSION_SUMMARY]` and either trigger Split Protocol or warn user.

**MVA Check (最低可行标注)**: Before writing, verify required fields. `[DECISION:]` needs `summary + context + project`. `[ERROR:]` needs `type + resolution + project`. Missing → mark `# MVA_FAIL:<field>` and leave in inbox.

## Phase 2 — Deferred Audit / 延迟审计 (Optional, T3 can supplement)

| # | Operation | Target |
|---|-----------|--------|
| ⑥ | Rules created/modified | `rules/<domain>.md` — append or modify section |
| ⑦ | Rules outdated | Insert `<!-- DEPRECATED: <reason> -->` in rule file |

## Output / 输出
- `memory/_phase1_inbox.md` (append)
- `memory/pitfalls/<slug>.md` or `memory/decisions/<slug>.md` (Phase 2 writes)
- `projects/<slug>.md` (`updated` refreshed)
- `rules/*.md` (`last_triggered` updated by domain field, not filename)
- **Delete** `.session_active`
- Emit `[SESSION_SUMMARY]` block (format: `[SESSION_SUMMARY: decisions: [...], errors: [...], rules_triggered: [...], project_status_changed: true|false, files_over_ceiling: [...]]`)
- **MUST confirm to user / 必须向用户确认**: After Phase 1 completes, tell the user what was saved: "Saved: 3 decisions → `memory/decisions/`, 2 errors → `memory/pitfalls/`. Project `my-project` status updated. MVA checks: all passed." / 告知用户保存了多少条、存到了哪里、MVA 检查是否通过。

## Failure Modes / 失败模式
- Terminal kill (Ctrl+C×2) → `.session_active` residue → F4 recovery from inbox content
- Only Phase 1 completed → core knowledge captured; Phase 2 deferred to T3
- No Phase 1, no transcript → F4 reports unrecoverable loss

## Platform Notes / 平台说明
(All paths relative to `$PROJECT_ROOT/.claude/` unless qualified.)
- **Claude Code**: `Stop` hook → `session_close.py --prompt` (Agent answers 5-step Phase 1) → `session_harvester.py` supplements with automated transcript harvesting and session data extraction
- **No-hook**: F2 user口令 → next T1 verifies via F4 recovery check. If platform has no transcript, Agent relies on conversation memory — less reliable but better than nothing.
