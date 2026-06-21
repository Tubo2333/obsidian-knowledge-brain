# Domain Registry / 规则域注册表

Minimum universal domain set for Phase A bootstrap. Each domain maps to `rules/<domain>.md` created from `templates/rule.template.md`.

## Universal Domains / 通用域 (always created)

| Domain | Priority | Description |
|--------|----------|-------------|
| `governance` | 1 | Project-wide MUST/NEVER rules, instruction priority / 项目治理 |
| `environment` | 2 | Platform-specific constraints (OS, paths, proxy, encoding) / 环境约束 |
| `git` | 3 | Version control operations, branch strategy, commit policy / 版本控制 |
| `knowledge` | 1 | THIS framework's meta-rules — how the knowledge system operates / 元规则 |

## Project-Specific Domains / 项目特定域 (Agent proposes based on project content)

**Scan targets** (in priority order): 1. `CLAUDE.md` — read for project description and technology stack. 2. Package manifests at project root (`package.json`, `requirements.txt`, `DESCRIPTION`, `Cargo.toml`, etc.). 3. Source file extensions in top 2 directory levels (`.py`, `.R`, `.js`, `.ts`, `.go`, etc.). 4. `README.md` for human-facing project description. Propose domains based on the combined signal. List proposals to user for confirmation before creating files. Minimum 1, suggested maximum 8.

| If project contains... | Propose domain... |
|------------------------|-------------------|
| Python/R/JS code with external APIs | `api` |
| Data processing pipelines | `data-pipeline` |
| Figures, charts, visualization | `figures` |
| Chinese/Unicode text output | `encoding` |
| Patent or legal documents | `patent` |
| Security-sensitive operations | `security` |
| CI/CD or testing infrastructure | `ci-cd` |
| Frontend/UI code | `frontend` |

Agent: list proposed domains to user, get confirmation, then create. Total domains = 4 universal + N project-specific. Phase Detection §1's ">=8" threshold is a guideline for mature projects, not a hard requirement for greenfield ones.
