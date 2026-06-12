---
version: "1.0.0"
baseline_start: null
weeks: []
---

# 成长指标 / Growth Metrics

> 追踪知识大脑的健康度和成长。每周日自动更新。
> Tracks knowledge brain health and growth. Auto-updated every Sunday.

---

## 核心指标 / Core Metrics

| 周 / Week | 活跃规则 / Active Rules | 观察期规则 / Beta Rules | 提案中 / Proposed | 已归档 / Archived | 决策总数 / Total Decisions | 踩坑总数 / Total Pitfalls | 跨项目关联 / Cross-Project Links | 用户反馈 / User Feedback |
|---|---|---|---|---|---|---|---|---|
| 基线/基线/基线/基线/基线/基线/基线/基线/基线/基线/基线/基线 / Baseline | — | — | — | — | — | — | — | — |

---

## 参考指标 / Reference Metrics

| 周 / Week | Session 数 / Sessions | 平均决策数/session / Avg Decisions | 平均错误数/session / Avg Errors | 错误修复率 / Error Fix Rate | 审批通过率 / Approval Rate | 审批响应时间(天) / Approval Response (days) |
|---|---|---|---|---|---|---|
| 基线/基线 / Baseline | — | — | — | — | — | — |

---

## 指标解释 / Metric Explanations

| 指标 / Metric | 说明 / Explanation | 健康趋势 / Healthy Trend |
|---|---|---|
| **活跃规则 / Active Rules** | 已生效的跨项目规则数 / Number of enforced cross-project rules | 稳步增长，每季度回顾是否有冗余 / Steady growth, quarterly review for redundancy |
| **Beta 规则 / Beta Rules** | 观察期中（30天）的规则 / Rules in 30-day observation period | 有值就说明系统在持续学习 / Non-zero means the system is continuously learning |
| **提案中 / Proposed** | 等待你审批的规则 / Rules waiting for your approval | 理想值 1-5，太多说明你积压了，太少说明系统没发现新模式 / Ideal 1-5: too many means backlog, too few means no new patterns found |
| **决策总数 / Total Decisions** | 所有项目中 AI 标记的决策总数 / Total AI-annotated decisions across all projects | 持续增长 / Continuous growth |
| **踩坑总数 / Total Pitfalls** | 所有项目中遇到的错误总数 / Total errors encountered across all projects | 增长率下降（坑在变少）/ Growth rate declining (fewer new pitfalls) |
| **跨项目关联 / Cross-Project Links** | 项目之间的关联数 / Links between projects | 稳步增长 / Steady growth |
| **错误修复率 / Error Fix Rate** | 已修复的错误 / 总错误 / Resolved errors / Total errors | 趋近 100% |
| **审批通过率 / Approval Rate** | 批准的规则 / 总提案 / Approved rules / Total proposals | 50-80%（太低=AI 提案太差，太高=可能在盲批）/ 50-80% (too low = AI proposals poor, too high = may be rubber-stamping) |
| **审批响应时间 / Approval Response (days)** | 提案生成到你去审批的天数 / Days from proposal to your review | < 7 天 / days |

---

## 基线说明 / Baseline Notes

- `baseline_start` 是你第一次运行 scanner 的日期
- 基线行 / Baseline row：初始化时的快照值 / Snapshot values at initialization
- 之后每周在表里追加一行 / One new row appended per week
- 增长率 / Growth rates 和趋势 / trends 由 reporter 自动计算并写在周报里 / auto-calculated by reporter in weekly report
