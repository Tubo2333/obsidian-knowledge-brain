"""Step 5: Compile 00-Rules -> CLAUDE.md marked blocks.

Reads active rules from the vault's 00-Rules/ directory and project status
from 01-Projects/, then injects them into CLAUDE.md between designated
marker comments.

Markers required in CLAUDE.md:
  <!-- COMPILED:RULES_START --> ... <!-- COMPILED:RULES_END -->
  <!-- COMPILED:PROJECTS_START --> ... <!-- COMPILED:PROJECTS_END -->

Safety: pauses if CLAUDE.md has uncommitted git changes (dirty detection).
"""

import os
import yaml
import subprocess
from datetime import datetime

RULES_START = "<!-- COMPILED:RULES_START -->"
RULES_END = "<!-- COMPILED:RULES_END -->"
PROJECTS_START = "<!-- COMPILED:PROJECTS_START -->"
PROJECTS_END = "<!-- COMPILED:PROJECTS_END -->"


def run(cfg, dry_run=False, step_results=None):
    vault = cfg['vault_path']
    claude_md_path = cfg.get('claude_md_path', '')

    if not claude_md_path:
        return {"error": "claude_md_path not configured in config.yaml — "
                         "compilation skipped"}

    if not os.path.exists(claude_md_path):
        return {"error": f"CLAUDE.md not found at: {claude_md_path}"}

    # Dirty detection — pause if file has uncommitted changes
    if has_uncommitted_changes(claude_md_path):
        return {"error": "CLAUDE.md has uncommitted manual edits — "
                         "compilation paused. Commit or stash changes first."}

    # Read current CLAUDE.md
    with open(claude_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Validate markers exist
    for marker in [RULES_START, RULES_END, PROJECTS_START, PROJECTS_END]:
        if marker not in content:
            return {"error": f"Missing marker in CLAUDE.md: {marker}"}

    # Compile sections
    rules_text = compile_rules_section(vault)
    projects_text = compile_projects_section(vault)

    # Replace marked blocks
    new_content = replace_block(content, RULES_START, RULES_END, rules_text)
    new_content = replace_block(new_content, PROJECTS_START, PROJECTS_END,
                                projects_text)

    if not dry_run:
        # Atomic write
        tmp_path = claude_md_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        os.replace(tmp_path, claude_md_path)

    return {
        "rules_compiled": rules_text.count('\n'),
        "projects_compiled": projects_text.count('\n'),
        "dirty": False
    }


def has_uncommitted_changes(filepath):
    """Check if file has uncommitted git changes.

    Checks both staged and unstaged changes vs HEAD.
    Returns False if git is not available (non-git environments).
    """
    try:
        cwd = os.path.dirname(filepath)
        # Check staged + unstaged changes vs HEAD
        result = subprocess.run(
            ['git', 'diff', 'HEAD', '--name-only', filepath],
            capture_output=True, text=True, cwd=cwd
        )
        if filepath in result.stdout:
            return True
        # Also check unstaged changes
        result2 = subprocess.run(
            ['git', 'diff', '--name-only', filepath],
            capture_output=True, text=True, cwd=cwd
        )
        return filepath in result2.stdout
    except Exception:
        return False  # If git not available, assume clean


def compile_rules_section(vault):
    """Generate rules table from 00-Rules/*.md active rules."""
    rules_dir = os.path.join(vault, '00-Rules')
    lines = [
        "| Rule ID | Title | Category | Applies To | Status |",
        "|---------|-------|----------|------------|--------|"
    ]

    if not os.path.exists(rules_dir):
        return '\n'.join(lines)

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
                lines.append(
                    f"| {rule_id} | {title} | {category} | "
                    f"{applies} | {status} |"
                )
        except (yaml.YAMLError, IndexError):
            continue

    return '\n'.join(lines)


def compile_projects_section(vault):
    """Generate project status table from 01-Projects/ decisions.md files."""
    projects_dir = os.path.join(vault, '01-Projects')
    lines = [
        "| Project | Decisions | Pitfalls | Last Session |",
        "|---------|-----------|----------|-------------|"
    ]

    if not os.path.exists(projects_dir):
        return '\n'.join(lines)

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

        lines.append(
            f"| {proj} | {n_decisions} | {n_pitfalls} | {last_session} |"
        )

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
    files = [f for f in os.listdir(sessions_dir)
             if f.endswith('.md') and not f.startswith('_')]
    if not files:
        return '-'
    return sorted(files)[-1][:10]  # First 10 chars = date
