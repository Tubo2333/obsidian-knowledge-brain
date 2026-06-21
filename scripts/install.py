#!/usr/bin/env python3
"""obsidian-knowledge-brain v3.0 — Installer for cross-platform path setup.
Replaces .claude/ with the target platform's base directory across all skill files.
Usage: python install.py [--platform cursor|gemini|codex|claude] [--dry-run]
"""

import os, sys, argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent  # .../obsidian-knowledge-brain/
PLATFORM_MAP = {
    "claude": ".claude",
    "cursor": ".cursor",
    "gemini": ".gemini",
    "codex": ".codex",
}
SKILL_FILES = ["SKILL.md"] + [
    f"references/{f}" for f in os.listdir(SKILL_ROOT / "references") if f.endswith(".md")
] + [
    f"templates/{f}" for f in os.listdir(SKILL_ROOT / "templates") if f.endswith(".md")
]

def install(platform, dry_run=False):
    base = PLATFORM_MAP[platform]
    changes = 0

    for rel_path in SKILL_FILES:
        fp = SKILL_ROOT / rel_path
        if not fp.exists():
            continue
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        # Replace .claude/ with target base, but NOT inside archive/ paths
        new_content = content.replace(".claude/", f"{base}/")
        new_content = new_content.replace("`.claude`", f"`{base}`")
        if new_content != content:
            changes += 1
            if not dry_run:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(new_content)
            print(f"  {'[DRY-RUN]' if dry_run else 'UPDATED'}: {rel_path}")

    print(f"\n{'Would change' if dry_run else 'Changed'} {changes} files to use '{base}/'.")
    if not dry_run:
        print("Done. Restart your Agent session for changes to take effect.")
    return changes


def detect_platform():
    """Auto-detect platform from existing directories."""
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        for name, base in PLATFORM_MAP.items():
            if (p / base).exists():
                return name
    return None


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Install obsidian-knowledge-brain for your platform")
    p.add_argument("--platform", choices=list(PLATFORM_MAP.keys()), help="Target platform")
    p.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = p.parse_args()

    platform = args.platform or detect_platform()
    if not platform:
        print("ERROR: Could not detect platform. Use --platform to specify.")
        sys.exit(1)

    print(f"Installing for platform: {platform} (base dir: {PLATFORM_MAP[platform]}/)")
    install(platform, dry_run=args.dry_run)
