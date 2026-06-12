# 设计原理与架构决策 / Design Rationale & Architecture Decisions

> 本文档记录了 Obsidian 知识大脑系统的核心设计决策及其背后的"为什么"。
> This document captures core design decisions and the "why" behind them.

---

## 一、为什么选 Obsidian + Markdown？/ 1. Why Obsidian + Markdown?

### 决策 / Decision
用 Obsidian Vault（Markdown 文件 + YAML frontmatter）作为唯一数据源，而不是数据库、REST API、或专用存储格式。

### 不选数据库的理由 / Why Not a Database

| 数据库的问题 / Database Problem | 解释 / Explanation |
|---|---|
| **AI 工具只能通过代码访问** / AI can only access via code | 每次读写都要写 Python/SQL 代码，增加摩擦。Markdown 文件可以直接读写。 |
| **工具锁死** / Tool lock-in | 换了 AI 工具（如从 Claude Code 换到 Codex）就要重写数据库连接代码。Markdown 是通用的。 |
| **人类不可读** / Not human-readable | 你不能用 Obsidian 打开 SQLite 浏览规则。你需要在聊天之外看到和编辑规则。 |
| **版本控制困难** / Version control difficult | Markdown 文件可以直接 `git diff`。数据库需要 dump/restore。 |
| **跨平台脆弱** / Cross-platform fragility | SQLite 在不同 OS 上行为一致但备份/迁移麻烦。文件就是文件。 |

### 不选专用 API 的理由 / Why Not a Custom API
一个中间服务器会增加单点故障。AI 可以直接读写文件系统（这是它和人类共用的界面），不需要在中间加一层 API。

### Markdown 文件的优势 / Markdown Advantages
- **人类直接可读可写** — 你可以在 Obsidian 里打开、编辑、添加笔记
- **AI 直接可读可写** — 所有主流 AI 工具都能读写 Markdown
- **版本控制友好** — `git diff` 清晰显示改了什么
- **简单** — 不需要安装数据库、不需要跑服务、不需要维护 schema migration
- **可移植** — 整个 vault 就是一个文件夹，拷贝到任何地方都能用

### YAML Frontmatter 的角色 / The Role of YAML Frontmatter
Markdown 正文是人类阅读的。YAML frontmatter 是给脚本和 Dataview 读的结构化数据。两条通道互不干扰。

---

## 二、为什么是三层金字塔？/ 2. Why a Three-Layer Pyramid?

### 三层结构 / Three Layers

```
跨项目规则 / Cross-Project Rules     ← 你审批 / You approve
    ↑ 自动晋升 / Auto-promote
项目记忆 / Project Memory            ← AI 自动写 / AI writes
    ↑ 自动摘要 / Auto-summarize
会话记录 / Session Records           ← 原始 JSONL / Raw JSONL
```

### 设计理由 / Rationale

**问题**: 单次对话的知识（"Redis 连接超时，加大连接池"）只在那一刻有价值。如果不提炼，永远是孤岛。
**解法**: 三层提炼管道——任何知识要成为"规则"，必须经过三层验证，缺一不可:

1. **出现次数验证** — 同一个错误在同一个项目出现多次（session 层验证）
2. **跨项目验证** — 同一个错误在多个项目中都出现了（project 层验证）——这才是真正的"跨项目模式"
3. **人类审批** — 你确认这条规则确实值得推广（rule 层验证）

**Anti-pattern 预防**: 没有三层验证，AI 会把一次性的、偶发的错误当成通用规则。比如"今天网络挂了"不代表"永远要离线模式"。

---

## 三、为什么双通道审批？/ 3. Why Dual-Channel Approval?

### 两条审批路径 / Two Approval Paths

| 通道 / Channel | 触发方式 / Trigger | 适合 / Best For |
|---|---|---|
| **Claude 会话内 / In-Chat** | AI 在聊天开始时提醒 `_inbox/` 里有待审批 | 日常、少量审批 / Daily, few proposals |
| **Obsidian 直接操作 / Direct in Obsidian** | 你在 Obsidian 里打开审批卡，手动改 frontmatter 的 `status` | 批量审批、深度修改 / Batch review, deep edits |

### 为什么需要双通道？/ Why Both?

- **聊天内审批快**：AI 提醒 → 你点 Y → 完事。适合 1-2 个提案。
- **Obsidian 审批适合深度思考**：你想仔细读每条证据、修改规则措辞，或者攒了一周的提案一次性处理。
- **同一个文件系统**：不管用哪种方式，改的都是同一个 Markdown 文件。不存在"在聊天里批了但在 Obsidian 里看不到"的问题。

---

## 四、原子写入模式 / 4. Atomic Write Pattern

### 问题 / Problem
脚本在写入文件时如果崩溃（断电、OOM、被 kill），文件可能损坏——写了一半的 YAML、截断的 Markdown。

### 解法 / Solution
所有脚本遵循"原子写入"模式：

```python
# 1. 把新内容写到一个临时文件
with open(target_path + ".tmp", "w", encoding="utf-8") as f:
    yaml.dump(data, f)

# 2. 原子替换（OS 级别的 rename 是原子的）
os.replace(target_path + ".tmp", target_path)
```

`os.replace()` 在 Linux/macOS/Windows 上都是原子操作——要么旧文件还在，要么新文件已经替换完成。永远不存在"半个文件"的状态。

### 备份 / Rollback
每次写操作前，当前文件会被复制到 `04-Feedback/_rollback/{date}/`。保留最近 4 周的备份。

---

## 五、Dry-Run 安全 / 5. Dry-Run Safety

### 问题 / Problem
脚本会写入 vault 的多个目录。如果逻辑有 bug，可能损坏已有的数据。

### 解法 / Solution
所有脚本默认 `--dry-run` 模式：输出会打印到终端（告诉你"将会做什么"），但不会写任何文件。只有加 `--no-dry-run` 或 `--force` 才会真正写入。

在 `runner.py` 中这是由 `SafeFileWriter` 统一控制的，不是每个脚本各自管各自的。

---

## 六、LLM 聚类分层设计 / 6. LLM Clustering Tier Design

### 为什么需要 LLM？/ Why LLM?

基于关键词的匹配可以找出"候选"（比如所有提到 `timeout` 的 session），但无法区分：
- "数据库连接超时" vs "API 请求超时" vs "WebSocket 心跳超时"
- 这三者在 keywords 里可能都是 `timeout`，但根因和修复方法完全不同

### 分层设计 / Tiered Approach

```
Tier 1: 关键词预筛选 / Keyword Pre-Screening
  └─ 用 error-taxonomy.md 的 keywords 字段从 session 中筛选候选 session

Tier 2: LLM 语义聚类 / LLM Semantic Clustering
  └─ 把 Tier 1 的候选发给 LLM，让它按"错误现象 + 根因"聚类

Tier 3: 自动提案生成 / Auto-Proposal Generation
  └─ 对 "N ≥ 3 个项目" 的聚类自动生成审批卡
```

### 为什么分层？/ Why Tiered?

- **成本**：直接送 100 个 session 给 LLM 很贵（可能 50K tokens）。先关键词缩到 10 个候选，再送 LLM，成本降 90%。
- **质量**：关键词筛选保证候选和错误分类相关，减少 LLM 的噪声。
- **可选性**：不配 LLM API key 也能跑 Tier 1（纯关键词模式），只是聚类没那么精细。

---

## 七、版本兼容策略 / 7. Version Compatibility Strategy

### Vault 模板版本 / Vault Template Versioning

- 每个模板的 YAML frontmatter 中包含 `version` 或 `vault_version` 字段
- `setup.py` 在初始化 vault 时记录模板版本到 `config.yaml`
- Scanner 脚本启动时检查 config 中的版本 vs 当前模板版本
- 版本不匹配时 scanner 打印警告但不中断（向前兼容）：
  ```
  ⚠ vault template v1.1 available (you are on v1.0)
     Run: python setup.py --upgrade
  ```

### Frontmatter Schema 演进 / Frontmatter Schema Evolution

- **新增字段 / New fields**: 总是可选的，带默认值。不影响已有 note。
- **移除字段 / Removed fields**: 先标记 deprecated，3 个大版本后才删除。
- **重命名字段 / Renamed fields**: 不做——改为 add + deprecated old。

### 脚本版本 / Script Version

- `heartbeat.md` 中记录 `script_version`
- 周报中会显示版本号
- 如果版本落后超过 2 个小版本，reporter 会在周报里提醒升级

---

## 八、设计反模式 / 8. Design Anti-Patterns (What We Explicitly Avoided)

| 反模式 / Anti-Pattern | 为什么不做 / Why Not |
|---|---|
| **自动应用规则（无审批）** / Auto-apply rules without approval | AI 会自己做主——这正是我们要防止的。规则必须由人类审批。 |
| **用 JSON 存 session** / Storing sessions as JSON | JSON 人类不可读、不易编辑、git diff 困难。Markdown + YAML frontmatter 是更好的选择。 |
| **建一个 Web 界面** / Building a web UI | Obsidian 本身就是一个很好的 UI。再建一个 Web 前端只会增加复杂度。 |
| **实时监控 daemon** / Real-time monitoring daemon | 不需要。每周跑一次够了。知识提炼不是实时需求。 |
| **用 embedding 向量做所有匹配** / All embeddings, all the time | 成本高、调试难、用户无法理解匹配逻辑。关键词 + LLM 的混合方案更透明、更便宜。 |
