---
schema_version: "3.0"
domain: <domain-slug>           # 规则域 / Domain (e.g., api, git, figures, governance)
priority: <1-10>                # 优先级 / Priority: 1-5=operational, 6-10=domain
last_triggered: <YYYY-MM-DD>    # 最近触发日期 / Last triggered
status: active                  # active | quarantine | deprecated
description: <one-line>         # 单行描述 / One-line description
trigger: <condition>            # 触发条件 / Trigger condition (可选 / optional)
---

# <Rule Title / 规则标题>

## Core Constraints / 核心约束
<!-- MUST/NEVER/DO behavioral constraints / 行为约束 -->

## Rationale / 理由
<!-- Why this rule exists / 为什么需要这条规则 -->

## Procedure / 流程
<!-- Steps to follow: 1. <step> 2. <step> / 操作步骤 -->

## Pitfalls / 陷阱
<!-- What happens when this rule is violated / 违反此规则会导致什么问题 -->

## See Also / 参见
- rules/<other-domain>.md
