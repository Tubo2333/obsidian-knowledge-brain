# obsidian-knowledge-brain v3.0 / Obsidian 知识大脑 v3.0

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Cursor%20%7C%20Gemini%20%7C%20Codex-lightgrey)

> **An AI agent skill that remembers every technical decision and bug fix across your sessions — and learns from them.**
> **一个让 AI Agent 跨会话记住技术决策和错误修复、并自动学习的技能。**

Every time you debug an error with an AI agent, that knowledge vanishes when the session ends. **obsidian-knowledge-brain** captures it — automatically building a searchable knowledge base that evolves project rules over time. Like a project librarian that learns from every conversation.

每次和 AI 编程解决了 bug、做了技术决策，下次对话就忘了。**obsidian-knowledge-brain** 帮你记住——自动构建可检索的知识库，持续进化项目规则。一个从每次对话中学习的项目图书管理员。

---

## v2.0 → v3.0: What Changed / 演进

v2.0 required an Obsidian vault, Python cron scripts, and Claude Code hooks. It was powerful but heavy — 11 Python scripts, a vault directory tree, and tight coupling to one platform.

v2.0 需要 Obsidian vault、Python 定时脚本、Claude Code hooks。强大但沉重——11 个 Python 脚本、一整套 vault 目录树、绑定单一平台。

**v3.0 is a skill-only system. / v3.0 是纯技能系统。** No vault. No scripts. No cron daemon. It works purely through the AI Agent reading and writing `.md` files in your project's `.claude/` directory. 无 vault。无脚本。无守护进程。Agent 直接在项目 `.claude/` 里读写 `.md` 文件执行全部逻辑。

| | v2.0 | v3.0 |
|---|------|------|
| **Storage / 存储** | External Obsidian vault | `.claude/` inside your project / 项目内 `.claude/` |
| **Execution / 执行** | Python scripts + hooks | AI Agent reads/writes markdown / Agent 读写 markdown |
| **Dependencies / 依赖** | Python 3.10+, PyYAML, requests | None (Agent-native) / 零依赖 |
| **Platforms / 平台** | Claude Code only | CC, Cursor, Gemini CLI, Codex |
| **Obsidian** | Required vault / 必须 | Optional visual browser / 可选浏览 |
| **Bootstrap / 播种** | `setup.py` interactive | Agent auto-detects + plans / Agent 自动诊断+规划 |

The core idea is the same — [DECISION] and [ERROR] annotations → MECE classification → pattern extraction → rule evolution. But v3.0 makes the Agent the executor, not a Python pipeline.

核心思路不变：[DECISION] 和 [ERROR] 标注 → 互斥穷尽分类 → 模式提取 → 规则进化。但 v3.0 让 Agent 成为执行者，而非 Python 流水线。

---

## Installation / 安装

### Claude Code (全自动 / full auto)

```bash
git clone https://github.com/Tubo2333/obsidian-knowledge-brain.git .claude/skills/obsidian-knowledge-brain/
```

That's it. The Agent auto-loads the skill on next session start. / 搞定。Agent 下次启动自动加载。

For optional hook automation (T1/T2/T3), add to `settings.json`: / 可选钩子自动化：

```json
{
  "hooks": {
    "SessionStart": [{ "command": "python .claude/skills/obsidian-knowledge-brain/scripts/session_start.py" }],
    "Stop": [{ "command": "python .claude/skills/obsidian-knowledge-brain/scripts/session_close.py --prompt" }]
  }
}
```

### Cursor / Gemini CLI / Codex (手动触发 / manual trigger)

Copy the `obsidian-knowledge-brain/` folder into your platform's skill directory. / 把 `obsidian-knowledge-brain/` 复制到对应平台目录：

| Platform / 平台 | Target directory / 目标目录 |
|----------|-----------------|
| Cursor | `.cursor/skills/obsidian-knowledge-brain/` |
| Gemini CLI | `.gemini/extensions/obsidian-knowledge-brain/` |
| Codex | `.codex/skills/obsidian-knowledge-brain/` |

Replace `.claude/` paths in SKILL.md with your platform's base. Then type commands manually — the Agent reads SKILL.md and executes protocols on your trigger words. See `references/platform-guide.md`. / 把 SKILL.md 中 `.claude/` 替换为对应目录，然后输入触发词手动执行。

---

## Quick Start in Four Words / 四个词上手

| Trigger / 触发词 | What it does / 效果 |
|-----------|------|
| **诊断** / `diagnose` | Scan project, report chaos score, propose a plan — no files touched / 扫描项目，输出混沌度评分和规划，不碰文件 |
| **整理项目** / `bootstrap` | Build `.claude/rules/` + `.claude/projects/` + `.claude/memory/` skeleton / 创建框架骨架 |
| **收尾** / `wrap up` | End of session: save decisions, errors, update project status / 会话结束：保存决策、错误、更新项目状态 |
| **健康检查** / `health check` | Full 7-dimension scan: ceiling, contradictions, orphans, GC / 七维全量扫描 |

**Work normally. / 正常干活。** The skill captures knowledge from your flow — not by interrupting it. / 知识在你工作中被捕获——而不是打断你来问。

---

## Cost / 花费

**Zero monetary cost. / 零费用。** This is a set of markdown templates and Agent protocols — no API calls, no servers, no subscription. 纯 markdown 模板和 Agent 协议——无 API 调用、无服务器、无订阅。

The "cost" is / "花费"的是时间：

- ~5-10 minutes for first bootstrap (Agent reads/writes ~15 files) / 首次播种约 5-10 分钟
- ~2 minutes per session end for "收尾" wrap-up / 每次收尾约 2 分钟
- ~50-200 lines added to your `.claude/` directory per session / 每次会话增加 50-200 行

Token usage: approximately 3,000-8,000 tokens per session for annotation and classification. Comparable to reading a few extra files. / Token 消耗：每次会话约 3,000-8,000 tokens，相当于多读几个文件。

---

## Obsidian Integration (Optional) / Obsidian 集成（可选）

v3.0 stores knowledge as plain `.md` files in `.claude/memory/`. To browse as a knowledge graph: / v3.0 用纯 `.md` 存储知识，要用 Obsidian 浏览知识图谱：

1. Open your project folder as an Obsidian vault / 用 Obsidian 打开项目文件夹
2. The `.claude/` directory becomes a browsable wiki / `.claude/` 目录变成可浏览的 wiki
3. `[[wikilinks]]` between decisions, pitfalls, and rules render as graph edges / 决策、陷阱、规则之间的 `[[双向链接]]` 呈现为图谱边

No plugin needed. The folder-is-vault convention works with any Markdown editor — Obsidian just makes the cross-references visual. / 无需插件。文件夹即 vault 的约定适用于任何 Markdown 编辑器——Obsidian 只是把交叉引用可视化。

---

## What's Inside / 目录结构

```
obsidian-knowledge-brain/
├── SKILL.md                    ← Agent skill definition / 技能定义 (≤200 lines, always loaded)
├── README.md                   ← This file / 本文件
├── LICENSE                     ← MIT
├── description.md              ← Marketplace listing / 技能市场描述 (≤500 chars)
├── templates/                  ← 4 templates for rules, projects, pitfalls, decisions / 4 个模板
│   ├── rule.template.md
│   ├── project.template.md
│   ├── pitfall.template.md
│   └── decision.template.md
├── references/                 ← 10 protocol & seed data files / 10 个协议和种子数据 (each ≤80 lines)
│   ├── quickstart.md           ← 5-minute walkthrough / 5 分钟上手
│   ├── platform-guide.md       ← Cursor/Gemini/Codex setup / 平台适配指南
│   ├── troubleshooting.md      ← Common recovery scenarios / 常见故障排查
│   ├── domain-registry.md      ← Rule domain vocabulary for bootstrap / 规则域注册表
│   ├── error-taxonomy.md       ← Error type vocabulary (50+ types) / 错误分类法
│   ├── root-cause-kb.md        ← Known root cause → symptom lookup / 根因知识库
│   ├── phase-a-bootstrap.md    ← Framework skeleton builder protocol / 框架播种协议
│   ├── t1-session-start.md     ← Session start 5-step protocol / 会话启动协议
│   ├── t2-session-end.md       ← Session end close protocol / 会话结束协议
│   └── t3-periodic-check.md    ← Weekly health check 7-dim scan / 定期健康检查
└── scripts/                    ← 17 Python scripts (v3.0 hook scripts + v2 utilities)
    ├── session_start.py        ← T1 hook: SessionStart briefing / 会话启动简报 (NEW v3.0)
    ├── session_close.py        ← T2 hook: session-end prompt + validator / 收尾协议+验证 (NEW v3.0)
    ├── session_harvester.py    ← Hook transcript harvester / 会话转录收割器
    ├── install.py              ← Cross-platform path setup / 跨平台路径安装
    ├── runner.py               ← Pipeline orchestrator (5-step) / 管道编排器
    ├── analyzer.py             ← Root-cause analysis (keyword + LLM) / 根因分析
    ├── maintainer.py           ← Rule lifecycle + merge detection / 规则维护
    ├── reporter.py             ← Weekly reports + index rebuild / 周报+索引重建
    ├── compiler.py             ← CLAUDE.md index sync / 索引同步
    ├── backup.py               ← JSONL transcript backup / 会话备份
    ├── config.py               ← Configuration loader / 配置加载器
    ├── setup.py                ← Interactive vault setup (v2 legacy) / 交互式安装 (v2 遗留)
    ├── validate_frontmatter.py ← Frontmatter field validation / 元数据字段校验
    ├── link_validator.py       ← Wiki-link integrity checker / 双向链接完整性检查
    ├── score_sessions.py       ← Session scoring utility / 会话评分工具
    ├── reformat_tables.py      ← Table reformatter / 表格格式化
    └── config.example.yaml     ← Sample configuration / 配置示例
```

---

## FAQ / 常见问题

**Q: Does this need Obsidian? / 需要 Obsidian 吗？**
A: No. v3.0 stores everything in `.claude/` inside your project. Obsidian is an optional viewer. / 不需要。v3.0 数据全在项目 `.claude/` 里，Obsidian 只是可选查看器。

**Q: Does it work without Claude Code? / 不用 Claude Code 能用吗？**
A: Yes — Cursor, Gemini CLI, and Codex all work via manual trigger words. See `references/platform-guide.md`. / 能——输触发词手动执行即可。

**Q: How long until it's useful? / 多久见效？**
A: ~3 sessions × ~7 annotations → 20 total → pattern extraction activates. Before that, everything is still stored — just no auto-detection yet. / 约 3 次会话积累 20 条标注后模式提取激活。在此之前知识照常存储，只是还没自动检测规律。

**Q: Does it call external APIs? / 会调用外部 API 吗？**
A: No. All classification is deterministic (MECE rules + heuristic matching). LLM-based pattern extraction is an optional Tier 2 feature gated behind explicit human opt-in. / 不会。全部分类是确定性的（MECE 规则 + 启发式匹配）。LLM 模式提取是可选的 Tier 2 功能，需人工显式激活。

---

## License / 许可证

MIT — use it, modify it, distribute it freely. / MIT — 随意使用、修改、分发。
