# T3 · Periodic Health Check / 定期健康检查

**Recommended**. Trigger: L1 cron (每周) | L2 T1 detects `last_check` > 7 days | L3 user口令 "健康检查" / "health check".
(All paths relative to `$PROJECT_ROOT/.claude/` unless qualified. / 以下路径除特别说明外均相对于 `$PROJECT_ROOT/.claude/`。)

## Concurrent Write Guard / 并发写入保护
**First**: check `.session_active` exists. YES → Agent session active → **skip this T3** (avoid read/write race / 避免读写竞争). NO → proceed. If skipped >14 days, T1 L2 fallback reminds user.

## 7-Dimension Scan / 七维扫描

| Dim | Scan | Frequency | Logic |
|-----|------|-----------|-------|
| 1 | **Hard ceiling (硬上限)** | Weekly | Check `rules/*.md` ≤80 lines, `projects/*.md` ≤60, root `CLAUDE.md` ≤100, `references/*.md` ≤60. Flag violators. Trace write source (modification time, git diff, cron logs) to determine if legacy automation injection (遗留自动化注入). |
| 2 | **Rule contradiction (规则矛盾)** | Weekly | Search for conflicting MUST/NEVER pairs across rules/. |
| 3 | **Orphan detection (孤立检测)** | Weekly | Files in rules/ projects/ memory/ but NOT indexed in CLAUDE.md. |
| 4 | **GC suggestions (归档建议)** | Weekly | Rules priority 1-5 not triggered in 180 days → suggest archive. Priority 6-10 → 365 days. |
| 5 | **Pattern extraction (模式提取)** | Weekly (if new annotations) | ≥20 new annotations since last run → Tier 1 heuristic match against `references/root-cause-kb.md`. If `total_annotations >= 20 AND mode: active` in cold-start counter → also check Tier 2 activation gate. Unmatched annotations → Tier 3 human review queue (人工审查队列). |
| 6 | **Index rebuild (索引重建)** | Weekly | Rebuild `_keyword_index.json` from filesystem. |
| 7 | **Legacy automation back-pressure (遗留自动化反向压力)** | Monthly (weekly if active) | Scan CLAUDE.md for `<!-- COMPILED:RULES_START -->` blocks → flag as legacy injection. Compare COMPILED entry count vs `rules/` file count. |

## Per-Dimension Idempotency / 分维度幂等性
Per-dimension independent timestamps in `HEALTH_REPORT.md`. Dims 1-4+6: skip if `dim_1_4_6_last_check` < 7 days. Dim 5: skip if `last_pattern_extraction` < 7 days OR no new annotations. Dim 7: skip if `dim_7_last_check` < 30 days (upgrade to weekly if active back-pressure).

## Tier 2 Activation Gate / Tier 2 激活门控
All 3 conditions required (默认 OFF / default OFF):
1. Past 30 days: Tier 1 miss rate > 20% AND total annotations ≥ 10
2. Human explicit opt-in (人工确认激活)
3. API available + token budget ≤5,000 tokens per run

Auto-degrade if / 自动降级条件:
- API unavailable → Tier 2 off, Tier 1 + Tier 3 continue (继续工作)
- 3 consecutive rejected clusters → Tier 2 paused 30 days (暂停30天)
- Token budget exhausted → pause this month, reset next month (本月暂停，下月重置)

## Output / 输出
- `HEALTH_REPORT.md` (overwrite): violations, GC suggestions, ROI (`stored/N retrieved/N hit_rate% cost_estimate`), learning narrative (学习叙事), per-dimension `last_check` timestamps
- `_keyword_index.json` (updated)
- If continuous 30 days `hit_rate = 0` → auto-degrade to cold-start mode (只存储不提取)

## Failure Modes / 失败模式
- Cron missed → T1 L2 lazy check catches staleness
- `.session_active` present → skip; T1 L2 falls back if >14 days
- T1/T3 race window (极短竞争窗口): T1 steps 1-4 are read-only; concurrent T3 reads are safe; race window < 1 sec; accepted limitation (接受为已知限制)

## Platform Notes / 平台说明
- **Claude Code**: `CronCreate` or system cron → `maintainer.py --health-check` (7-dim scan + report). Per-dimension timestamps in `HEALTH_REPORT.md` enable partial re-runs
- **No-cron fallback (无cron降级)**: T1 L2 lazy check only (compares `HEALTH_REPORT.md` timestamp, warns if >7 days). Manual trigger via L3 user口令
