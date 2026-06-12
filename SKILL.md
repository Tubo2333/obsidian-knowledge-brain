---
name: obsidian-knowledge-brain
description: Build an Obsidian vault-based AI shared knowledge brain — a dual-channel approval system where Claude and the user maintain project memory, cross-project rules, and weekly automated pattern detection via Python scanner scripts. Use this whenever the user wants to set up AI knowledge management, build a shared brain, create project memory systems, organize cross-session AI learning, or mentions Obsidian vault + AI agent workflow. Also trigger on phrases like "知识管理", "共享大脑", "AI 记忆系统", "跨会话学习", "session 总结", "规则自动提取".
---

# Obsidian Knowledge Brain / Obsidian 知识大脑

> 一个基于 Obsidian Vault 的 AI 知识管理系统。双通道审批、三层知识金字塔、每周自动扫描。
> An Obsidian Vault-based AI knowledge management system. Dual-channel approval, three-layer knowledge pyramid, weekly automated scanning.

## 这是什么 / What Is This

你和 AI 聊了几百次天，每次的知识都锁在聊天记录里，下次换一个 AI 工具就全丢了。这个系统用一个 Obsidian Vault 作为"唯一真相源"——所有 AI 工具读同一个文件夹、写同一种 Markdown 格式，规则、决策、踩坑记录全在里面，永不丢失。

This system uses an Obsidian Vault as the single source of truth. Every AI tool reads and writes the same Markdown files. Rules, decisions, and pitfalls are permanently stored and auto-maintained.

## 核心架构 / Core Architecture

```
聊天 / Chat Session
  │
  ├─ 会话中 / During: Claude 输出 [DECISION:...] 和 [ERROR:...] 标注
  │
  ├─ 会话尾 / End: Claude 输出 [SESSION_SUMMARY] → 写入 vault 草稿
  │
  └─ 每周日 / Sunday: Python runner.py 自动运行
       ├── backup.py     → 备份聊天记录到 vault
       ├── analyzer.py   → 扫描所有 session，发现跨项目错误模式
       ├── maintainer.py → 跨项目模式 ≥3 次 → 自动生成审批卡
       ├── reporter.py   → 生成周报 + 刷新主题索引 + 时间线
       └── compiler.py   → 同步规则到 CLAUDE.md
```

### 三层知识金字塔 / Three-Layer Knowledge Pyramid

```
跨项目规则 / Cross-Project Rules     ← 00-Rules/ （你审批）
    ↑
项目记忆 / Project Memory            ← 01-Projects/ （AI 自动写）
    ↑
会话记录 / Session Records           ← JSONL → vault sessions/
```

## 快速开始 / Quick Start

### 1. 一键初始化 / One-Click Setup

```bash
cd scripts/
python setup.py
```

脚本会问你三个问题 / The script asks three questions:
- Vault 放哪里？/ Where to put the vault? (e.g. `~/ObsidianBrain/`)
- 项目根在哪？/ Where is your project root? (where CLAUDE.md lives)
- 有哪些项目？/ What projects do you have? (e.g. `web-app, data-pipeline, ml-experiments`)

然后自动建好全部目录、复制模板、生成配置文件。/ Then auto-creates all directories, copies templates, generates config.

### 2. 配置 CLAUDE.md / Configure CLAUDE.md

把 `patches/CLAUDE.md.patch` 的内容加到你的项目 `CLAUDE.md` 里。加了三个东西 / Adds three things:
- `[DECISION]` / `[ERROR]` 标注规则 / annotation rules
- `[SESSION_SUMMARY]` 块格式 / block format
- `COMPILED:RULES` / `COMPILED:PROJECTS` 标记（compiler 自动填充）/ markers (auto-populated by compiler)

### 3. 跑一次 / Run Once

```bash
cd scripts/
python runner.py --dry-run   # 预览 / Preview
python runner.py             # 正式运行 / Full run
```

### 4. 配定时任务 / Schedule It

**Linux/macOS (cron):**
```cron
0 15 * * 0 cd /path/to/scripts && python runner.py
```

**Windows (Task Scheduler):**
```cmd
schtasks /create /tn "ObsidianBrain-WeeklyScan" /tr "python C:\path\to\scripts\runner.py" /sc weekly /d SUN /st 15:00
```

## Vault 结构 / Vault Structure

```
vault/
├── README.md                    ← AI 入口 / AI entry point
├── 用户手册.md                   ← 你的说明书 / Your manual
│
├── 00-Rules/                    ← 🔒 你审批 / You approve
│   ├── _TEMPLATE.md             ← 规则模板 / Rule template
│   ├── _inbox/                  ← AI 提案 / AI proposals
│   │   ├── _TEMPLATE.md         ← 审批卡模板 / Approval card template
│   │   └── _rejected/           ← 已拒绝 / Rejected (30天后自动清)
│   └── _archive/                ← 已归档规则 / Archived rules
│
├── 01-Projects/                 ← 🤖 AI 自动写 / AI writes
│   └── {project}/
│       ├── Memory/
│       │   ├── sessions/        ← 每次聊天的纪要 / Per-session summaries
│       │   ├── decisions.md     ← 关键决策日志 / Decision log
│       │   ├── pitfalls.md      ← 踩坑记录 / Pitfall log
│       │   └── cross-project-links.md ← 跨项目关联 / Cross-project links
│       └── Feedback/            ← 👤 你的反馈 / Your feedback
│
├── 02-Resources/                ← 📥 Web Clipper 自动存 / Auto-saved
│   ├── articles/
│   ├── tool-docs/
│   ├── prompts/
│   └── templates/
│
├── 03-Maps/                     ← 🗺️ 每周自动重建 / Weekly auto-rebuilt
│   ├── topic-index.md           ← 按主题索引 / Browse by topic
│   ├── timeline.md              ← 按时间线 / Browse by timeline
│   └── project-graph.md         ← 项目关联图 / Project relationship graph
│
├── 04-Feedback/                 ← 🔄 脚本自动生成 / Script auto-generates
│   ├── weekly-reports/          ← {YYYY-Www}.md 周报
│   ├── growth-metrics.md        ← 成长指标 / Growth metrics
│   ├── error-taxonomy.md        ← 错误分类词典 / Error taxonomy
│   ├── heartbeat.md             ← 扫描心跳 / Scanner heartbeat
│   ├── _raw-sessions/           ← JSONL 备份
│   ├── _rollback/               ← 回滚备份
│   └── _logs/                   ← 运行日志
│
└── _attachments/                ← 图片、PDF
```

## 脚本说明 / Scripts Reference

| 脚本 / Script | 干什么 / What |
|--------------|--------------|
| `setup.py` | 一键初始化 vault / One-click vault initialization |
| `runner.py` | 管道编排器 / Pipeline orchestrator |
| `backup.py` | JSONL 会话备份 → vault / Backup sessions to vault |
| `analyzer.py` | 关键词筛选 + LLM 语义聚类 / Keyword screening + LLM clustering |
| `maintainer.py` | 审批卡生成 + 规则过期/晋升/清理 / Approval cards + rule lifecycle |
| `reporter.py` | 周报 + 指标 + 地图重建 + 心跳 / Reports + metrics + maps + heartbeat |
| `compiler.py` | 00-Rules → CLAUDE.md 编译 / Compile rules to CLAUDE.md |
| `validate_frontmatter.py` | YAML frontmatter 校验 / Validate frontmatter |
| `link_validator.py` | Wiki-link 完整性检查 / Check link integrity |
| `score_sessions.py` | 3D 评分：从历史 session 选最有价值的做深度摘要 / Score sessions for migration |

## 日常使用流程 / Daily Workflow

### 会话结束时 / At Session End

Claude 自动输出：
```
[SESSION_SUMMARY]
projects: [project-alpha]
primary: project-alpha
decisions:
  - id: ALPHA-D01
    text: "决定使用 Redis 替代文件缓存"
    context: "文件缓存在多实例部署时不一致"
errors:
  - type: "redis_connection_timeout"
    resolution: "增加连接池大小到 20"
summary: "完成了用户认证模块的重构，从文件缓存迁移到 Redis。"
[/SESSION_SUMMARY]
```

然后自动写入 vault 草稿。/ Then auto-writes draft to vault.

### 每周日 / Every Sunday

Runner 自动运行 → 发现跨项目模式 → 生成审批卡 → 下次你开 Claude 时提醒审批。

### 审批规则 / Approving Rules

Claude 会话开始时 / At session start:
```
⏳ 1 rule pending approval:
📌 redis_connection_timeout across 3 projects (5 occurrences)
[Y] 批准/Approve  [N] 拒绝/Reject  [M] 修改/Modify  [S] 跳过/Skip
```

你点 Y → 规则进入 beta（30 天后自动转正）。/ Approve → rule enters beta (auto-promotes after 30 days).

## 进阶：历史 Session 迁移 / Advanced: Historical Migration

如果你已经有很多 Claude Code 聊天记录想导入：

```bash
python score_sessions.py   # 3D 评分，选出最有价值的 20 个
# 确认要深度摘要的 Top 15
# 对每个选中的 session 手动或批量生成深度摘要
python runner.py --full     # 全量扫描一次
```

评分维度 / Scoring dimensions:
- **决策密度 / Decision density** = 决策数 / 助手消息数
- **错误密度 / Error density** = 错误数 / 助手消息数
- **项目覆盖 / Project coverage** = 会话覆盖了还没代表的项目 → 加分

## 自定义 / Customization

### 错误分类 / Error Taxonomy

编辑 `04-Feedback/error-taxonomy.md` 的 YAML frontmatter，换成你自己项目里的错误类型。模板里给了一套通用分类（R-plotting, python-encoding, api-network 等），你可以删、改、加。

### 主题检测 / Topic Detection

编辑 `config.yaml` 里的 `topic_map` 字段，把脚本里的标签和你的项目主题对应起来。每周日 reporter 重建主题索引时自动用。

## 注意事项 / Important Notes

- **Python 3.10+**，唯一依赖 PyYAML（`pip install PyYAML`）
- **跨平台**：Windows/macOS/Linux 都支持
- **LLM 聚类可选**：有 API key 配了就启用语义聚类；没有也能跑关键词模式
- **非破坏性**：脚本默认 `--dry-run` 不修改文件，确认没问题再正式跑
- **回滚安全**：所有写操作都是原子写入（.tmp → rename），崩溃不损坏文件

## 引用文件 / Bundled Resources

- `references/architecture.md` — 设计原理和决策记录 / Design rationale & decisions
- `references/workflow.md` — 详细使用流程和故障排除 / Detailed workflow & troubleshooting
- `scripts/` — 所有 Python 脚本 / All Python scripts
- `templates/vault/` — Vault 模板文件 / Vault template files
- `patches/CLAUDE.md.patch` — 添加到 CLAUDE.md 的内容 / Content to add to CLAUDE.md
