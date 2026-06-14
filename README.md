# Obsidian Knowledge Brain v2.0 / Obsidian 知识大脑 v2.0

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-2.0.0-orange)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

> **v2.0: 不是错题本。是会学习的系统。**
> 每次对话自动标注 → 关窗口自动收割 → 开窗口秒级同步 → 每天深度根因分析。
> 四层进化架构，AI 真的越用越聪明。

> **v2.0: Not an error notebook. A learning system.**
> Every chat auto-annotated → harvested on window close → synced on window open → deep root-cause analysis daily.
> Four-layer evolution architecture. The AI actually gets smarter.

---

## v2.0 vs v1.0

| | v1.0 | v2.0 |
|---|------|------|
| **触发方式** | 每周日跑一次 scanner | **四层**: Stop hook + SessionStart hook + 每天 cron + 手动收尾 |
| **知识真空** | 关窗口后等 7 天才扫描 | **SessionStart hook**: 开新窗口秒级补收割 |
| **分析深度** | 数错误出现次数 | **根因分析**: 找 WHY，提炼一个原则防止所有同类错误 |
| **审批卡片** | "(TBD — refine during approval)" | 带具体规则文本，可直接使用 |
| **规则存储** | 只写 CLAUDE.md | **双路径**: CLAUDE.md + Agent Memory (50+ 规则 .md 文件) |
| **周报** | "6 patterns found" | "本周最重要的发现: GFW 网络干扰是 4 个错误的共同根因..." |

---

## 四层进化架构 / Four-Layer Evolution

```
L1: 即时标注 → 每次决策/错误立即输出 [DECISION:] [ERROR:] (CLAUDE.md Priority 0)
L2: Hook 收割 → Stop hook (关窗口) + SessionStart hook (开窗口) 双保险
L3: 深度分析 → 每天 14:07 cron 全量根因分析 + 规则维护 + 周报
L4: 手动收尾 → "收尾" 触发 neat-freak 审计
```

**实时闭环 / The Real-Time Loop:**

```
Session 进行 → AI 自动标注 (L1)
    ↓
关窗口 → Stop hook 收割 → vault + Agent Memory (L2, <2s)
    ↓
开新窗口 → SessionStart hook 补收割漏网之鱼 → Agent Memory 更新 (L2, <2s)
    ↓
AI 初始化 → 加载 CLAUDE.md + 最新 Agent Memory → 已更聪明
    ↓
每天 14:07 → 全量深度扫描 → 根因分析 → 规则合并 → 周报 (L3)
```

---

## 快速安装 / Quick Install

```bash
git clone https://github.com/YOUR_USERNAME/obsidian-knowledge-brain.git
cd obsidian-knowledge-brain/scripts
pip install -r requirements.txt   # PyYAML + requests (LLM mode optional)
python setup.py
```

脚本问三个问题，自动建好一切。

**然后必须做两件事**:
1. 把 `patches/CLAUDE.md.patch` 的内容加到你的 `CLAUDE.md`（这是 L1 — AI 的"感官系统"）
2. 在 `~/.claude/settings.json` 配好 Stop + SessionStart hook（这是 L2 — 自动收割）

```json
{
  "hooks": {
    "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "python path/to/scripts/session_harvester.py --mode stop"}]}],
    "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "python path/to/scripts/session_harvester.py --mode start"}]}]
  }
}
```

**最后配定时任务**:
```
/cron 7 14 * * * durable=true "cd path/to/scripts && python runner.py --full"
```

---

## 深度分析系统 / Deep Analysis System

### 不是计数器，是学习者

**v1.0**: 扫描 → "R-package_package_not_found 出现 4 次" → 卡片 "(TBD)"

**v2.0**: 扫描 → 发现 4 个不同错误 (package_not_found, install_fail, bioc_version_mismatch, dependency_conflict) → **根因分析: 它们都源于 R library 在 D:/R/library 不是默认路径** → 一条原则 → 检查已有规则已覆盖 → reinforce (不重复创建) → 周报: "[CONFIRMED] R 包管理规则已验证有效"

### 三层分析 / Three-Tier Analysis

```
Tier 1: 启发式知识库 (ROOT_CAUSE_KB) — 离线工作，覆盖已知根因
Tier 2: LLM 深度分析 — 发现新模式 (可选，需要 API key)
Tier 3: 人工审查 — 标记未知模式供人审核
```

---

## 实际效果 / What You'll See

### 周报第一行就是最重要的发现

```markdown
## 这周学到了什么 / What We Learned

[CONFIRMED] GFW network interference — 5 existing rules validated:
  RULE-GIT-001 (6 errors, 3 projects), RULE-WIN-002, RULE-R-002...
```

### 审批卡片带具体规则，不是 "(TBD)"

```markdown
# Proposed Rule: RULE-API-001

## Root Cause
cBioPortal API has non-standard parameter requirements

## Principle
Always use projection=DETAILED, entrezGeneId=<int> for methylation,
always client-side filter geneList results

## Rule Text
1. All cBioPortal requests MUST include projection=DETAILED
2. Methylation endpoints use entrezGeneId=<int> NOT geneList=<str>
3. geneList filter MAY be silently ignored — always client-side filter
4. PanCan Atlas methylation is often empty — fall back to legacy TCGA
```

---

## 为什么不用... / Why Not Just Use...

| 方案 | 问题 |
|------|------|
| **纯 CLAUDE.md** | 单文件膨胀、无自动发现跨项目模式、无时间线/主题索引 |
| **数据库** | 需要 schema 维护、AI 不能直接读写、Obsidian 打不开 |
| **Notion/Confluence** | API 限流、需联网、知识锁在 SaaS、不跨 AI 工具 |
| **纯 Agent Memory** | 只对当前 AI 有效。换工具不认。Markdown vault 任何工具都能读 |
| **v1.0 (纯周扫描)** | 知识真空 7 天、分析只数数不找根因、卡片写 "(TBD)" |

---

## 目录结构 / What's Inside

```
obsidian-knowledge-brain/
├── SKILL.md                         ← AI 技能定义 (v2.0)
├── README.md                        ← 本文件 / This file (v2.0)
│
├── scripts/                         ← 11 个 Python 脚本
│   ├── setup.py                     ← 一键初始化
│   ├── session_harvester.py         ← Hook 收割器 (v2.0 新增)
│   ├── runner.py                    ← 管道编排 (5 步)
│   ├── backup.py                    ← JSONL 备份 + Nutstore
│   ├── analyzer.py                  ← 根因分析 (v2.0 重写)
│   ├── maintainer.py                ← 智能卡片 + 合并检测 (v2.0 重写)
│   ├── reporter.py                  ← 周报 + 学习叙事 (v2.0 重写)
│   ├── compiler.py                  ← CLAUDE.md + Agent Memory (v2.0)
│   ├── config.py / config.example.yaml
│   └── requirements.txt             ← PyYAML + requests
│
├── references/                      ← 深入文档 (v2.0)
│   ├── architecture.md              ← 8 个设计决策 + Anti-Patterns
│   └── workflow.md                  ← 四层工作流 + Hook 配置 + 管道
│
├── templates/vault/                 ← Vault 模板
└── patches/CLAUDE.md.patch         ← Priority 0 标注规则 (v2.0)
```

---

## 常见问题 / FAQ

**Q: 离网能用吗？/ Works offline?**
A: 完全离网工作。启发式根因分析不需要网络。LLM 深度分析是可选的增强。

**Q: 必须装 Obsidian？**
A: 不必须。Vault 是纯 Markdown 文件夹，任何编辑器都能看。Obsidian 提供更好的可视化。

**Q: 漏扫了怎么办？**
A: runner.py 启动时自动检测上次扫描时间。超过 7 天自动切换全量模式补跑。

**Q: 会改坏文件吗？**
A: 所有写操作是原子写入 (.tmp → os.replace)。崩溃不损坏原文件。有 `--dry-run` 预览模式。

---

## 许可证 / License

MIT — 随便用、改、分发。
