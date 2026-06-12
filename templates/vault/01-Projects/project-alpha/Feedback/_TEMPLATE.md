---
date: "{YYYY-MM-DD}"
session_id: "{PROJECT-S###}"
task_type: "{debug, feature, refactor, data-analysis, writing, config, other}"
task: "{Brief description of the task}"
verdict: "{good, acceptable, needs-work}"
changes_requested: ""
follow_up_session: null
resolved: false
---

# Feedback: {session_id} — {task}

> **日期 / Date**: {YYYY-MM-DD}
> **任务类型 / Task type**: {task_type}
> **你的评价 / Your verdict**: {verdict}

---

## 任务描述 / Task Description

{AI 做了什么 / What the AI did}

---

## 你的评价 / Your Assessment

### 做得好的 / What Went Well

- 

### 做得不好、需要改进的 / What Needs Improvement

- 

---

## 具体修改要求 / Specific Change Requests

{如果有的话 / If any}

---

## 后续 / Follow-up

- [ ] AI 已修正 / AI has fixed: {是/否}
- [ ] 下次会话跟进 / Follow up in next session: [[sessions/{file}|{session-id}]]

---

## 评价说明 / Verdict Guide

| Verdict | 含义 / Meaning |
|---|---|
| `good` | 完成任务，没有需要改进的地方 / Task done, nothing to improve |
| `acceptable` | 任务完成，有小问题但不影响使用 / Task done, minor issues but usable |
| `needs-work` | 有明显问题，需要修复后才能继续 / Significant issues, needs fix before continuing |
