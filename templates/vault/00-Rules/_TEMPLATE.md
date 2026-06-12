---
rule_id: "{RULE-XXX}"
title: "{Rule Title}"
status: "beta"
category: "{category}"
applies_to: ["{project-alpha}", "{project-beta}"]
source: "{approval card path or manual}"
trigger_count: 0
prevention_count: 0
created: "{YYYY-MM-DD}"
last_triggered: null
expires: "{YYYY-MM-DD}"
anchor: "## Rule: {Title}"
---

# Rule: {Rule Title}

> **状态 / Status**: `beta` — 观察期，30 天后无异议自动转 `active` / Beta period, auto-promotes to active after 30 days if no objection.
> **适用范围 / Applies to**: {project-alpha}, {project-beta}
> **触发次数 / Trigger count**: 0 | **预防次数 / Prevention count**: 0
> **创建日期 / Created**: {YYYY-MM-DD} | **到期日期 / Expires**: {YYYY-MM-DD}

---

## 规则内容 / Rule Content

{一句话描述这条规则的核心要求。用"必须"/"禁止"/"建议"开头。}
{One-sentence description of the core requirement. Start with "MUST"/"MUST NOT"/"SHOULD".}

## 为什么 / Why

{这条规则要解决什么问题？它防止了什么错误？}
{What problem does this rule solve? What error does it prevent?}

## 触发条件 / Trigger Conditions

- {条件 1 / Condition 1}
- {条件 2 / Condition 2}

## 例外 / Exceptions

- {例外 1 / Exception 1}：{什么情况下可以不遵守 / When this rule can be ignored}
- {例外 2 / Exception 2}

## 关联 / Related

- **原始提案 / Original proposal**: [[00-Rules/_inbox/{PROPOSAL-ID}|提案 {PROPOSAL-ID}]]
- **触发案例 / Trigger cases**:
  - [[01-Projects/project-alpha/Memory/sessions/{session-file}|{session-id}]] — {brief context}
  - [[01-Projects/project-beta/Memory/sessions/{session-file}|{session-id}]] — {brief context}

---

## 生命周期 / Lifecycle

```
beta (30天/30 days) → active (永久/permanent) → archived (手动/manual)
```

- **beta → active**: 30 天后无用户拒绝 / Auto-promotes after 30 days without user rejection
- **active → archived**: 用户手动归档 / User manually archives
- **beta → archived**: 用户在观察期内拒绝 / User rejects during beta period
