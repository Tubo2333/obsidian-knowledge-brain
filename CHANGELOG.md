# Changelog / 变更日志

## [4.0.0] — 2026-06-29

### Added / 新增
- **Global Atom Table** (`~/.obsidian-knowledge-brain/atoms.json`): <=20 active atoms, root-cause hash dedup, cross-machine convergence
- **Pre-Action Triggers**: Pre/During/Post three-phase MUST instruction injected into always-loaded file (6 format auto-detection)
- **Cross-Project Promotion**: Same error in >=2 independent projects -> human-confirmed promotion to global table
- **Demotion Lifecycle**: 365d no trigger -> auto-flag -> 90d sync window -> final removal with local keyword return
- **Safe-Merge Sync**: atoms.json into `_global_atoms` section with debounce, .bak protection, and full corruption recovery
- **Concurrent Write Protection**: `atoms.json.lock` with 10-min TTL stale detection
- **Uninstall**: `install.py --uninstall` creates `.uninstalled` marker, removes pre-action, keeps atoms.json
- **New Error Types**: `missed-atom`, `missed-record` (missed-knowledge category)
- **Atom ID**: `{DOMAIN}-{SHA256(root_cause_id + type)[:8]}` -- content-addressable, cross-user dedup
- **scripts/global_atoms.py**: Full atom lifecycle (promote, demote, reactivate, emergency evict, schema validate)
- **scripts/keyword_index.py**: Safe-merge sync, .bak, directory rebuild from rules/ + memory/
- **scripts/pre_action.py**: 6-format detection + instruction injection + removal

### Changed / 变更
- **SKILL.md section 0**: Structural rewrite -- immediate `[ERROR:]` stubs + session-end `[DECISION:]` (dual rule)
- **SKILL.md section 0b**: Sandbox boundary expanded -- declares `~/.obsidian-knowledge-brain/`
- **SKILL.md section 0c**: New -- Known Limitations (9 items) + Platform Capability Matrix
- **install.py**: Complete rewrite (72->285 lines) -- 9-step idempotent, `--uninstall`, platform detection
- **error-taxonomy.md**: Added missed-knowledge category (v3.0->v4.0)
- **domain-registry.md**: Added atom_prefix column for all domains
- **t2-session-end.md**: Added section 2b Cross-Project Promotion Detection (6-step protocol)
- **t3-periodic-check.md**: Added dim-8 Atom Lifecycle scan
- **phase-a-bootstrap.md**: Added section 5 Global Setup (5a-5f), schema_version->4.0
- **README.md**: v3->v4 evolution section, global atom table FAQ, updated directory tree
- **quickstart.md**: Added v4.0 cross-project knowledge section
- **troubleshooting.md**: Added 4 v4.0 troubleshooting scenarios
- **Removed**: `patches/CLAUDE.md.patch` (v2 artifact), `__pycache__/` directories

### Fixed / 修复
- Emergency eviction sort order (two `.sort()` calls now single tuple key)
- `promoted` field validation (now validates ISO date format)
- Lock protection for `mark_demoted()` and `cleanup_demoted()`
- `remove()` now handles all 6 injection formats, not just Markdown blockquote
- Demoted atoms return pointer as local keyword entries
- `_rebuild_from_scan()` now scans `memory/` in addition to `rules/`

---

## [3.0.0] — 2026-06-21

### Added / 新增
- **Zero vault dependency**: Project-local `.claude/` storage, Obsidian optional
- **Agent-native execution**: No Python cron daemon required; Agent reads/writes markdown directly
- **Multi-platform**: Claude Code (full auto), Cursor, Gemini CLI, Codex (manual trigger)
- **Phase A Bootstrap**: Auto-diagnose chaos score -> plan -> build skeleton -> migrate -> validate
- **T1/T2/T3/T4 Protocol**: Session start briefing, session end wrap-up, periodic health check, manual invoke
- **Cold Start Protocol**: 20 annotations + 3 sessions -> active mode
- **MECE Classification**: IS_RULE/IS_PROJECT/IS_MEMORY parallel tagging
- **Keyword Index**: `_keyword_index.json` for grep-based knowledge retrieval
- **install.py**: Cross-platform path setup (`.claude/` -> `.cursor/` etc.)
- **17 Python scripts**: session_start.py, session_close.py, maintainer.py, compiler.py, reporter.py, etc.

### Changed / 变更
- Moved from Obsidian vault (`D:/Obsidian/a/`) to project-local `.claude/`
- All protocols are Agent-executed markdown, not Python pipelines
- Templates generalized from project-specific to universal

---

## [2.0.0] — 2026-05

### Added / 新增
- Obsidian vault-based knowledge storage
- Session transcript harvesting (JSONL -> markdown)
- Rule lifecycle management (11 categories, 46 subcategories)
- [DECISION] and [ERROR] annotation format
- Python cron pipeline: harvester -> analyzer -> compiler -> reporter
- Claude Code hooks (SessionStart, Stop, CronCreate)

### Known Issues / 已知问题 (resolved in v3.0)
- Required Obsidian vault (external dependency)
- Python cron daemon fragile on Windows
- Vault bloat (300+ flat session files, no hierarchy)
- Tight coupling to Claude Code platform
