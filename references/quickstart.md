# Quick Start / 快速上手 (5 min)

First time using obsidian-knowledge-brain? Follow these 3 steps.

**⚠️ Non-Claude-Code users (Cursor, Gemini, Codex)**: The skill does NOT auto-start. Your first message MUST tell the Agent to load SKILL.md: `"请读取 .cursor/skills/obsidian-knowledge-brain/SKILL.md 并执行相位检测"` (use your platform's path). Without this, the skill sits dormant — installed but never executed. / 非 CC 用户：第一条消息必须让 Agent 加载 SKILL.md，否则 Skill 不会启动。

## Step 1: First Session — Bootstrap / 第一次：播种

**Tip**: Run `"诊断" / "diagnose"` first — READ-ONLY. Then `"整理项目" / "bootstrap"` to execute. / 先"诊断"看计划，再"整理项目"执行。

When the Agent runs bootstrap, it auto-detects your project state (~5-10 min):

```
Agent: "Chaos score: 7/12. Plan: create 23 files in .claude/, move 0 to archive/."
Agent: "Proceed? [User approves]"
Agent: "Created .claude/rules/ (9 domain files). Created .claude/projects/."
Agent: "PHASE_A_COMPLETE — framework ready."
```

Clean project? Agent skips bootstrap. Interrupted? Re-run `"整理项目"` — idempotent, resumes from breakpoint. / 中断重跑即可从断点继续。

## Step 2: Work Normally / 正常工作

Work normally. Don't interrupt yourself to take notes. The skill learns when the session ENDS, not during it. / 正常干活，不用边工作边记笔记。

## Step 3: End Session — Wrap Up / 收尾 (CRITICAL)

Type **"收尾"** / **"wrap up"**. The Agent reviews the session transcript and extracts ALL decisions and error fixes. This is the ONLY moment knowledge is captured — if you skip this step, everything from this session is permanently lost. / 这是知识被捕获的唯一时刻——跳过这步，本次会话的一切永久丢失。

Agent output example:
```
Saved: 2 decisions → memory/decisions/ (use-limma, switch-docx)
       3 errors → memory/pitfalls/ (encoding, segfault, gfw-blocked)
       MVA checks: 5/5 passed.
```

## Next Session / 下次会话

When you start a new session, you'll see a briefing like:
```
## Session Briefing / 会话简报
**Cold Start / 冷启动**: 3/20 annotations, 1 session.
**Last session**: [ERROR: type=encoding | resolution: ...]
**Health / 健康**: No violations.
```

After ~20 annotations across ~3 sessions, the skill enters **active mode** and starts detecting patterns: "You've hit this same GFW error 3 times. Here's the known fix."

## One-Minute Commands / 一分钟命令

| Say / 说 | What happens / 效果 |
|-----------|-------------------|
| "诊断" / "diagnose" | Read-only project scan + plan (no writes) |
| "整理项目" / "bootstrap" | Full Phase A bootstrap |
| "收尾" / "wrap up" | Save session knowledge |
| "健康检查" / "health check" | Full project health scan |
| "Skill 状态" / "skill status" | Show what the skill knows so far |
→ All 10 commands: SKILL.md §3 T4 | Deep dive: `references/t1-session-start.md` to `t3-periodic-check.md`

## v4.0: Cross-Project Knowledge / 跨项目知识

v4.0 adds a global atom table at `~/.obsidian-knowledge-brain/atoms.json`. When the same error occurs in >=2 independent projects, the Agent will offer to promote it to global knowledge. Once promoted, every project's pre-action check sees it — prevention, not just memory. / v4.0 增加全局原子表。同一错误在 >=2 个独立项目中复现时，Agent 会提议晋升为全局知识。晋升后所有项目都能在动手前看到警告。

The four trigger words are the same. What changes is what happens after "收尾" — the Agent now checks for cross-project patterns and offers promotion. / 四个触发词不变。"收尾"之后 Agent 会检查跨项目模式并提议晋升。