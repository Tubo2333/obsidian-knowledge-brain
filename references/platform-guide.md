# Platform Adapter Guide / 平台适配指南

obsidian-knowledge-brain works on any Agent platform. This guide covers setup for non-Claude-Code environments. / 本指南覆盖非 Claude Code 环境的配置。

## Path Mapping / 路径映射

The skill uses `.claude/` as the default base directory. On other platforms, substitute:

| Platform | Base dir | Config file | Hook system |
|----------|----------|-------------|-------------|
| Claude Code | `.claude/` | `settings.json` | SessionStart / Stop / CronCreate |
| Cursor | `.cursor/` | `.cursorrules` | None (manual T1/T2 only) |
| Gemini CLI | `.gemini/` | `extensions.json` | Extension hooks (if available) |
| Codex | `.codex/` | `codex.yaml` | None (manual T1/T2 only) |

**On install**, replace all `.claude/` paths in SKILL.md with your platform's base. The file structure underneath (`rules/`, `projects/`, `memory/`) stays the same. / 安装时将 `.claude/` 替换为对应平台目录，下层结构不变。

## Capability Tiers / 能力分级 (be honest / 诚实版)

| Tier | Platforms | What actually works | What does NOT work |
|------|-----------|--------------------|--------------------|
| **Full auto** | Claude Code only | T1+T2 via hooks, T3 via cron. Install → Agent auto-loads SKILL.md → Phase A auto-detected. Zero manual steps. | — |
| **Manual trigger** | Cursor, Gemini CLI, Codex | T1: Agent reads SKILL.md when you say "加载 obsidian-knowledge-brain". T2: type "收尾" before closing. T3: type "健康检查" weekly. MECE classification works if Agent loads references. | No auto-start. No auto-close. No cron. You MUST remember to trigger every step yourself. |
| **Not supported** | Plain terminal, web ChatGPT, Agent-free | Nothing. The skill produces empty directories without an Agent to execute protocols. | Everything. |

**Critical**: On Cursor/Codex, the skill does NOT auto-start. The Agent does not know it exists until you tell it. Say: "请读取 .cursor/skills/obsidian-knowledge-brain/SKILL.md 并执行相位检测" as your first message. / 在 Cursor/Codex 上，Skill 不会自动启动，你需要在第一条消息里告诉 Agent 去读 SKILL.md。

## Cursor Setup / Cursor 配置

1. Copy `obsidian-knowledge-brain/` to `.cursor/skills/obsidian-knowledge-brain/`
2. In SKILL.md §1, replace `.claude/` with `.cursor/`
3. Start a Composer session — the Agent reads SKILL.md and auto-executes Phase Detection
4. At session end, type "收尾" or "wrap up" to trigger T2
5. For health checks, type "健康检查" weekly

## Gemini CLI Setup / Gemini CLI 配置

Copy `obsidian-knowledge-brain/` to `.gemini/extensions/obsidian-knowledge-brain/`. If extensions support hooks → configure start/stop hooks. If no hooks → same manual workflow as Cursor.

## Feature Loss by Platform / 各平台功能损失

| Feature | CC | Cursor | Gemini |
|---------|-----|--------|--------|
| Auto T1 briefing | ✅ | ⚠️ Agent-read | ⚠️ Agent-read |
| Auto T2 close | ✅ | ❌ 口令 | ❌ 口令 |
| T3 cron health check | ✅ | ❌ Manual | ❌ Manual |
| PHASE_A_COMPLETE auto | ✅ | ✅ | ✅ |
| Transcript available | ✅ (JSONL) | ⚠️ Platform-dependent | ⚠️ Platform-dependent |
