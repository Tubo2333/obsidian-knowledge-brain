"""Step 5: Compile 00-Rules -> CLAUDE.md marked blocks + Agent Memory.
Also provides --sync-index to auto-generate Rules/Project Index tables in
root CLAUDE.md from .claude/rules/ and .claude/projects/ filesystem.

sync-indices is ADDITIVE: it reads existing table rows first and only ADDS new
filesystem entries not already in the table. It never overwrites hand-curated
descriptions or trigger conditions.
"""
import os
import sys
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

# ── Part A constants & functions — SHUTDOWN per v3.0 §8.4 L1 (2026-06-21) ──
# Removed: RULES_START/END, PROJECTS_START/END constants
# Removed: compile_rules_section(), compile_projects_section(), replace_block()
# Removed: count_frontmatter_items(), get_latest_session() (Part A helpers)
# Part C (sync_indices) continues below — independent of Part A.


def _get_project_root():
    """Detect project root from script location or CWD."""
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir.parent.parent
    if (candidate / "CLAUDE.md").exists() and (candidate / ".claude").exists():
        return candidate
    cwd = Path.cwd().resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "CLAUDE.md").exists() and (p / ".claude").exists():
            return p
    return cwd

_PROJECT_ROOT = _get_project_root()
CLAUDE_MD = str(_PROJECT_ROOT / "CLAUDE.md")
RULES_DIR = str(_PROJECT_ROOT / ".claude" / "rules")
PROJECTS_DIR = str(_PROJECT_ROOT / ".claude" / "projects")
MEMORY_DIR = str(Path.home() / ".claude" / "projects" / f"d--{_PROJECT_ROOT.name.replace(':', '-')}" / "memory")
MEMORY_INDEX = os.path.join(MEMORY_DIR, "MEMORY.md") if os.path.exists(MEMORY_DIR) else ""

# Priority-1 domains are always loaded; others use a domain-derived trigger.
# This map is the FALLBACK when frontmatter has no description/trigger field.
_TRIGGER_MAP = {
    "governance": "Always", "knowledge": "Always",
    "figures": "R/ggplot code, figure tasks",
    "api": "External API calls, data fetching",
    "r-ecosystem": "R scripts",
    "windows": "System calls, curl, shell",
    "chinese": "DOCX/Word output",
    "git": "Git operations, network",
    "patent": "Patent documents",
}

def run(cfg, dry_run=False, step_results=None):
    vault = cfg['vault_path']
    claude_md_path = cfg.get('claude_md_path', CLAUDE_MD)
    results = {"rules_compiled": 0, "projects_compiled": 0, "dirty": False,
               "memory_rules_written": 0, "memory_index_updated": False,
               "index_rules_synced": 0, "index_projects_synced": 0}

    # ── Part A: CLAUDE.md compilation — SHUTDOWN per v3.0 §8.4 L1 ──
    # v2.0 compiler.py Part A injected Obsidian-vault rules/projects tables into
    # CLAUDE.md via COMPILED markers. v3.0 manages rules/ and projects/ directly
    # from .claude/rules/ and .claude/projects/ filesystem. Part A removed
    # 2026-06-21. Part C (sync_indices) continues to maintain the compact index
    # tables from the v3.0 authoritative sources.

    # ── Part B: Agent Memory sync ──
    try:
        mem_result = sync_to_agent_memory(vault, dry_run)
        results.update(mem_result)
    except Exception as e:
        results["memory_error"] = str(e)

    # ── Part C: Sync root CLAUDE.md index tables from .claude/{rules,projects}/ ──
    try:
        idx_result = sync_indices(claude_md_path, dry_run=dry_run)
        results.update(idx_result)
    except Exception as e:
        results["index_sync_error"] = str(e)

    return results


# ── Agent Memory Sync ────────────────────────────────────────
def sync_to_agent_memory(vault, dry_run):
    """Write new/updated rules to Agent Memory so they load next session.
    Rules marked 'active' or 'beta' in 00-Rules/ get a memory file.
    """
    rules_dir = os.path.join(vault, '00-Rules')
    if not os.path.exists(rules_dir):
        return {"memory_rules_written": 0}

    written = 0
    updated_index = False

    for f in sorted(os.listdir(rules_dir)):
        if not f.endswith('.md') or f.startswith('_'):
            continue

        fp = os.path.join(rules_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                rule_content = fh.read()
            fm_parts = rule_content.split('---', 2)
            if len(fm_parts) < 3:
                continue
            fm = yaml.safe_load(fm_parts[1])
        except Exception:
            continue

        status = fm.get('status', '')
        if status not in ('active', 'beta'):
            continue

        rule_id = fm.get('rule_id', f.replace('.md', ''))
        title = fm.get('title', rule_id)
        category = fm.get('category', 'unknown')
        applies_to = fm.get('applies_to', [])

        # Generate memory slug
        slug = rule_id.lower().replace('_', '-')

        # Build memory file content
        memory_md = f"""---
name: {slug}
description: {title} — {category}
metadata:
  type: reference
  rule_id: {rule_id}
  status: {status}
  applies_to: {applies_to}
  compiled_at: {datetime.now().isoformat()}
---

# {title}

Rule ID: `{rule_id}`
Category: {category}
Applies to: {', '.join(applies_to)}
Status: {status}

## Rule Content

{fm_parts[2].strip()[:1000]}
"""

        mem_path = os.path.join(MEMORY_DIR, f"{slug}.md")

        # Check if existing memory needs update
        should_write = True
        if os.path.exists(mem_path):
            try:
                with open(mem_path, 'r', encoding='utf-8') as fh:
                    existing = fh.read()
                if existing.strip() == memory_md.strip():
                    should_write = False  # No change
            except Exception:
                pass

        if should_write and not dry_run:
            try:
                tmp = mem_path + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as fh:
                    fh.write(memory_md)
                os.replace(tmp, mem_path)
                written += 1
            except Exception as e:
                print(f"    WARNING: Cannot write memory {slug}: {e}")

    # Update MEMORY.md index if new rules were written
    if written > 0 and not dry_run:
        try:
            rebuild_memory_index()
            updated_index = True
        except Exception as e:
            print(f"    WARNING: Cannot rebuild memory index: {e}")

    return {"memory_rules_written": written, "memory_index_updated": updated_index}


def rebuild_memory_index():
    """Rebuild MEMORY.md index from all memory files."""
    entries = []
    for f in sorted(os.listdir(MEMORY_DIR)):
        if not f.endswith('.md') or f == 'MEMORY.md' or f.startswith('DEPRECATED'):
            continue
        fp = os.path.join(MEMORY_DIR, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm_parts = content.split('---', 2)
            if len(fm_parts) < 3:
                continue
            fm = yaml.safe_load(fm_parts[1])
            name = fm.get('name', f.replace('.md', ''))
            description = fm.get('description', '')
            entries.append((name, description))
        except Exception:
            continue

    lines = []
    for name, desc in sorted(entries):
        lines.append(f"- [{name}]({name}.md) — {desc}")

    index_content = '\n'.join(lines) + '\n'

    tmp = MEMORY_INDEX + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(index_content)
    os.replace(tmp, MEMORY_INDEX)

def has_uncommitted_changes(filepath):
    """Check if file has uncommitted git changes (working tree + staged)."""
    try:
        # Check both unstaged and staged changes vs HEAD
        result = subprocess.run(
            ['git', 'diff', 'HEAD', '--name-only', filepath],
            capture_output=True, text=True, cwd=os.path.dirname(filepath)
        )
        if filepath in result.stdout:
            return True
        # Also check untracked changes (not yet staged)
        result2 = subprocess.run(
            ['git', 'diff', '--name-only', filepath],
            capture_output=True, text=True, cwd=os.path.dirname(filepath)
        )
        return filepath in result2.stdout
    except Exception:
        return False  # If git not available, assume clean

# ── Index Sync: .claude/{rules,projects}/ → root CLAUDE.md tables ──────

def _parse_existing_index_rows(lines, header):
    """Parse existing table rows under a section header. Returns list of
    (filename_ref, row_text) tuples. filename_ref e.g. 'rules/figures.md'."""
    rows = []
    in_section, in_table = False, False
    for line in lines:
        if line.startswith(header):
            in_section = True; continue
        if in_section:
            if line.startswith('|') and '---' not in line:
                parts = [c.strip() for c in line.split('|') if c.strip()]
                if len(parts) >= 2:
                    file_ref = parts[1].replace('`', '')
                    # Skip header rows (re-inserted by sync_indices)
                    if file_ref in ('File', 'Domain', 'Project', 'Description',
                                    'Trigger Condition', 'Status', 'Title', 'Category',
                                    'Applies To', 'Decisions', 'Pitfalls', 'Last Session'):
                        continue
                    rows.append((file_ref, line))
                in_table = True
            elif in_table and not line.startswith('|'):
                break
    return rows


def _build_rule_row(f, fm, body):
    """Build a single rule index row. Uses frontmatter 'description'/'trigger'
    if present, else falls back to H1 heading and _TRIGGER_MAP."""
    domain = fm.get('domain', f.replace('.md', ''))
    priority = fm.get('priority', 5)
    desc = fm.get('description', '')
    if not desc:
        for line in body.split('\n'):
            s = line.strip()
            if s.startswith('# ') and not s.startswith('## '):
                desc = s[2:].strip(); break
    if not desc:
        desc = domain.replace('-', ' ').title()
    display = {'api': 'API', 'r-ecosystem': 'R Ecosystem'}.get(domain, domain.replace('-', ' ').title())
    trigger = fm.get('trigger', '')
    if not trigger:
        trigger = "Always" if priority <= 1 else _TRIGGER_MAP.get(domain, display + " tasks")
    return f"| {display} | `rules/{f}` | {desc} | {trigger} |"


def _build_project_row(f, fm, body):
    """Build a single project index row."""
    slug = fm.get('project', f.replace('.md', ''))
    status = fm.get('status', 'unknown')
    h1 = ''
    for line in body.split('\n'):
        s = line.strip()
        if s.startswith('# ') and not s.startswith('## '):
            h1 = s[2:].strip(); break
    h1 = h1 or slug.upper()
    return f"| {h1} | `projects/{f}` | {status} |"


def sync_indices(claude_md_path=None, rules_dir=None, projects_dir=None, dry_run=False):
    """ADDITIVE sync: preserves existing hand-curated table rows. Only ADDS
    new filesystem entries not already in the table. Never overwrites."""
    claude_md_path = claude_md_path or CLAUDE_MD
    rules_dir = rules_dir or RULES_DIR
    projects_dir = projects_dir or PROJECTS_DIR

    with open(claude_md_path, 'r', encoding='utf-8') as fh:
        original = fh.read()
    original_lines = original.split('\n')

    # ── Rules Index ──
    existing_rules = _parse_existing_index_rows(original_lines, '## Rules Index')
    existing_files = {row[0] for row in existing_rules}
    rules_rows = ["| Domain | File | Description | Trigger Condition |",
                  "|--------|------|-------------|-------------------|"]
    preserved_r = 0
    for file_ref, row_text in existing_rules:
        rules_rows.append(row_text); preserved_r += 1
    new_r = 0
    if os.path.isdir(rules_dir):
        for f in sorted(os.listdir(rules_dir)):
            if not f.endswith('.md'): continue
            if f"rules/{f}" in existing_files: continue
            try:
                fp = os.path.join(rules_dir, f)
                with open(fp, 'r', encoding='utf-8') as fh:
                    parts = fh.read().split('---', 2)
                if len(parts) < 3: continue
                fm = yaml.safe_load(parts[1]); body = parts[2].strip()
                rules_rows.append(_build_rule_row(f, fm, body)); new_r += 1
            except Exception: continue

    # ── Project Index ──
    existing_projs = _parse_existing_index_rows(original_lines, '## Project Index')
    existing_proj_files = {row[0] for row in existing_projs}
    proj_rows = ["| Project | File | Status |",
                 "|---------|------|--------|"]
    preserved_p = 0
    for file_ref, row_text in existing_projs:
        proj_rows.append(row_text); preserved_p += 1
    new_p = 0
    if os.path.isdir(projects_dir):
        for f in sorted(os.listdir(projects_dir)):
            if not f.endswith('.md') or f.startswith('_'): continue
            if f"projects/{f}" in existing_proj_files: continue
            try:
                fp = os.path.join(projects_dir, f)
                with open(fp, 'r', encoding='utf-8') as fh:
                    parts = fh.read().split('---', 2)
                if len(parts) < 3: continue
                fm = yaml.safe_load(parts[1]); body = parts[2].strip()
                proj_rows.append(_build_project_row(f, fm, body)); new_p += 1
            except Exception: continue

    if new_r == 0 and new_p == 0:
        return {"rules_synced": 0, "projects_synced": 0, "dirty": False,
                "rules_preserved": preserved_r, "projects_preserved": preserved_p}

    # ── Patch CLAUDE.md ──
    lines = list(original_lines)
    def _replace_or_append(lines, header, new_rows):
        out, skip, inserted, found = [], False, False, False
        for i, line in enumerate(lines):
            if line.startswith(header):
                found = True; out.append(line); skip, inserted = True, False; continue
            if skip:
                if not inserted: out.extend(new_rows); inserted = True
                if line.startswith('## ') or (line.startswith('```') and i > 0):
                    skip = False; out.append(line)
                continue
            out.append(line)
        if skip and not inserted: out.extend(new_rows)
        if not found: out.append(''); out.append(header); out.extend(new_rows)
        return out

    lines = _replace_or_append(lines, '## Rules Index', rules_rows)
    lines = _replace_or_append(lines, '## Project Index', proj_rows)
    new_content = '\n'.join(lines)
    if new_content == original:
        return {"rules_synced": 0, "projects_synced": 0, "dirty": False,
                "rules_preserved": preserved_r, "projects_preserved": preserved_p}
    if not dry_run:
        tmp = claude_md_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            fh.write(new_content)
        os.replace(tmp, claude_md_path)
    return {"rules_synced": new_r, "projects_synced": new_p, "dirty": True,
            "rules_preserved": preserved_r, "projects_preserved": preserved_p}


# ── CLI ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Compiler — sync index tables or run full compile")
    p.add_argument("--sync-index", action="store_true",
                   help="Rebuild Rules Index and Project Index in root CLAUDE.md")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--claude-md", default=CLAUDE_MD)
    p.add_argument("--rules-dir", default=RULES_DIR)
    p.add_argument("--projects-dir", default=PROJECTS_DIR)
    args = p.parse_args()

    if args.sync_index:
        result = sync_indices(claude_md_path=args.claude_md,
                              rules_dir=args.rules_dir,
                              projects_dir=args.projects_dir,
                              dry_run=args.dry_run)
        print(result)
        sys.exit(0 if not result.get("dirty") else 0)
    else:
        print("Use --sync-index to rebuild index tables.", file=sys.stderr)
        print("For full compile, use runner.py --step compile.", file=sys.stderr)
        sys.exit(1)
