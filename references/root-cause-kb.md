# Root Cause KB / 根因知识库 v4.0

Seed lookup for Tier 1 heuristic matching. Symptom keywords → `root_cause_id` (根因ID).

## Matching Logic / 匹配逻辑

**≥2 keyword hits = match** (high confidence). 1 hit = low confidence, Agent reads full pitfall to verify. 0 hits = Tier 1 miss, escalates to review queue. This is deterministic: grep-able keywords, count-and-threshold, no ML.

## Lookup Table / 检索表

| root_cause_id / 根因ID | Symptom Keywords / 症状关键词 | error_type / 错误类型 | Pitfall / 陷阱文件 |
|---|---|---|---|
| `rc-win-r-color` | `scale_fill_manual`, `#7F7F7F grey`, `identity-fill` | `scale-fill-manual-grey` | *pending migration / 待迁移* |
| `rc-gfw-rst` | `TCP RST`, `fetch-pack disconnect`, `GFW reset` | `gfw-rst` | *pending migration / 待迁移* |
| `rc-chinese-encoding` | `python-docx garbled`, `Chinese mojibake`, `GBK UTF-8 mismatch` | `chinese-garbled-docx` | *pending migration / 待迁移* |
| `rc-combat-segfault` | `sva::ComBat segfault`, `zero-variance genes batch` | `combat-segfault` | *pending migration / 待迁移* |
| `rc-rscript-e-segfault` | `Rscript -e segfault`, `inline R command crash` | `segfault-rscript-e` | *pending migration / 待迁移* |
| `rc-cbio-projection` | `cBioPortal SUMMARY`, `hugoGeneSymbol "?"` | `api-param-wrong` | *pending migration / 待迁移* |
| `rc-curl-ssl-win` | `curl: (35) schannel`, `--ssl-no-revoke missing` | `curl-ssl` | *pending migration / 待迁移* |
| `rc-git-gfw-block` | `git clone blocked GFW`, `zip-download bypass` | `gfw-block` | *pending migration / 待迁移* |
| `rc-jsonlite-autosimplify` | `jsonlite::fromJSON auto-simplify`, `nested list→data.frame` | `data-incomplete` | *pending migration / 待迁移* |
| `rc-thinking-budget-unset` | `thinking token exhaustion`, `budget not configured` | `llm-api-config` | `deepseek-thinking-token-exhaustion.md` |
| `rc-incremental-layer-conflict` | `design contradiction`, `incremental layers conflict` | `design-contradiction` | `design-contradiction-incremental-layers.md` |
| `rc-figure-wrong-json` | `figure data-source mismatch`, `wrong JSON input` | `data-provenance` | `figure-data-source-mismatch.md` |
| `rc-no-write-serialization` | `concurrent write race`, `no serialization guard` | `concurrency-design` | `no-concurrent-write-protection.md` |
| `rc-uncomputable-metric` | `recall denominator undefined`, `uncomputable metric` | `metric-undefined` | `uncomputable-recall-metric.md` |
| `rc-naming-leak` | `internal codename leaks`, `project slug external` | `naming-discipline` | `internal-codenames-leak-external.md` |

## Entry Format / 条目格式

Each entry maps to a `memory/pitfalls/<slug>.md` with full Symptoms/Root Cause/Resolution. The KB is a fast lookup index — for details, follow the pitfall link.

Entries marked *pending migration* are v2.0-validated patterns awaiting pitfall file creation during §8.2 batch migration. **Agent behavior on match**: if Tier 1 matches a *pending migration* entry, create the pitfall file from `templates/pitfall.template.md` using the known `root_cause_id` and `error_type` from this table. Fill Symptoms from annotation context. Mark `status: active`.

## Expansion Protocol / 扩展协议
1. Tier 1 misses → `root_cause_id` left empty in new pitfall
2. Same pattern recurs ≥3 sessions across ≥2 projects → Agent proposes new KB entry
3. Human confirms → appended to table → this file updated as authoritative seed

## Version History / 版本历史
- v3.0 seed (2026-06-21): 15 entries — 9 from v2.0 patterns (pending pitfall migration) + 6 from v3.0 design-phase pitfall files with verified frontmatter
