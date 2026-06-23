# obsidian-knowledge-brain v3.0

An AI agent skill that remembers every technical decision and bug fix across sessions — and learns from them. Zero dependencies, no external vault, works on Claude Code, Cursor, Gemini CLI, and Codex.

**How it works**: At session end, type "收尾" / "wrap up". The Agent classifies your decisions and error fixes into `.claude/memory/`, builds cross-references, and updates project rules. After ~20 annotations across ~3 sessions, it starts detecting patterns: "You've hit this same GFW error 3 times across 2 projects — here's the known fix."

**Key features**: Auto-bootstrap from chaos (scan → plan → build skeleton), cold-start protocol (classify-only until 20 annotations), 7-dimension health checks (ceiling, contradictions, orphans, GC), bilingual Chinese/English, optional Obsidian graph view.

**Cost**: Zero. No API calls, no servers. ~3K-8K tokens/session for Agent classification.
