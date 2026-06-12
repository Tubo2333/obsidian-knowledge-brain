#!/usr/bin/env python3
"""Validate YAML frontmatter in vault Markdown files.

Checks that .md files in the vault have valid YAML frontmatter and that
known template types include all required fields.

Usage:
  python validate_frontmatter.py <vault_path> [--templates-only] [--file <path>]
"""

import os
import sys
import yaml

REQUIRED_FIELDS = {
    "rule": ["rule_id", "title", "status", "category", "created"],
    "inbox_card": ["status", "proposed", "one_liner",
                   "affected_projects", "priority"],
    "session_summary": ["session_id", "date", "projects",
                        "summary_status", "summary_type"],
    "decisions": ["project", "decisions"],
    "pitfalls": ["project", "pitfalls"],
    "feedback": ["date", "task", "verdict"],
    "weekly_report": ["week", "date", "scan_status"],
    "heartbeat": ["last_scan", "scan_status"],
    "error_taxonomy": ["version", "categories"],
}


def detect_template_type(frontmatter):
    """Infer template type from frontmatter fields."""
    if "rule_id" in frontmatter:
        return "rule"
    if "one_liner" in frontmatter:
        return "inbox_card"
    if "session_id" in frontmatter and "summary_status" in frontmatter:
        return "session_summary"
    if "decisions" in frontmatter and "project" in frontmatter:
        return "decisions"
    if "pitfalls" in frontmatter:
        return "pitfalls"
    if "verdict" in frontmatter:
        return "feedback"
    if "scan_status" in frontmatter and "week" in frontmatter:
        return "weekly_report"
    if "scan_status" in frontmatter and "last_scan" in frontmatter:
        return "heartbeat"
    if "categories" in frontmatter:
        return "error_taxonomy"
    return None


def validate_frontmatter(filepath):
    """Validate a single file's frontmatter.

    Returns (ok, errors, template_type).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if not content.startswith('---'):
        return True, [], None  # No frontmatter, skip

    parts = content.split('---', 2)
    if len(parts) < 3:
        return False, ["Malformed frontmatter delimiters"], None

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"], None

    if fm is None:
        return True, [], None  # Empty frontmatter, skip

    ttype = detect_template_type(fm)
    if ttype is None:
        return True, [], None  # Unknown type, skip validation

    required = REQUIRED_FIELDS.get(ttype, [])
    errors = []
    for field in required:
        if field not in fm:
            errors.append(f"Missing required field: {field}")

    return len(errors) == 0, errors, ttype


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_frontmatter.py <vault_path> "
              "[--templates-only] [--file <path>]")
        sys.exit(1)

    vault_path = sys.argv[1]
    templates_only = '--templates-only' in sys.argv

    # Check for single file mode
    single_file = None
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            single_file = sys.argv[idx + 1]

    if single_file:
        ok, errors, ttype = validate_frontmatter(single_file)
        if errors:
            print(f"FAIL [{ttype or 'unknown'}]: {single_file}")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"OK: {single_file}")
            sys.exit(0)

    # Walk the vault
    files_to_check = []
    for root, dirs, files in os.walk(vault_path):
        # Skip non-content directories
        dirs_to_skip = {'.git', '_rollback', '_logs', '_raw-sessions'}
        dirs[:] = [d for d in dirs if d not in dirs_to_skip]
        for f in files:
            if f.endswith('.md'):
                filepath = os.path.join(root, f)
                if templates_only and '_TEMPLATE' not in f:
                    continue
                files_to_check.append(filepath)

    total_errors = 0
    for fp in files_to_check:
        ok, errors, ttype = validate_frontmatter(fp)
        if errors:
            total_errors += len(errors)
            rel = os.path.relpath(fp, vault_path)
            print(f"FAIL [{ttype or 'unknown'}]: {rel}")
            for e in errors:
                print(f"  - {e}")

    if total_errors == 0:
        print(f"OK: {len(files_to_check)} files validated, 0 errors")
    else:
        print(f"FAIL: {total_errors} errors in {len(files_to_check)} files")
        sys.exit(1)


if __name__ == '__main__':
    main()
