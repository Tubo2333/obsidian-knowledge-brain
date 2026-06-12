---
status: "proposed"
proposed: "{YYYY-MM-DD}"
proposed_by: "scanner"
confidence_auto: 0.0
one_liner: "{One-line description of the proposed rule}"
evidence:
  pattern: "{error_pattern_keyword}"
  across_projects: ["{project-alpha}", "{project-beta}"]
  occurrences: 0
  sessions: []
affected_projects: ["{project-alpha}", "{project-beta}"]
priority: "medium"
skip_count: 0
skip_until: 0
review_deadline: "{YYYY-MM-DD}"
approved_by: null
approved_at: null
target_rule_id: null
---

# 审批卡 / Approval Card: {one_liner}

> **状态 / Status**: `proposed` — 等待审批 / Awaiting review
> **截止日期 / Review deadline**: {YYYY-MM-DD}（7 天后 / 7 days from proposal）

---

## AI 提案 / AI Proposal

**建议规则 / Proposed rule**: {one_liner}

**理由 / Rationale**:
{Why the scanner thinks this should become a rule. Include the cross-project evidence.}

**自动置信度 / Auto-confidence**: {0.0-1.0} — {解释：基于跨项目数、出现次数、错误严重度等 / Explanation: based on cross-project count, occurrence count, error severity, etc.}

---

## 证据 / Evidence

| 项目 / Project | Session | 上下文 / Context |
|---|---|---|
| {project-alpha} | [[01-Projects/project-alpha/Memory/sessions/{file}\|{session-id}]] | {brief context} |
| {project-beta} | [[01-Projects/project-beta/Memory/sessions/{file}\|{session-id}]] | {brief context} |

---

## 你的选择 / Your Decision

| 选项 / Option | 含义 / Meaning | 结果 / Result |
|---|---|---|
| **[Y] 批准 / Approve** | 这条规则成立 / This rule is valid | 生成规则文件 → beta 30 天 → active |
| **[N] 拒绝 / Reject** | 不成立或不需要 / Not valid or not needed | 移到 _rejected/，30 天后自动清理 |
| **[M] 修改 / Modify** | 方向对但内容要改 / Direction is right, content needs revision | 告诉 AI 怎么改 → 重新提案 |
| **[S] 跳过 / Skip** | 不急着决定 / Not urgent | 再触发 skip_until 次后重新提醒 / Remind after N more triggers |

---

## 日志 / Log

| 日期 / Date | 操作 / Action | 备注 / Notes |
|---|---|---|
| {YYYY-MM-DD} | proposed | 由 scanner 自动提案 / Auto-proposed by scanner |
