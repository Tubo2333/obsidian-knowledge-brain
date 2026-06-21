# Error Taxonomy v3.0 / 错误分类法 v3.0

Seed vocabulary for `[ERROR: type=<value>]` annotations. Agent MUST use values from this taxonomy. Unmatched errors use `type=NEW:<proposed_type>` (新错误类型提案 / new error type proposal).

## Top-Level Categories / 顶层分类

### 1. Network/GFW / 网络/防火墙
`gfw-rst` `timeout` `gfw-block` `proxy-down` `dns-fail`

### 2. R-Environment / R 环境
`install-fail` `bioc-version-mismatch` `dependency-conflict` `segfault-rscript-e` `combat-segfault` `package-not-found`

### 3. Windows-Platform / Windows 平台
`curl-ssl` `path-separator` `file-not-found` `permission-denied` `disk-full` `symlink-issue` `task-scheduler`

### 4. Encoding / 编码
`gbk-utf8-mismatch` `chinese-garbled-docx` `chinese-garbled-csv` `unicode-path` `docx-corrupt`

### 5. API / API 集成
`ssl-error` `http-403` `http-400-param` `rate-limit` `api-timeout` `api-param-wrong`

### 6. Figure-Rendering / 图形渲染
`scale-fill-manual-grey` `ragg-greyscale` `ggsave-drop-color` `cairo-pdf-issue` `svg-font-missing` `heatmap-color`

### 7. Data-Pipeline / 数据管线
`jsonl-parse-error` `rds-version-mismatch` `csv-delimiter` `frontmatter-missing` `frontmatter-invalid-yaml` `data-incomplete` `reference-gap` `data-provenance`

### 8. Agent-Behavior / Agent 行为
`naming-discipline` `compliance-gap` `llm-behavior` `vendor-lockin` `cost-estimate` `knowledge-decay` `llm-api-config` `concurrency-design` `metric-undefined` `design-contradiction`

### 9. Other / 其他
Catch-all (兜底分类). ≥3 occurrences of same NEW type → propose new subcategory or top-level category.

## Extension Protocol / 扩展协议
1. Agent encounters unmatched error → annotate `type=NEW:<kebab-case-proposal>`
2. T3 periodic check scans all NEW entries
3. ≥3 occurrences across ≥2 sessions → merge into existing or promote to new subcategory
4. Human confirms; this file is updated as authoritative seed. Cross-project extensions flow back to skill-package seed via Skill update (§5.5).

## Version History / 版本历史
- v3.0 seed (2026-06-21): Inherited 46 subcategories from v2.0 11-category taxonomy, consolidated into 8 cross-project categories per App C. Added Agent-Behavior category. Registered 5 additional types from v3.0 design-phase pitfall files (`data-provenance`, `llm-api-config`, `concurrency-design`, `metric-undefined`, `design-contradiction`). Dropped 10 v2.0 subcategories as intentionally platform/project-specific (not cross-project general): obsidian (plugin_conflict, vault_corrupt, sync_fail), git-internal (merge_conflict, detached_head, submodule_issue, large_file_push_fail), nodejs toolchain (puppeteer_render_fail, npm_install_fail), shell (git_hook_fail). All dropped types can be reintroduced via `NEW:` extension protocol if encountered in new projects.
