# memory-brain v3.0 / 记忆大脑 v3.0

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Cursor%20%7C%20Gemini%20%7C%20Codex-lightgrey)

> **An AI agent skill that remembers every technical decision and bug fix across your sessions — and learns from them.**
> **一个让 AI Agent 跨会话记住技术决策和错误修复、并自动学习的技能。**

Every time you debug an error with an AI agent, that knowledge vanishes when the session ends. **memory-brain** captures it — automatically building a searchable knowledge base that evolves project rules over time. Like a project librarian that learns from every conversation.

---

## v2.0 → v3.0: What Changed / 演进

v2.0 required an Obsidian vault, Python cron scripts, and Claude Code hooks. It was powerful but heavy — 11 Python scripts, a vault directory tree, and tight coupling to one platform.

**v3.0 is a skill-only system.** No vault. No scripts. No cron daemon. It works purely through the AI Agent reading and writing `.md` files in your project's `.claude/` directory.

| | v2.0 | v3.0 |
|---|------|------|
| **Storage** | External Obsidian vault | `.claude/` inside your project |
| **Execution** | Python scripts + hooks | AI Agent reads/writes markdown |
| **Dependencies** | Python 3.10+, PyYAML, requests | None (Agent-native) |
| **Platforms** | Claude Code only | CC, Cursor, Gemini CLI, Codex |
| **Obsidian** | Required vault | Optional visual browser |
| **Bootstrap** | `setup.py` interactive | Agent auto-detects + plans |

The core idea is the same — [DECISION] and [ERROR] annotations → MECE classification → pattern extraction → rule evolution. But v3.0 makes the Agent the executor, not a Python pipeline.

---

## Installation / 安装

### Claude Code (full auto)

```bash
git clone https://github.com/<user>/memory-brain.git .claude/skills/memory-brain/
```

That's it. The Agent auto-loads the skill on next session start. For optional hook automation (T1/T2/T3), add to `settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{ "command": "python .claude/skills/memory-brain/scripts/session_start.py" }],
    "Stop": [{ "command": "python .claude/skills/memory-brain/scripts/session_close.py --prompt" }]
  }
}
```

### Cursor / Gemini CLI / Codex (manual trigger)

Copy the `memory-brain/` folder into your platform's skill directory:

| Platform | Target directory |
|----------|-----------------|
| Cursor | `.cursor/skills/memory-brain/` |
| Gemini CLI | `.gemini/extensions/memory-brain/` |
| Codex | `.codex/skills/memory-brain/` |

Replace `.claude/` paths in SKILL.md with your platform's base. Then type commands manually — the Agent reads SKILL.md and executes protocols on your trigger words. See `references/platform-guide.md`.

---

## Quick Start in Four Words / 四个词上手

| Trigger / 触发词 | What it does / 效果 |
|-----------|------|
| **诊断** / `diagnose` | Agent scans your project, reports chaos score, proposes a plan — no files touched |
| **整理项目** / `bootstrap` | Agent builds `.claude/rules/` + `.claude/projects/` + `.claude/memory/` skeleton |
| **收尾** / `wrap up` | End of session: save decisions, errors, update project status |
| **健康检查** / `health check` | Full 7-dimension scan: ceiling violations, contradictions, orphans, GC suggestions |

**Work normally.** The skill captures knowledge from your flow — not by interrupting it.

---

## Cost / 花费

**Zero monetary cost.** This is a set of markdown templates and Agent protocols — no API calls, no servers, no subscription. The "cost" is:

- ~5-10 minutes for first bootstrap (Agent reads/writes ~15 files)
- ~2 minutes per session end for "收尾" wrap-up
- ~50-200 lines added to your `.claude/` directory per session

Token usage: approximately 3,000-8,000 tokens per session for annotation and classification. Comparable to reading a few extra files.

---

## Obsidian Integration (Optional) / Obsidian 集成（可选）

v3.0 stores knowledge as plain `.md` files in `.claude/memory/`. To browse as a knowledge graph:

1. Open your project folder as an Obsidian vault
2. The `.claude/` directory becomes a browsable wiki
3. `[[wikilinks]]` between decisions, pitfalls, and rules render as graph edges

No plugin needed. The folder-is-vault convention works with any Markdown editor — Obsidian just makes the cross-references visual.

---

## What's Inside / 目录结构

```
memory-brain/
├── SKILL.md                    ← Agent skill definition (≤200 lines, always loaded)
├── README.md                   ← This file
├── LICENSE                     ← MIT
├── description.md              ← Marketplace listing (≤500 chars)
├── templates/                  ← 4 templates for rules, projects, pitfalls, decisions
├── references/                 ← 10 protocol & seed data files (each ≤80 lines)
│   ├── quickstart.md           ← 5-minute walkthrough
│   ├── platform-guide.md       ← Cursor/Gemini/Codex setup
│   ├── troubleshooting.md      ← Common recovery scenarios
│   ├── domain-registry.md      ← Rule domain vocabulary for bootstrap
│   ├── error-taxonomy.md       ← Error type vocabulary (50+ types)
│   ├── root-cause-kb.md        ← Known root cause → symptom lookup
│   ├── phase-a-bootstrap.md    ← Framework skeleton builder protocol
│   ├── t1-session-start.md     ← Session start 5-step protocol
│   ├── t2-session-end.md       ← Session end close protocol
│   └── t3-periodic-check.md    ← Weekly health check 7-dim scan
└── scripts/                    ← 18 Python scripts (v2 hook automation + v3 install.py)
    ├── install.py              ← Cross-platform path setup (NEW v3)
    ├── session_harvester.py    ← Hook harvest: Stop + SessionStart
    ├── runner.py               ← Pipeline orchestrator (5-step)
    ├── analyzer.py             ← Root-cause analysis (keyword + LLM)
    ├── maintainer.py           ← Rule lifecycle + merge detection
    ├── reporter.py             ← Weekly reports + index rebuild
    ├── compiler.py             ← Agent Memory sync
    ├── backup.py               ← JSONL transcript backup
    ├── setup.py                ← Interactive vault setup (v2 legacy)
    ├── config.py               ← Configuration loader
    └── ...                     ← 8 more utility scripts
```

---

## FAQ / 常见问题

**Q: Does this need Obsidian?**
A: No. v3.0 stores everything in `.claude/` inside your project. Obsidian is an optional viewer.

**Q: Does it work without Claude Code?**
A: Yes — Cursor, Gemini CLI, and Codex all work via manual trigger words. See `references/platform-guide.md` for capability tiers.

**Q: How long until it's useful?**
A: ~3 sessions × ~7 annotations → 20 total → pattern extraction activates. Before that, everything is still stored — just no auto-detection yet.

**Q: Does it call external APIs?**
A: No. All classification is deterministic (MECE rules + heuristic matching). LLM-based pattern extraction is an optional Tier 2 feature gated behind explicit human opt-in.

---

## License / 许可证

MIT — use it, modify it, distribute it freely.
