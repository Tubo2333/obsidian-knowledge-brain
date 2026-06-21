"""Step 5: Compile 00-Rules -> CLAUDE.md marked blocks + Agent Memory."""
import os
import yaml
import subprocess
from datetime import datetime

# ── Part A constants — SHUTDOWN per v3.0 S8.4 L1 (2026-06-21) ──
# Removed: RULES_START/END, PROJECTS_START/END, compile_rules_section(),
# compile_projects_section(), replace_block()

MEMORY_DIR = "C:/Users/Administrator/.claude/projects/d--C-file/memory"
MEMORY_INDEX = os.path.join(MEMORY_DIR, "MEMORY.md")

def run(cfg, dry_run=False, step_results=None):
    vault = cfg['vault_path']
    claude_md_path = cfg.get('claude_md_path', "D:/C-file/CLAUDE.md")
    results = {"rules_compiled": 0, "projects_compiled": 0, "dirty": False,
               "memory_rules_written": 0, "memory_index_updated": False}

    # ── Part A: CLAUDE.md compilation — SHUTDOWN per v3.0 S8.4 L1 (2026-06-21) ──
    # Part A injected Obsidian-vault rules/projects tables into CLAUDE.md via
    # COMPILED markers. v3.0 manages rules/ and projects/ directly from
    # .claude/rules/ and .claude/projects/ filesystem. Part A removed.

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

# ── Part A functions — SHUTDOWN per v3.0 S8.4 L1 (2026-06-21) ──
# Removed: has_uncommitted_changes(), compile_rules_section(), compile_projects_section(),
# replace_block(), count_frontmatter_items(), get_latest_session()
