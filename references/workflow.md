# 详细使用流程 / Detailed Workflow

> 本文档详细描述 Obsidian 知识大脑系统的日常使用流程和故障排除。
> This document describes the detailed daily workflow and troubleshooting for the Obsidian Knowledge Brain system.

---

## 一、四层进化工作流 / 1. Four-Layer Evolution Workflow

v2.0 用四层独立的触发机制取代了 v1.0 的单一周扫描。每层有不同的可靠性保证，互相补偿。

```
L1: 即时标注 → 每次决策/错误立即输出标注 (CLAUDE.md Priority 0)
L2: Hook 收割 → Stop hook + SessionStart hook 双保险 (session_harvester.py)
L3: 深度分析 → 每天 14:07 cron 全量扫描 (runner.py --full)
L4: 手动收尾 → "收尾"触发 neat-freak 审计
```

关键改进: **SessionStart hook 消除了"知识真空期"** — 关旧窗口开新窗口后，新 AI 加载时就拿到上个窗口的教训。

## 二、会话标注流程 / 2. Session Annotation Flow

### 2.1 v2.0 简化格式 / v2.0 Simplified Format

v2.0 使用**内联格式**（inline），不再使用块格式（block）。AI 更可能遵守，harvester 更容易解析。

#### [DECISION] — 每次技术决策后 (单行内联)

```
[DECISION: <一句话总结> | context: <为什么>]
```

**何时**: 选库、选算法、选架构、配置值、命名约定、workaround——任何技术选择。

#### [ERROR] — 每次解决错误后 (单行内联)

```
[ERROR: type=<来自error-taxonomy> | resolution=<怎么修的>]
```

**何时**: 遇到并解决任何错误——stack trace、测试失败、构建失败、API 拒绝、数据格式问题。

#### [SESSION_SUMMARY] — 会话结束时 (块格式)

触发词: "好的/谢谢/完成/收尾/bye/整理"。格式见 CLAUDE.md patch。

---

## 三、Hook 配置 / 3. Hook Configuration

v2.0 的关键基础设施。需要在 `~/.claude/settings.json` 中配置两个 hook：

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

| Hook | 触发时机 | 收割什么 | 耗时 |
|------|---------|---------|------|
| Stop | 关窗口/退出 Claude Code | 当前 session 的 transcript | <2s |
| SessionStart | 开窗口/启动 Claude Code | 48h 内未收割的 transcript | <2s |

**为什么需要两个 hook？** Stop hook 在关窗口时触发——但如果用 Ctrl+C 两次或 kill -9，hook 可能不触发。SessionStart hook 在下次开窗口时补收割所有漏网之鱼。两个 hook 互为保险。

## 四、深度扫描管道 / 4. Deep Scanner Pipeline (v2.0)

### 4.1 管道概览 / Pipeline Overview

```
runner.py --full (每天 14:07 cron)
  │
  ├── Step 1: backup.py
  │     └── 将新增 JSONL transcript 备份到 vault + Nutstore
  │
  ├── Step 2: analyzer.py  ← v2.0 重写
  │     ├── 关键词筛选所有 session 摘要
  │     ├── (可选) LLM 根因分析: 找 WHY，不只是 HOW MANY
  │     ├── 启发式知识库 (ROOT_CAUSE_KB): 离线也能做根因分析
  │     └── 输出: learnings (根因 + 原则 + 影响 + 规则建议) + summary
  │
  ├── Step 3: maintainer.py  ← v2.0 重写
  │     ├── 从 learnings 生成审批卡 (带具体规则文本，不再 "(TBD)")
  │     ├── 合并检测: ≥2 规则重叠 → 建议合并
  │     ├── 规则 reinforce: 更新已有规则的 last_triggered
  │     └── 规则生命周期: beta→active (30天) + 过期归档 (60天)
  │
  ├── Step 4: reporter.py  ← v2.0 重写
  │     ├── 生成周报: 第一行就是最重要的发现
  │     ├── growth-metrics 真实填充 (不再全是 0)
  │     ├── 更新 heartbeat.md
  │     └── 重建 03-Maps/ (topic-index, timeline)
  │
  └── Step 5: compiler.py  ← v2.0 新增 Agent Memory 路径
        ├── CLAUDE.md: 替换 COMPILED:RULES + COMPILED:PROJECTS 块
        ├── Agent Memory: 50+ 规则 .md 文件 → 下次 session 即加载
        └── MEMORY.md index 重建
```

### 2.2 各步骤详解 / Step Details

#### Step 1: backup.py
- 输入：你的 Claude Code 聊天记录（JSONL 文件）
- 处理：过滤出本周新增的，复制到 `04-Feedback/_raw-sessions/`
- 命名：`{YYYY-MM-DD}_{session_uuid}.jsonl`
- 去重：已存在的文件跳过

#### Step 2: analyzer.py
- 扫描范围：`01-Projects/*/Memory/sessions/` 中尚未标记 `processed` 的 session
- 关键词筛选：遍历 error-taxonomy 的 `keywords`，做文本包含匹配
- LLM 聚类（可选）：将关键词筛选出的候选发给 LLM，要求按"错误现象 + 根因"聚类
- 输出：每个聚类的 pattern name、涉及 session 列表、置信度

#### Step 3: maintainer.py
- **审批卡生成条件**：同一 pattern 出现在 ≥ 3 个不同项目
- **规则晋升**：`beta` 状态 + `created` 距今 ≥ 30 天 → `active`
- **过期清理**：`_rejected/` 中的文件 `proposed` 距今 ≥ 30 天 → 删除
- **跳过逻辑**：`skip_count < skip_until` → 不生成审批卡

#### Step 4: reporter.py
- 周报模板：`04-Feedback/weekly-reports/_TEMPLATE.md`
- 指标更新：在 `growth-metrics.md` YAML 的 `weeks` 列表中追加本周数据
- 地图重建：
  - `topic-index.md`：按错误分类/主题索引所有 session
  - `timeline.md`：按时间线排列所有决策和错误
  - `project-graph.md`：项目间关联的可视化（Mermaid 图）
- 心跳更新：`heartbeat.md` 更新 `last_scan` 和 `scan_status`

#### Step 5: compiler.py
- 只替换 `<!-- COMPILED:RULES_START -->` ... `<!-- COMPILED:RULES_END -->` 之间的内容
- 只替换 `<!-- COMPILED:PROJECTS_START -->` ... `<!-- COMPILED:PROJECTS_END -->` 之间的内容
- **不会修改** CLAUDE.md 的其他部分
- 如果没有找到标记块 → 报错提示用户先加 patch

---

## 三、规则审批流程 / 3. Rule Approval Flow

### 3.1 方法 A：聊天内审批 / In-Chat Approval

1. Claude 会话开始时自动检查 `00-Rules/_inbox/` 是否有 `status: proposed` 的文件
2. 如果有，列出待审批列表
3. 你选择 Y/N/M/S
4. AI 更新审批卡的 frontmatter 并执行相应操作

**操作含义**:
- **[Y]**: `approved_by=用户名`, `approved_at=日期`, `target_rule_id` 指向新生成的规则文件 → 脚本在下一次扫描时生成规则文件
- **[N]**: 移动文件到 `_inbox/_rejected/`
- **[M]**: `status=modification_requested` → AI 按你的指示修改后重新提案
- **[S]**: `skip_count += 1`, `skip_until += N`（默认 N=3，即再跳过 3 次触发）→ 暂时不提醒

### 3.2 方法 B：Obsidian 直接审批 / Direct Obsidian Approval

1. 在 Obsidian 中打开 `00-Rules/_inbox/` 里的审批卡
2. 手动修改 YAML frontmatter：
   - 批准：添加 `approved_by: "{你的名字}"`, `approved_at: "{日期}"`
   - 拒绝：移动文件到 `_rejected/`
3. 下次扫描时，`maintainer.py` 会检测到变更并执行相应操作

### 3.3 规则生命周期 / Rule Lifecycle

```
proposed (审批卡) / proposed (approval card)
  │
  ├─ [Y] 批准 → beta (30天观察期 / 30-day observation)
  │     │
  │     ├─ 30天后 / After 30 days: auto → active
  │     │     │
  │     │     └─ 用户手动 / User manually: active → archived
  │     │
  │     └─ 用户在观察期内拒绝 / User rejects during beta: beta → archived
  │
  ├─ [N] 拒绝 → rejected (30天后自动清理 / auto-cleaned after 30 days)
  │
  ├─ [M] 修改 → modification_requested → (修改后) proposed / back to proposed
  │
  └─ [S] 跳过 → proposed (延迟提醒 / delayed reminder)
```

---

## 四、历史 Session 迁移指南 / 4. Historical Session Migration Guide

### 4.1 适用场景 / When to Migrate

你已经有几十甚至上百次 AI 对话记录，想把这些历史知识导入到新系统中。

### 4.2 迁移步骤 / Migration Steps

```bash
# 步骤1: 评分——选出最有价值的 session
cd {vault_path}/scripts/
python score_sessions.py --input {path/to/chat/logs/} --top 20

# 步骤2: 审阅——确认要深度摘要的 Top N
# 脚本会输出一个列表，你手动选择要摘要的 session

# 步骤3: 批量生成深度摘要
# 对于每个选中的 session，AI 读取原始对话并生成完整的 session 摘要
# 写入: 01-Projects/{project}/Memory/sessions/{PROJECT}-S{NNN}.md

# 步骤4: 全量扫描一次
python runner.py --full
```

### 4.3 评分维度 / Scoring Dimensions

| 维度 / Dimension | 权重 / Weight | 说明 / Description |
|---|---|---|
| **决策密度 / Decision density** | 40% | 决策数 / 助手消息数。值越高说明这个 session 产出了重要决策。 |
| **错误密度 / Error density** | 35% | 错误数 / 助手消息数。坑多的 session 值得记录。 |
| **项目覆盖 / Project coverage** | 25% | 会话涉及了还没被其他 session 代表的子项目 → 加分。避免全部高分 session 都来自同一个子领域。 |

### 4.4 注意事项 / Notes

- **不要全量迁移**——100 个 session 全做深度摘要会花几个小时，而且很多 session 没有多少价值。选 Top 15-20 个就够了。
- **评分是启发式的**——机器学习项目 vs 前端项目的决策密度天然不同。不要求绝对公平，只求选出最有代表性的。
- **迁移后首次扫描要 `--full`**——否则 scanner 会认为这些 session 是"旧数据"而跳过。

---

## 五、常见问题排查 / 5. Troubleshooting

### Scanner 不跑了 / Scanner Not Running

1. 检查 `heartbeat.md` 的 `scan_status` — 如果是 `error`，查看 `errors` 列表
2. 检查 `04-Feedback/_logs/` 中的最新日志文件
3. 手动跑一次看报错：`python runner.py --dry-run`
4. 检查 cron/schtasks 是否还在生效

### 审批卡不生成 / Approval Cards Not Generating

1. 确认 `maintainer.py` 的最小阈值：同一 pattern 必须出现在 ≥ 3 个项目中
2. 检查 `_inbox/` 里是否已经有类似提案（去重逻辑）
3. 检查 `skip_until` 是否还没到
4. 手动跑 `python runner.py --step analyze --verbose` 看中间输出

### CLAUDE.md 没更新 / CLAUDE.md Not Updating

1. 确认 CLAUDE.md 里有 `<!-- COMPILED:RULES_START -->` 和 `<!-- COMPILED:RULES_END -->` 标记
2. 确认两个标记是成对的——缺一个 compiler 会报错
3. 手动跑 `python runner.py --step compile --verbose` 看具体错误
4. 确认 `00-Rules/` 里有 `status: active` 或 `status: beta` 的规则文件

### 中文乱码 / Chinese Garbled

1. 所有脚本强制使用 `encoding="utf-8"` 读写文件
2. 如果你在用 Windows Terminal，确认它支持 UTF-8
3. 如果 Obsidian 里中文显示异常，检查 Obsidian 设置 → 文件与链接 → 默认编码是否为 UTF-8

### Wiki-link 断了 / Broken Wiki-links

```bash
python link_validator.py
```
会扫描所有 `[[...]]` 链接，报告死链。常见原因：文件被移动、文件名拼写错误。

---

## 六、如何自定义 / 6. How to Customize

### 6.1 添加新的错误分类 / Adding Error Categories

编辑 `04-Feedback/error-taxonomy.md`，在 YAML frontmatter 的 `categories` 列表中添加新条目：

```yaml
- name: "docker-deploy"
  description: "Docker 部署相关错误 / Docker deployment errors"
  keywords:
    - "docker"
    - "container"
    - "image"
    - "compose"
    - "registry"
    - "volume"
    - "network"
    - "port mapping"
    - "env file"
  subcategories:
    - name: "build-failure"
      description: "镜像构建失败 / Image build failure"
      examples:
        - "Docker build context too large"
        - "Multi-stage build cache miss"
    - name: "orchestration"
      description: "编排问题：compose、swarm、k8s"
      examples:
        - "Docker compose service dependency order wrong"
```

修改后，下次运行 `analyzer.py` 会自动使用新的 keywords。

### 6.2 自定义主题检测 / Custom Topic Detection

编辑 `config.yaml`：

```yaml
topic_map:
  "api-network": ["api", "http", "network", "request"],
  "data-processing": ["pandas", "spark", "etl", "pipeline"],
  "ml-training": ["model", "training", "gpu", "cuda", "overfit"],
  "frontend-ui": ["react", "css", "component", "layout"],
  "devops": ["ci", "cd", "deploy", "monitor"],
  # ...
```

每个分类的 value 是关键词列表。`reporter.py` 在重建 `topic-index.md` 时用这些词做自动归类和标签。

### 6.3 添加新项目 / Adding a New Project

```bash
cd {vault_path}/scripts/
python setup.py --add-project {project-name}
```

这会：
1. 在 `01-Projects/` 下创建新项目目录
2. 复制所有 Memory 和 Feedback 模板
3. 更新 `config.yaml` 的项目列表
4. 更新 CLAUDE.md 的 `COMPILED:PROJECTS` 块（下次扫描时生效）

---

## 七、安全与隐私 / 7. Security & Privacy

- **Vault 是你的本地文件**——不经过任何服务器
- **LLM 聚类是可选的**——不配 API key 就不会有任何数据离开你的电脑
- **如果配了 LLM API key**：只有关键词筛选出的少量 session 片段会被发送。不发送完整对话记录。
- **不要把 vault 直接放在云同步盘里**跑扫描——并发写入可能导致冲突。要么 vault 在本地 + 定期备份到云端，要么用 Obsidian Sync / Git。
