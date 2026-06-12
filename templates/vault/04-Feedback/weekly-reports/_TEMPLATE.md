---
week: "{YYYY}-W{ww}"
date: "{YYYY-MM-DD}"
scan_status: "ok"
sessions_scanned: 0
sessions_total: 0
scan_duration_sec: 0.0
errors_during_scan: 0
new_patterns_detected: 0
new_rules_proposed: 0
rules_awaiting_approval: 0
rules_approved_this_week: 0
rules_archived_this_week: 0
heartbeat_ok: true
---

# 周报 / Weekly Report — Week {ww}, {YYYY}

> 自动生成于 / Auto-generated at: {YYYY-MM-DD} {HH}:{MM}
> 扫描耗时 / Scan duration: {N} 秒 / seconds

---

## 一、扫描概览 / 1. Scan Overview

| 指标 / Metric | 本周 / This Week | 上周 / Last Week | 变化 / Change |
|---|---|---|---|
| 扫描 session 数 / Sessions scanned | {N} | — | — |
| Session 总数 / Total sessions | {N} | — | — |
| 新发现的错误模式 / New patterns detected | {N} | — | — |
| 新提案的规则 / New rules proposed | {N} | — | — |
| 待审批规则 / Rules awaiting approval | {N} | — | — |
| 本周审批的规则 / Rules approved this week | {N} | — | — |
| 本周归档的规则 / Rules archived this week | {N} | — | — |
| 扫描错误 / Scan errors | {N} | — | — |

---

## 二、新增错误模式 / 2. New Patterns Detected

{如果没有新增模式 / If no new patterns}
> 本周无新增跨项目错误模式。
> No new cross-project error patterns detected this week.

{如果有新增模式 / If new patterns detected:}
### {pattern_name}
- **类型 / Type**: {error_type}
- **影响项目 / Affected projects**: {project-alpha}, {project-beta}
- **出现次数 / Occurrences**: {N}
- **首次出现 / First seen**: {YYYY-MM-DD}
- **已生成审批卡 / Approval card generated**: [[00-Rules/_inbox/{file}|{PROPOSAL-ID}]]

---

## 三、规则动态 / 3. Rule Activity

### 本周审批 / Approved This Week

| 规则 / Rule | 类型 / Type | 审批时间 / Approved At | 状态 / Status |
|---|---|---|---|
| — | — | — | — |

### 本周归档 / Archived This Week

| 规则 / Rule | 归档原因 / Reason | 活跃天数 / Days Active |
|---|---|---|
| — | — | — |

---

## 四、跨项目热点 / 4. Cross-Project Hotspots

{热点图：哪些错误类型跨了最多项目 / Hotspot map: which error types span the most projects}

| 错误类型 / Error Type | 影响项目数 / Projects Affected | 总出现次数 / Total Occurrences |
|---|---|---|
| — | — | — |

---

## 五、项目健康 / 5. Project Health

| 项目 / Project | 新决策 / New Decisions | 新踩坑 / New Pitfalls | 待反馈 / Pending Feedback | 健康度 / Health |
|---|---|---|---|---|
| {project-alpha} | {N} | {N} | {N} | — |
| {project-beta} | {N} | {N} | {N} | — |

> 健康度 / Health: `优秀/Great` (坑下降) / `一般/OK` (持平) / `关注/Watch` (坑上升)

---

## 六、元健康 / 6. Meta Health

- **扫描器心跳 / Scanner heartbeat**: {正常/OK | 异常/Error}
- **备份完整性 / Backup integrity**: {正常/OK | 异常/Error}
- **LLM 聚类（如启用）/ LLM clustering (if enabled)**: {状态 / Status}
- **磁盘使用 / Disk usage**: {N} MB

---

## 七、AI 建议 / 7. AI Recommendations

{基于本周数据，AI 给用户的建议。如：哪些规则该复审了、哪些项目需要关注。}
{Based on this week's data, AI recommendations for the user. E.g., which rules to review, which projects need attention.}

- {建议 1 / Recommendation 1}
- {建议 2 / Recommendation 2}

---

## 八、您的反馈 / 8. Your Feedback

<!-- 你可以在下面写本周的感想、对 AI 的建议、对系统的调整要求等 / Add your thoughts, suggestions for AI, system adjustment requests below -->

_
