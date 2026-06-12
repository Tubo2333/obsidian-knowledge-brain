# Obsidian Knowledge Brain / Obsidian 知识大脑

> 一个基于 Obsidian Vault 的 AI 知识管理系统。零数据库、零 API、零同步协议——全靠 Markdown 文件系统。
> An Obsidian Vault-based AI knowledge management system. Zero database, zero API, zero sync protocol — just Markdown files.

## 这是什么 / What

你的 Claude Code 聊了几百次天，每次的知识（决策、踩坑、规则）都锁在 JSONL 聊天记录里。换个 AI 工具就全丢了。

这个系统用一个 Obsidian Vault 做"唯一真相源"——所有 AI 读同一个文件夹、写同一种 Markdown。**规则自动提取、周报自动生成、跨项目模式自动发现。**

Your Claude Code sessions contain valuable knowledge — decisions, pitfalls, rules. But they're locked in JSONL chat logs. Switch AI tools and they're gone.

This system uses an Obsidian Vault as the single source of truth. Every AI reads and writes the same Markdown files. **Rules auto-extracted. Weekly reports auto-generated. Cross-project patterns auto-detected.**

## 快速安装 / Quick Install

```bash
git clone https://github.com/YOUR_USERNAME/obsidian-knowledge-brain.git
cd obsidian-knowledge-brain/scripts
pip install -r requirements.txt
python setup.py
```

脚本会问你三个问题 / The script asks three questions:
1. Vault 放哪里？/ Where to put the vault?
2. 项目根在哪？/ Where is your project root?
3. 有哪些项目？/ What projects to track?

然后自动建好一切。/ Then auto-creates everything.

## 怎么用 / How It Works

```
聊天 / Chat → [DECISION]/[ERROR] 标注 → 自动写 session 摘要到 vault
                          ↓
             每周日 / Sunday: Python runner.py
                          ↓
    backup → analyze → maintain → report → compile
                          ↓
         跨项目模式 ≥3 次 → 审批卡 → 你点 Y → 规则生效
```

详细文档 / Full docs:
- `SKILL.md` — AI 技能入口 / AI skill entry
- `references/architecture.md` — 设计原理 / Design rationale
- `references/workflow.md` — 使用流程 / Usage workflow

## 结构 / Structure

```
obsidian-knowledge-brain/
├── SKILL.md                     ← AI skill entry point
├── README.md                    ← This file
├── scripts/                     ← 10 Python scripts (4896 lines)
│   ├── setup.py                 ← One-click vault init
│   ├── runner.py                ← Pipeline orchestrator
│   ├── backup.py / analyzer.py / maintainer.py / reporter.py / compiler.py
│   ├── validate_frontmatter.py / link_validator.py / score_sessions.py
│   └── config.example.yaml
├── templates/vault/             ← 13 vault template files
├── references/                  ← Design docs
└── patches/                     ← CLAUDE.md additions
```

## 依赖 / Requirements

- **Python 3.10+**
- **PyYAML** (`pip install PyYAML`)
- **Obsidian** (optional — vault is plain Markdown, readable by anything)
- **Claude API key** (optional — LLM clustering enhancer; works without it)

## 许可证 / License

MIT
