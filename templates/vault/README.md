---
vault_version: "1.0.0"
created: "{YYYY-MM-DD}"
projects:
  - project-alpha
  - project-beta
rules:
  active: 0
  beta: 0
  proposed: 0
  archived: 0
last_weekly_report: null
---

# {Vault Name} — AI 知识大脑 / AI Knowledge Brain

> 这是你和 AI 助手共享的知识库。AI 在这里读规则、写记忆、发现模式。你在这里审批 AI 的提案、看周报、纠正错误。
> This is the shared knowledge base between you and your AI assistants. AI reads rules, writes memories, and discovers patterns here. You approve proposals, read weekly reports, and correct mistakes here.

## 这是什么？/ What Is This?

一个 **Obsidian Vault**，记录你和 AI 助手所有对话中的：
- 关键决策（为什么这么做？）
- 踩过的坑（怎么修的？）
- 跨项目规则（"以后所有项目都 X"）
- 每周成长指标（规则数、项目覆盖、修复率）

AI 助手在会话结束时自动写摘要，每周日 Python 脚本自动扫描、聚类、生成周报。

An **Obsidian Vault** that records from all your AI conversations:
- Key decisions (why did we do it this way?)
- Pitfalls encountered (how did we fix them?)
- Cross-project rules ("always X in all projects")
- Weekly growth metrics (rule count, project coverage, fix rate)

AI assistants auto-write summaries at session end. Python scripts auto-scan, cluster, and report every Sunday.

## 文件夹地图 / Folder Map

| 文件夹 / Folder | 谁写 / Who Writes | 干什么 / Purpose |
|---|---|---|
| `00-Rules/` | AI 提案 → **你审批** / AI proposes → You approve | 跨项目硬规则 / Cross-project hard rules |
| `01-Projects/` | **AI 自动写** / AI auto-writes | 每个项目的记忆、决策、踩坑 / Per-project memory, decisions, pitfalls |
| `02-Resources/` | Web Clipper / 你 / AI | 网页保存、提示词、工具文档 / Clippings, prompts, tool docs |
| `03-Maps/` | **脚本自动生成** / Script auto-generates | 主题索引、时间线、项目关联图 / Topic index, timeline, project graph |
| `04-Feedback/` | **脚本自动生成** / Script auto-generates | 周报、错误分类、扫描日志 / Reports, error taxonomy, scan logs |
| `_attachments/` | 你 / AI | 图片、PDF 等附件 / Images, PDFs, etc. |

## AI 助手第一次读这里 / AI First-Read Guide

> **如果你是 AI 助手，这是你该读的第一份文件。**

1. **先读 `00-Rules/`** — 里面是用户定下的硬规则。遵守它们，不要质疑。
2. **再看 `01-Projects/{project}/Memory/decisions.md` 和 `pitfalls.md`** — 了解这个项目做过的决策和踩过的坑。
3. **如果有待审批的规则**（`00-Rules/_inbox/` 里有文件），在开始任务时提醒用户审批。
4. **会话结束时**，输出 `[SESSION_SUMMARY]` 块，写入本项目的 `Memory/sessions/` 目录。
5. **如果你犯了新错误**，在聊天里用 `[ERROR: ...]` 标注，脚本会自动捕获。

> **If you are an AI assistant, this is your first-read file.**

1. **Read `00-Rules/` first** — these are the user's hard rules. Follow them, don't question them.
2. **Then read `01-Projects/{project}/Memory/decisions.md` and `pitfalls.md`** — understand past decisions and pitfalls for this project.
3. **If there are pending approval cards** (files in `00-Rules/_inbox/`), remind the user at session start.
4. **At session end**, output a `[SESSION_SUMMARY]` block and write to this project's `Memory/sessions/` directory.
5. **If you encounter a new error**, annotate with `[ERROR: ...]` in chat — the scanner will auto-capture it.

## 当前状态 / Current State

- **活跃规则 / Active rules**: 0
- **观察期规则（beta）/ Beta rules**: 0
- **待审批提案 / Pending proposals**: 0
- **已归档规则 / Archived rules**: 0
- **项目数 / Projects**: 1 (project-alpha)
- **最近周报 / Last weekly report**: 尚未生成 / Not yet generated

## 快速链接 / Quick Links

- [[用户手册|用户手册 / User Manual]] — 详细使用说明 / Detailed usage guide
- [[04-Feedback/weekly-reports/_TEMPLATE|周报模板 / Weekly Report Template]]
- [[04-Feedback/error-taxonomy|错误分类词典 / Error Taxonomy]]
- [[00-Rules/_TEMPLATE|规则模板 / Rule Template]]
