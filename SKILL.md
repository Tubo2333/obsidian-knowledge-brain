---
name: obsidian-knowledge-brain
description: Build an Obsidian vault-based AI shared knowledge brain — a four-layer real-time evolution system where every chat session feeds into automated pattern detection, root-cause analysis, and Agent Memory sync. The brain learns from every conversation, not just counts errors. Use this whenever the user wants to set up AI knowledge management, build a shared brain, create project memory systems, organize cross-session AI learning, or mentions Obsidian vault + AI agent workflow. Also trigger on phrases like "知识管理", "共享大脑", "AI 记忆系统", "跨会话学习", "session 总结", "规则自动提取".
---

# Obsidian Knowledge Brain v2.0 / Obsidian 知识大脑 v2.0

> 不是错题本。是会学习的系统。
> Not an error notebook. A learning system.

## v2.0 核心升级 / What Changed from v1.0

| v1.0 (旧) | v2.0 (新) |
|-----------|-----------|
| 每周日跑一次 scanner | **三层触发**: Stop hook (关窗口) + SessionStart hook (开窗口) + Cron (每天深度扫描) |
| 知识真空期: 关窗口后等 7 天才扫描 | **SessionStart hook**: 开新窗口立刻补收割，上一个窗口的教训秒级可用 |
| 分析 = 数错误次数 | **根因分析**: 找到 WHY，不只是 HOW MANY。提炼一个原则防止所有同类错误 |
| 审批卡片写 "(TBD)" | **具体规则文本**: 每条卡片带可直接使用的规则措辞 |
| 规则只写 CLAUDE.md | **双路径**: CLAUDE.md + Agent Memory (跨 session 即时生效) |
| 扫描后不知道学了什么 | **学习叙事**: 周报第一行告诉你"这周最重要的发现是..." |

## 这是什么 / What Is This

你和 AI 聊了几百次天。每次的决策、踩坑、解决方案——这些知识是最宝贵的。但如果没有系统化管理，它们就在聊天记录里烂掉。

这个系统做一件事：**让 AI 从每一次对话中学习，下次变得更聪明。**

This system does one thing: **makes the AI learn from every conversation, so it gets smarter next time.**

## 四层进化架构 / Four-Layer Evolution Architecture

```
┌──────────────────────────────────────────────────────────┐
│ L1: 即时标注 (Instant Annotation)                          │
│     每次决策 → [DECISION: ...]  每次错误 → [ERROR: ...]     │
│     CLAUDE.md Priority 0 强制执行                          │
│     可靠性: 最高 (事件驱动，不需要等任何东西)                    │
├──────────────────────────────────────────────────────────┤
│ L2: 自动收割 (Auto-Harvest)                               │
│     Stop hook: 关窗口 → 收割当前 transcript → 写 vault       │
│     SessionStart hook: 开窗口 → 扫 48h 漏网 transcript →    │
│     补收割 → Agent Memory 更新 → AI 初始化时已是聪明版         │
│     可靠性: 高 (系统信号 + 双保险)                            │
├──────────────────────────────────────────────────────────┤
│ L3: 深度分析 (Deep Analysis)                               │
│     每天 14:07 cron → 全量扫描 → 根因分析 → 规则维护 → 周报    │
│     不是数错误，是找根因。不是堆规则，是合并泛化。                │
│     可靠性: 中 (电脑得开着)                                   │
├──────────────────────────────────────────────────────────┤
│ L4: 手动收尾 (Manual Sync)                                 │
│     你说 "收尾/整理/sync up" → neat-freak 全量审计           │
│     可靠性: 中 (靠人记得)                                     │
└──────────────────────────────────────────────────────────┘
```

### 实时进化闭环 / The Real-Time Evolution Loop

```
Session 进行中
    ↓ AI 输出 [DECISION:] [ERROR:] (L1 — 实时)
Session 结束
    ↓ Stop hook → session_harvester.py (L2 — 秒级)
    ↓ 提取标注 → 写入 vault → 触发增量扫描
    ↓ 新模式 → 规则注入 Agent Memory
下一个 Session 开始
    ↓ SessionStart hook → 补收割漏网之鱼 (L2 — 秒级)
    ↓ AI 加载 CLAUDE.md + Agent Memory → 已经更聪明
每天 14:07
    ↓ 全量深度扫描 → 根因分析 → 规则合并 → 周报 (L3)
```

## 快速开始 / Quick Start

### 1. 一键初始化 / One-Click Setup

```bash
cd scripts/
python setup.py
```

回答三个问题：vault 放哪、项目根在哪、有哪些项目。自动建好全部目录。

### 2. 配置 CLAUDE.md / Configure CLAUDE.md

把 `patches/CLAUDE.md.patch` 的内容加到你的项目 `CLAUDE.md`。这部分是 **Priority 0 标注规则** —— AI 必须在每次决策和错误时输出结构化标注。这是整个大脑的"感官系统"。

### 3. 配置 Hooks / Configure Hooks

在 `~/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python path/to/scripts/session_harvester.py --mode stop"
      }]
    }],
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python path/to/scripts/session_harvester.py --mode start"
      }]
    }]
  }
}
```

**这两个 hook 是把"被动存储"变成"主动学习"的关键。** Stop hook 在每次关窗口时收割，SessionStart hook 在每次开窗口时补收割漏网之鱼。

### 4. 配定时任务 / Schedule Daily Deep Scan

Claude Code cron (推荐):
```
/cron 7 14 * * * durable=true "cd path/to/scripts && python runner.py --full"
```

### 5. 跑一次 / Run Once

```bash
python runner.py --full
```

## Vault 结构 / Vault Structure

```
vault/
├── README.md
├── 用户手册.md
│
├── 00-Rules/                    ← 你审批的规则
│   ├── RULE-API-001.md          ← 例如: cBioPortal API 规则
│   ├── RULE-FIG-002.md          ← 例如: identity-fill 规则
│   ├── _TEMPLATE.md
│   ├── _inbox/                  ← AI 提案 (待审批)
│   │   └── _rejected/           ← 已拒绝 (30天自动清)
│   └── _archive/                ← 已归档
│
├── 01-Projects/                 ← AI 自动写
│   └── {project}/
│       └── Memory/
│           ├── sessions/        ← 每次对话的结构化总结
│           ├── decisions.md     ← 决策日志
│           └── pitfalls.md      ← 踩坑记录
│
├── 03-Maps/                     ← 自动重建 (每次扫描)
│   ├── topic-index.md           ← 按主题索引
│   └── timeline.md              ← 按时间线
│
└── 04-Feedback/                 ← 自动生成
    ├── weekly-reports/          ← 周报 (含"学到了什么")
    ├── growth-metrics.md        ← 成长指标
    ├── error-taxonomy.md        ← 错误分类词典
    ├── heartbeat.md             ← 扫描心跳
    ├── _raw-sessions/           ← JSONL 备份
    └── _logs/                   ← 运行日志
```

## 脚本说明 / Scripts Reference

| 脚本 | 干什么 | 关键特性 |
|------|--------|----------|
| `session_harvester.py` | **新增 v2.0** — Hook 收割器。`--mode stop` 收割当前 session，`--mode start` 补收割 48h 内漏网 transcript | 原子写入、幂等、离网工作 |
| `runner.py` | 管道编排器。5 步: backup → analyze → maintain → report → compile | UTF-8 强制、lock 防并发 |
| `backup.py` | JSONL transcript → vault + Nutstore 备份。过滤 agent sub-session | 原子复制、增量检测 |
| `analyzer.py` | **v2.0 重写** — 关键词筛选 + LLM 根因分析 + 启发式兜底。输出 learnings (根因+原则+影响+规则建议) | 三层: 关键词→LLM→启发式 |
| `maintainer.py` | **v2.0 重写** — 智能审批卡 (带具体规则文本) + 合并检测 + 规则 reinforce/touch + 过期/晋升/清理 | 不再生成 "(TBD)" |
| `reporter.py` | **v2.0 重写** — 周报 + "学到了什么"叙事 + growth-metrics 真实填充 + 搜索索引 + 主题地图 | 第一行就是最重要的发现 |
| `compiler.py` | **v2.0 新增 Agent Memory 路径** — CLAUDE.md 规则表 + **Agent Memory 同步** (50+ 规则 .md 文件) | 双路径: 项目 + 跨 session |

## 深度分析系统 / Deep Analysis System

### 不是计数器，是学习者 / Not a Counter, a Learner

**v1.0 做的事**: 扫描 session → 发现 "R-package_package_not_found 出现 4 次" → 生成卡片 "(TBD)"

**v2.0 做的事**: 扫描 session → 发现 4 个不同错误 (package_not_found, install_fail, bioc_version_mismatch, dependency_conflict) → 根因分析: **它们都源于同一个根因: R library 在 D:/R/library 不是默认路径** → 一条原则: "安装前先检查 D:/R/library" → 检查已有规则 RULE-R-002 已覆盖 → action=reinforce (强化现有规则，不重复创建) → 周报: "[CONFIRMED] R 包管理规则已验证有效 — 4 次错误, 2 个项目, 全部被正确引导到同一解决方案"

### 根因分析知识库 / Root-Cause Knowledge Base

系统内置了已知根因的知识库 (`ROOT_CAUSE_KB`)，即使没有 LLM API 也能做深度分析:

| 根因 | 原则 | 症状 |
|------|------|------|
| Windows R 4.5.2 颜色渲染 bug | identity-fill + svglite→rsvg 管线 | scale_fill_manual_grey, ragg_greyscale, ggsave_drop_color |
| GFW 网络干扰 | 所有网络调用前检查代理 | ssl_error, gfw_rst, timeout, curl_ssl |
| Windows 路径分隔符 | 始终用 / 不用 \\ | path_separator_mix, file_not_found |
| R 包管理 (非标准路径) | 安装前检查 D:/R/library | install_fail, package_not_found |
| 中文编码 (Windows) | 不用 Python 生成 .docx | gbk_utf8_mismatch, chinese_garbled_docx |
| Rscript -e segfault | 写 .R 文件再 Rscript 执行 | segfault_rscript_e |
| cBioPortal API 参数怪癖 | projection=DETAILED, entrezGeneId=int | http_400_wrong_param |

**LLM 模式**: 当 API key 可用时，LLM 做更精细的根因聚类——能发现知识库里没有的新模式。LLM 是增强，不是必需。

### 规则生命周期 / Rule Lifecycle

```
启发式/LLM 发现模式
    ↓
action=new_rule → 生成审批卡 (带具体规则文本)
action=reinforce → 更新已有规则的 last_triggered
action=merge → 生成合并建议卡 (≥2 条规则重叠)
action=review → 标记需人工审查的未知模式
    ↓
你审批 (在 Obsidian 里或聊天里)
    ↓
beta (30天观察期) → active (正式规则)
    ↓
60天未触发 → 归档 (不是删除，移到 _archive/)
```

## 日常使用场景 / Daily Usage Scenarios

### 场景 1: 正常关窗口 (知识不丢)

你干完活 → 说 "收尾" → AI 输出 [SESSION_SUMMARY] → 你关窗口 → Stop hook 收割 → vault + Agent Memory 更新 → 完成

### 场景 2: 换窗口继续 (知识秒传)

你在窗口 A 做了交接 → X 掉 → 开窗口 B → SessionStart hook 收割窗口 A 的 transcript → Agent Memory 更新 → 窗口 B 的 AI 已经拿到窗口 A 的教训

### 场景 3: 突然关掉 (知识等下次)

你 Ctrl+C 两次强杀 → transcript 在磁盘上 → 下次你开窗口时 SessionStart hook 收割 → 或者等下午 14:07 cron

### 场景 4: 电脑关机过夜 (知识等明天)

你今天干完关机 → transcript 在磁盘 → 明天开机开 Claude Code → SessionStart hook 收割 → 下午 14:07 深度分析

## 注意事项 / Important Notes

- **Python 3.10+**，依赖: PyYAML, requests (LLM 模式)
- **跨平台**: Windows/macOS/Linux
- **不联网也能跑**: LLM 聚类是可选增强，启发式分析离线工作
- **Obsidian 只是查看器**: vault 是纯 Markdown 文件夹，不需要 Obsidian 运行
- **原子写入**: 所有写操作是 .tmp → os.replace，崩溃不损坏文件
- **非破坏性**: 脚本有 --dry-run 模式
- **Idempotent**: 收割器跑两次不会重复写入

## 引用文件 / Bundled Resources

- `references/architecture.md` — v2.0 设计原理和决策记录
- `references/workflow.md` — 详细使用流程和故障排除
- `scripts/` — 所有 Python 脚本 (v2.0 版本)
- `templates/vault/` — Vault 模板文件
- `patches/CLAUDE.md.patch` — CLAUDE.md Priority 0 标注规则补丁
