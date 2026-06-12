#!/usr/bin/env python3
"""Validate [[wiki-links]] across all vault Markdown files.

Scans all .md files, extracts [[wiki-links]], and verifies targets exist.
Supports Obsidian's bare-filename resolution ([[my-note]] resolves to
any file named my-note.md regardless of directory).

Usage:
  python link_validator.py <vault_path>
"""

import os
import re
import sys

WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]')


def run(vault_path):
    """Scan all .md files, extract [[links]], verify targets exist.

    Returns list of broken links with {source, target, reason} dicts.
    """
    # Build file index
    file_index = {}
    anchor_index = {}

    for root, dirs, files in os.walk(vault_path):
        dirs_to_skip = {'.git', '_rollback', '_logs'}
        dirs[:] = [d for d in dirs if d not in dirs_to_skip]
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, vault_path).replace('\\', '/')
            file_index[rel.lower()] = rel

            # Extract anchors from this file
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    fm = yaml.safe_load(parts[1])
                    if fm and 'anchor' in fm:
                        anchor_index[
                            f"{rel}#{fm['anchor']}".lower()
                        ] = rel
                except yaml.YAMLError:
                    pass

    # Build filename-only index for Obsidian bare-filename resolution
    # e.g., [[my-memory]] resolves to any file named my-memory.md
    filename_index = {}
    for rel in file_index.values():
        basename = os.path.basename(rel).lower()
        name_no_ext = basename.replace('.md', '')
        if name_no_ext not in filename_index:
            filename_index[name_no_ext] = []
        filename_index[name_no_ext].append(rel)

    # Validate all links
    broken = []
    for root, dirs, files in os.walk(vault_path):
        dirs_to_skip = {'.git', '_rollback', '_logs'}
        dirs[:] = [d for d in dirs if d not in dirs_to_skip]
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()

            links = WIKI_LINK_PATTERN.findall(content)
            for link in links:
                target = link.strip().replace('\\', '/').lower()
                base = target.split('#')[0]
                if not base.endswith('.md'):
                    base += '.md'

                if base in file_index or target in anchor_index:
                    continue

                # Fallback: Obsidian filename-only resolution
                search_name = base.replace('.md', '')
                if search_name in filename_index:
                    continue
                if search_name + '.md' in filename_index:
                    continue

                broken.append({
                    'source': os.path.relpath(fp, vault_path).replace('\\', '/'),
                    'target': link.strip(),
                    'reason': 'file not found'
                })

    return broken


def main():
    if len(sys.argv) < 2:
        print("Usage: python link_validator.py <vault_path>")
        sys.exit(1)

    vault = sys.argv[1]
    if not os.path.exists(vault):
        print(f"ERROR: Vault path not found: {vault}")
        sys.exit(1)

    broken = run(vault)
    if broken:
        print(f"Broken links: {len(broken)}")
        for b in broken:
            print(f"  {b['source']} -> [[{b['target']}]] ({b['reason']})")
        sys.exit(1)
    else:
        print("All wiki-links valid")


if __name__ == '__main__':
    main()
