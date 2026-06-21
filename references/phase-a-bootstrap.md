# Phase A · Framework Bootstrap / 框架播种

**Precondition for Phase B**. Diagnose → classify → build skeleton → migrate → validate.

## 1. Diagnose: Chaos Score / 混沌度评分

Score 4 dimensions (0-3 each, total 0-12):

| Dim | 0 | 1 | 2 | 3 |
|-----|---|---|---|---|
| CLAUDE.md completeness | 5 sections present | Missing 1-2 | Missing 3+ | No file |
| rules/ health | ≥8 domains, frontmatter valid | 4-7, partial invalid | 1-3 files | No dir |
| projects/ health | ≥1 file, frontmatter valid | Partial invalid | No valid frontmatter | No dir |
| Top-level dir count | <15 | 15-30 | 30-50 | >50 |

**Action**: 0-3 → skip full bootstrap (reduced legacy audit only). 4-7 → incremental (fill gaps). 8-12 → full bootstrap.

## 2. Legacy Automation Audit / 遗留自动化审计

| Scan Source | Method |
|-------------|--------|
| Active cron/scheduler | Read `.claude/scheduled_tasks.json`, system crontab |
| Hook references | Check `settings.json` hooks → script → write target |
| `.claude/scripts/` | Audit `open('w')` / `write()` calls → target matrix |

**Chaos 0-3**: reduced audit (cron/hook scan only, skip script file-by-file). **Chaos 4-12**: full audit. Output: write-target matrix (写入目标矩阵) → each active automation → target → in v3.0 domain? → keep/shutdown/redirect.

## 3. Classify: Raw Content Tree / 原始内容分类

For each file, per-paragraph parallel labeling (并行标记):

1. Contains MUST/NEVER/DO? → mark `IS_RULE`
2. Describes project identity (paths, status, blockers, data sources, milestones)? → mark `IS_PROJECT`
3. Records past-event lesson (error, decision)? → mark `IS_MEMORY`

Post-label: 1 tag → classify directly. ≥2 tags → split paragraph + cross-reference. 0 tags → leave in place. Original files **move** to `archive/.claude-archive/bootstrap-<YYYY-MM-DD>/`.

## 4. Build Skeleton / 建骨架

Create from skill-package templates (`<skill-root>/templates/`):
- `CLAUDE.md` (≤100 lines: Navigation, Environment, Critical Rules, Rules Index, Project Index)
- `.claude/rules/` — create universal domains from `references/domain-registry.md` + scan project for project-specific domains. Use `templates/rule.template.md` for each.
- `.claude/projects/` (per-project files from `project.template.md`)
- `.claude/memory/` (`pitfalls/` `decisions/` `preferences/` `reference/` + `_phase1_inbox.md`; later: `pitfall.template.md` `decision.template.md`)
- `archive/.claude-archive/` + README.md (explain recovery)

## 5. Validate / 验证

6-item checklist (Agent manual, no script dependency):
1. ✅ CLAUDE.md ≤ 100 lines
2. ✅ All `rules/*.md` YAML frontmatter valid (schema_version, domain, priority, last_triggered, status)
3. ✅ All `projects/*.md` YAML frontmatter valid (schema_version, project, status, updated)
4. ✅ No orphan files (all rules/projects in CLAUDE.md index)
5. ✅ `archive/` contains complete copy of originals
6. ✅ Legacy automation audit complete, write-target matrix populated

All PASS → create `.claude/PHASE_A_COMPLETE` marker with YAML frontmatter fields: `phase: A, status: complete, bootstrap_date: <YYYY-MM-DD>, chaos_score: <0-12>, audit_type: <full|reduced>, validated_by: Agent, schema_version: "3.0"`. Body: `## Validation Results` with per-item PASS/FAIL for all 6 checklist items.

## Idempotency / 幂等性
Check `PHASE_A_COMPLETE` first: status=complete + ≤90 days → skip. >90 days → re-validate all 6 checklist items; all pass → refresh bootstrap_date; any fail → re-diagnose. status=in_progress → re-run all 6 checks from scratch (marker stores no per-item state). Corrupt YAML → re-diagnose. Force re-run → archive old marker first.
