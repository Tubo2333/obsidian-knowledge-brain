#!/usr/bin/env python3
"""Repair mangled Markdown table separators using regex replacement.

Utility for fixing topic-index.md and timeline.md table formatting
after manual edits or encoding issues corrupt separator rows.

Usage:
  python reformat_tables.py <vault_path>
"""

import os
import re
import sys


def fix_table_separators(filepath, separator_line):
    """Fix mangled separator lines in a Markdown table file.

    Detects table header lines followed by corrupted separator rows
    (random dashes, pipes, spaces) and replaces them with a clean separator.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: table header line followed by one or more junk lines
    # Junk = lines containing only dashes, pipes, spaces, or blank
    junk_line = r'[\-|\s]+\n'
    pattern = re.compile(
        r'(\| [^\n]+\n)'     # Header line
        r'(' + junk_line + r')+'  # One or more junk lines
    )
    fixed = pattern.sub(r'\1' + separator_line + '\n', content)

    if fixed != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed)
        return True
    return False


def run(vault_path):
    """Fix table separators in topic-index.md and timeline.md."""
    maps_dir = os.path.join(vault_path, '03-Maps')

    fixes = []

    # topic-index.md has a 3-column table
    ti_path = os.path.join(maps_dir, 'topic-index.md')
    if os.path.exists(ti_path):
        changed = fix_table_separators(
            ti_path,
            '|---------------|---------------------|---------------------------|'
        )
        if changed:
            fixes.append(ti_path)
            print(f"Fixed: {ti_path}")

    # timeline.md has a 3-column table
    tl_path = os.path.join(maps_dir, 'timeline.md')
    if os.path.exists(tl_path):
        changed = fix_table_separators(
            tl_path,
            '|---------------|------------|------------------|'
        )
        if changed:
            fixes.append(tl_path)
            print(f"Fixed: {tl_path}")

    if not fixes:
        print("No tables needed fixing.")
    else:
        print(f"\nDone! {len(fixes)} file(s) fixed.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python reformat_tables.py <vault_path>")
        sys.exit(1)

    vault = sys.argv[1]
    if not os.path.exists(vault):
        print(f"ERROR: Vault path not found: {vault}")
        sys.exit(1)

    run(vault)
