# Domain Registry / 规则域注册表

Minimum universal domain set for Phase A bootstrap. Each domain maps to `rules/<domain>.md` created from `templates/rule.template.md`.

## Universal Domains / 通用域 (always created)

| Domain | atom_prefix | Priority | Description |
|--------|-------------|----------|-------------|
| `governance` | `GOV` | 1 | Project-wide MUST/NEVER rules, instruction priority / 项目治理 |
| `environment` | `ENV` | 2 | Platform-specific constraints (OS, paths, proxy, encoding) / 环境约束 |
| `git` | `GIT` | 3 | Version control operations, branch strategy, commit policy / 版本控制 |
| `knowledge` | `KNW` | 1 | THIS framework's meta-rules — how the knowledge system operates / 元规则 |

## Project-Specific Domains / 项目特定域 (Agent proposes based on project content)

**Scan targets** (in priority order): 1. `CLAUDE.md` — read for project description and technology stack. 2. Package manifests at project root (`package.json`, `requirements.txt`, `DESCRIPTION`, `Cargo.toml`, etc.). 3. Source file extensions in top 2 directory levels (`.py`, `.R`, `.js`, `.ts`, `.go`, etc.). 4. `README.md` for human-facing project description. Propose domains based on the combined signal. List proposals to user for confirmation before creating files. Minimum 1, suggested maximum 8.

| If project contains... | Propose domain... | atom_prefix |
|------------------------|-------------------|-------------|
| Python/R/JS code with external APIs | `api` | `API` |
| Data processing pipelines | `data-pipeline` | `DAT` |
| Figures, charts, visualization | `figures` | `FIG` |
| Chinese/Unicode text output | `encoding` | `ZH` |
| Patent or legal documents | `patent` | `PAT` |
| Security-sensitive operations | `security` | `SEC` |
| CI/CD or testing infrastructure | `ci-cd` | `CICD` |
| Frontend/UI code | `frontend` | `UI` |

> Unregistered `root_cause_id` → `atom_prefix = "GEN"`. / 未注册的 root_cause_id → atom_prefix = "GEN"。

Agent: list proposed domains to user, get confirmation, then create. Total domains = 4 universal + N project-specific. Phase Detection §1's ">=8" threshold is a guideline for mature projects, not a hard requirement for greenfield ones.
