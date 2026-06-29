# Troubleshooting / 故障排查

Stuck? This guide covers common recovery scenarios. If your problem isn't here, run `"Skill 状态"` / `"skill status"` to see the current state.

## Phase A: Bootstrap Problems / 播种问题

### "I ran bootstrap but nothing happened" / "跑了整理项目但没变化"
1. Run `"Skill 状态"` — check if `PHASE_A_COMPLETE` exists
2. If `status: in_progress` → bootstrap was interrupted, re-run `"整理项目"`
3. If no marker at all → the Agent may not have write permission. Check that `.claude/` directory was created
4. The skill only touches `.claude/` and `archive/` — it never modifies your source code

### "Chaos score is wrong" / "混沌度评分不对"
The chaos score is a diagnostic, not a judgment. It measures structure, not code quality. If the score feels wrong:
- 0-3: Your project already has a clean structure. Bootstrap skipped — this is expected.
- 4-7: Some gaps found. The Agent fills only what's missing.
- 8-12: Significant reorganization needed. The Agent presents a plan first — you approve before any writes.

### "Bootstrap interrupted — how to resume?" / "播种中断了怎么继续"
Re-run `"整理项目"` / `"bootstrap"`. All bootstrap steps are idempotent:
- Already-created files are skipped
- Already-moved originals are not re-moved
- The 6-item validation checklist is re-run from scratch
- If the interruption was due to permission denial, approve file writes when prompted

## Phase B: Memory Problems / 记忆问题

### "I wrote an [ERROR:] but it's gone next session" / "写了标注但下次会话找不到了"
1. Check `_phase1_inbox.md` — does your annotation appear there?
2. Look for `# MVA_FAIL:<field>` markers — missing required fields prevent classification
3. Required: `[ERROR:]` needs `type=` + `resolution=` + `project:`. `[DECISION:]` needs `summary` + `context:` + `project:`
4. If the annotation is in inbox but not in `memory/pitfalls/`, the MECE classifier may not have run. Check cold-start counter — `"Skill 状态"` shows current mode

### "Still in cold start after many sessions" / "用了很久还是冷启动"
Cold start exits when: ≥20 total annotations AND ≥3 sessions. Common misunderstandings:
- 50 annotations in 1 session = 1 session. You need ≥3 separate sessions.
- Annotations with `# MVA_FAIL` don't count toward the total (they stay in inbox, unclassified)
- Check `"Skill 状态"` for exact counter values

### "Health check never runs" / "健康检查从不执行"
T3 triggers three ways:
1. Automatic (Claude Code only): weekly cron via `CronCreate`
2. T1 reminder: if `last_check > 7 days`, the session briefing includes a reminder
3. Manual: type `"健康检查"` / `"health check"` any time
If using a non-CC platform, you must trigger T3 manually or via your own scheduler.

## General / 通用问题

### "Skill does nothing when installed" / "安装后完全没反应"
This skill is a **protocol**, not a background service. It works when:
- Your AI Agent reads SKILL.md and follows its instructions (Claude Code, Cursor, etc.)
- You manually invoke T4 commands (`"收尾"`, `"诊断"`, `"健康检查"`)
If you're on a platform without Agent auto-loading, start by reading SKILL.md §0 (Critical Rule) and §0a (Prerequisites).

### "Too many permission prompts" / "权限弹窗太多"
Phase A bootstrap creates ~20-25 files in `.claude/`. This is a one-time cost. After bootstrap, typical sessions only modify 1-3 files. Run `"诊断"` first to see the plan, then `"整理项目"` to execute — you'll know exactly how many prompts to expect.

### "How do I verify everything is working?" / "怎么确认一切正常"
After bootstrap, you should see:
- `CLAUDE.md` — navigation hub
- `.claude/rules/` — 9+ domain files
- `.claude/projects/` — 1+ project files
- `.claude/memory/` — 4 subdirectories (pitfalls/ decisions/ preferences/ reference/) + `_phase1_inbox.md`
- `.claude/PHASE_A_COMPLETE` — confirmation marker
- `archive/.claude-archive/README.md` — recovery instructions

Run `"Skill 状态"` for a live status summary.

## v4.0: Global Atom Table / 全局原子表问题

### "Pre-action instruction missing from CLAUDE.md" / "预行动指令丢失"
1. Check `~/.obsidian-knowledge-brain/.uninstalled` — if it exists, delete it and re-run `python scripts/install.py`
2. If `.uninstalled` doesn't exist, re-run `python scripts/install.py` — injection is idempotent
3. Verify with: `grep "Knowledge triggers" CLAUDE.md` — should return exactly 1 match

### "atoms.json corrupted" / "atoms.json 损坏"
1. Check `~/.obsidian-knowledge-brain/atoms.json.bak` — if valid, it auto-recovers on next read
2. If both are corrupt, atoms.json is rebuilt from any project's `_global_atoms` section (metadata loss — see SKILL.md section 0c L9)
3. To force rebuild: delete both atoms.json and atoms.json.bak, then re-run install.py

### "Promotion never happens" / "晋升从不触发"
1. Promotion requires: same `root_cause_id` in >=2 independent projects
2. T2 "收尾" checks for this — make sure you say "收尾" at session end
3. Promotion is human-confirmed — the Agent asks `[y/N]`, you must respond "y"
4. Check `~/.obsidian-knowledge-brain/atoms.json` to see current active atoms

### "Pre-action triggers not firing" / "预行动触发器不工作"
1. Pre-action is a MUST instruction in the always-loaded file — it relies on Agent compliance, not mechanical enforcement
2. On non-Claude-Code platforms: verify the always-loaded file is actually loaded by your platform
3. If the keyword index doesn't exist (project not bootstrapped), Pre section is gracefully skipped
