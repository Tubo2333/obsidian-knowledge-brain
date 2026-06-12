---
session_id: "{PROJECT-S###}"
date: "{YYYY-MM-DD}"
projects: ["{project-alpha}"]
parent_session: null
duration_min: 0
ai_title: "{Brief descriptive title}"
summary_status: "draft"
summary_type: "auto"
tags: []
decisions_made: 0
errors_encountered: 0
rules_triggered: []
new_patterns_flagged: []
---

# {session_id}: {ai_title}

> **日期 / Date**: {YYYY-MM-DD}
> **AI 助手 / AI Assistant**: {model name}
> **时长 / Duration**: ~{N} 分钟 / minutes
> **状态 / Status**: `draft` — 等待 AI 完成全文摘要 / Awaiting full-text summary

---

## 做了什么 / What We Did

{一句话概述 / One-sentence overview}

### 关键任务 / Key Tasks

1. {任务 1 / Task 1}
2. {任务 2 / Task 2}
3. {任务 3 / Task 3}

---

## 决策记录 / Decisions Made

> 格式 / Format: `[DECISION:{PROJECT}-D{##}] 决策内容 / Decision text`

| ID | 决策 / Decision | 上下文 / Context |
|---|---|---|
| {PROJECT}-D{##} | {决策内容 / What we decided} | {为什么做这个决定 / Why we decided this} |

---

## 错误与修复 / Errors & Fixes

> 格式 / Format: `[ERROR:{type}] 错误描述 → 修复方法 / Error description → Fix`

| 类型 / Type | 错误 / Error | 修复 / Fix |
|---|---|---|
| {error_type} | {错误描述 / What went wrong} | {怎么修好的 / How we fixed it} |

---

## 产出的文件 / Files Produced

- `{relative/path/to/file}` — {简短描述 / Brief description}

---

## 下一步 / Next Steps

- [ ] {待办项 1 / TODO 1}
- [ ] {待办项 2 / TODO 2}

---

## AI 自评 / AI Self-Assessment

**任务完成度 / Task completion**: {X}% — {简要评价 / Brief assessment}
**是否引入新坑 / Introduced new pitfalls?**: {是/否 / Yes/No}
**学到的东西 / Lessons learned**: {如果适用 / If applicable}

---

## 用户反馈 / User Feedback

<!-- 用户可在此处添加反馈，或使用 [[../Feedback/]] 模板 / User can add feedback here or use the Feedback template -->

{user feedback or link to feedback note}
