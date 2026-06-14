"""Step 5: Compile 00-Rules -> CLAUDE.md marked blocks + Agent Memory."""
import os
import yaml
import subprocess
from datetime import datetime

RULES_START = "<!-- COMPILED:RULES_START -->"
RULES_END = "<!-- COMPILED:RULES_END -->"
PROJECTS_START = "<!-- COMPILED:PROJECTS_START -->"
PROJECTS_END = "<!-- COMPILED:PROJECTS_END -->"

MEMORY_DIR = "C:/Users/Administrator/.claude/projects/d--C-file/memory"
MEMORY_INDEX = os.path.join(MEMORY_DIR, "MEMORY.md")

def run(cfg, dry_run=False, step_results=None):
    vault = cfg['vault_path']
    claude_md_path = cfg.get('claude_md_path', "D:/C-file/CLAUDE.md")
    results = {"rules_compiled": 0, "projects_compiled": 0, "dirty": False,
               "memory_rules_written": 0, "memory_index_updated": False}

    # ── Part A: CLAUDE.md compilation ──
    # Dirty detection
    if has_uncommitted_changes(claude_md_path):
        results["error"] = "CLAUDE.md has uncommitted manual edits — compilation paused"
        # Don't return — still do Agent Memory part
    else:
        try:
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            markers_ok = True
            for marker in [RULES_START, RULES_END, PROJECTS_START, PROJECTS_END]:
                if marker not in content:
                    results["error"] = f"Missing marker in CLAUDE.md: {marker}"
                    markers_ok = False
                    break

            if markers_ok:
                rules_text = compile_rules_section(vault)
                projects_text = compile_projects_section(vault)
                new_content = replace_block(content, RULES_START, RULES_END, rules_text)
                new_content = replace_block(new_content, PROJECTS_START, PROJECTS_END, projects_text)

                if not dry_run:
                    tmp_path = claude_md_path + '.tmp'
                    with open(tmp_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    os.replace(tmp_path, claude_md_path)

                results["rules_compiled"] = rules_text.count('\n')
                results["projects_compiled"] = projects_text.count('\n')
        except Exception as e:
            results["claude_md_error"] = str(e)

    # ── Part B: Agent Memory sync ──
    try:
        mem_result = sync_to_agent_memory(vault, dry_run)
        results.update(mem_result)
    except Exception as e:
        results["memory_error"] = str(e)

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

def compile_rules_section(vault):
    """Generate rules table from 00-Rules/*.md active rules."""
    rules_dir = os.path.join(vault, '00-Rules')
    lines = ["| Rule ID | Title | Category | Applies To | Status |",
             "|---------|-------|----------|------------|--------|"]

    for f in sorted(os.listdir(rules_dir)):
        if not f.endswith('.md') or f.startswith('_'):
            continue
        fp = os.path.join(rules_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm = yaml.safe_load(content.split('---')[1])
            if fm.get('status') in ('active', 'beta'):
                rule_id = fm.get('rule_id', '?')
                title = fm.get('title', '?')
                category = fm.get('category', '?')
                applies = ', '.join(fm.get('applies_to', []))
                status = fm.get('status', '?')
                lines.append(f"| {rule_id} | {title} | {category} | {applies} | {status} |")
        except (yaml.YAMLError, IndexError):
            continue

    return '\n'.join(lines)

def compile_projects_section(vault):
    """Generate project status table from 01-Projects/ decisions.md files."""
    projects_dir = os.path.join(vault, '01-Projects')
    lines = ["| Project | Decisions | Pitfalls | Last Session |",
             "|---------|-----------|----------|-------------|"]

    for proj in sorted(os.listdir(projects_dir)):
        proj_dir = os.path.join(projects_dir, proj)
        if not os.path.isdir(proj_dir):
            continue
        decisions_path = os.path.join(proj_dir, 'Memory', 'decisions.md')
        pitfalls_path = os.path.join(proj_dir, 'Memory', 'pitfalls.md')
        sessions_dir = os.path.join(proj_dir, 'Memory', 'sessions')

        n_decisions = count_frontmatter_items(decisions_path, 'decisions')
        n_pitfalls = count_frontmatter_items(pitfalls_path, 'pitfalls')
        last_session = get_latest_session(sessions_dir)

        lines.append(f"| {proj} | {n_decisions} | {n_pitfalls} | {last_session} |")

    return '\n'.join(lines)

def replace_block(content, start_marker, end_marker, new_content):
    """Replace content between start and end markers."""
    before = content.split(start_marker)[0]
    after = content.split(end_marker)[1]
    return before + start_marker + '\n' + new_content + '\n' + end_marker + after

def count_frontmatter_items(path, key):
    if not os.path.exists(path):
        return 0
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        fm = yaml.safe_load(content.split('---')[1])
        return len(fm.get(key, []))
    except (yaml.YAMLError, IndexError):
        return 0

def get_latest_session(sessions_dir):
    if not os.path.exists(sessions_dir):
        return '-'
    files = [f for f in os.listdir(sessions_dir) if f.endswith('.md') and not f.startswith('_')]
    if not files:
        return '-'
    return sorted(files)[-1][:10]  # First 10 chars = date
