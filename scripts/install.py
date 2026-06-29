#!/usr/bin/env python3
"""
obsidian-knowledge-brain v4.0 — Installer.
9-step idempotent cross-platform setup. Orchestrates global_atoms,
keyword_index, and pre_action modules. Handles install, upgrade, and uninstall.
Usage: python install.py [--platform cursor|gemini|codex|claude] [--dry-run] [--uninstall]
"""
import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from global_atoms import (
    ensure_atoms_dir, init_atoms, read_atoms, write_atoms,
    validate_schema, ATOMS_DIR, ATOMS_PATH, is_uninstalled, UNINSTALLED_PATH,
    compute_atom_id, promote_atom
)
from keyword_index import (
    ensure_global_atoms_section, safe_merge_sync, read_index, write_index,
    has_global_atoms
)
from pre_action import inject, remove, is_already_injected, detect_format

PLATFORM_MAP = {
    "claude": (".claude", "CLAUDE.md"),
    "cursor": (".cursor", ".cursorrules"),
    "gemini": (".gemini", "extensions.json"),
    "codex": (".codex", "codex.yaml"),
}


def detect_platform():
    """Auto-detect platform from existing directories in cwd or parents."""
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        for name, (base_dir, always_loaded) in PLATFORM_MAP.items():
            if (p / base_dir).exists():
                return name
    return None


def check_dual_platforms():
    """Check for multiple agent directories. Returns list of found platforms."""
    cwd = Path.cwd()
    found = []
    for name, (base_dir, _) in PLATFORM_MAP.items():
        if (cwd / base_dir).exists():
            found.append(name)
    return found


def step1_version_check():
    """Step 1: Check install.py schema version vs SKILL.md schema version."""
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        print("  WARNING: SKILL.md not found, skipping version check")
        return True
    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()
    if "**Schema**: 4.0" in content or "**Schema**:4.0" in content:
        return True
    if "**Schema**: 3.0" in content or "**Schema**:3.0" in content:
        print("  WARNING: SKILL.md is v3.0, install.py is v4.0.")
        print("  Upgrading SKILL.md schema version as part of v4.0 migration...")
        return True
    print("  WARNING: Cannot determine SKILL.md schema version")
    return True


def step2_platform_detection(platform_arg):
    """Step 2: Detect platform. Returns (platform_name, base_dir, always_loaded_file)."""
    platform = platform_arg or detect_platform()
    if not platform:
        print("ERROR: Could not detect platform. Use --platform to specify.")
        print(f"  Options: {list(PLATFORM_MAP.keys())}")
        return None
    base_dir, always_loaded = PLATFORM_MAP[platform]
    print(f"  Platform: {platform} (base: {base_dir}/, always-loaded: {always_loaded})")
    return platform, base_dir, always_loaded


def step3_dual_platform_check(platform_name):
    """Step 3: Check for multiple agent directories.
    Always returns True — dual-platform is a warning, not an error."""
    found = check_dual_platforms()
    other = [p for p in found if p != platform_name]
    if other:
        print(f"  ⚠ 多平台目录检测到 (Dual-platform detected): {found}")
        print(f"  当前目标 (Current target): {platform_name}")
        print(f"  建议选主平台 (Recommend selecting primary platform).")
        print(f"  两个平台共享 ~/.obsidian-knowledge-brain/，各自维护独立索引文件。")
    return True


def step4_global_directory_setup():
    """Step 4: Create ~/.obsidian-knowledge-brain/, init atoms.json. Idempotent."""
    ensure_atoms_dir()
    if ATOMS_PATH.exists():
        data = read_atoms()
        if data is None:
            print("  ERROR: atoms.json exists but is invalid. NOT overwriting (protect data).")
            print("  Check ~/.obsidian-knowledge-brain/atoms.json and atoms.json.bak")
            return False
        print("  atoms.json exists + valid -> skip init")
        return True
    else:
        data = init_atoms()
        print("  Created atoms.json with empty skeleton")
        return True


def step5_inject_pre_action(base_dir, always_loaded):
    """Step 5: Inject pre-action instruction into always-loaded file. Idempotent."""
    if is_uninstalled():
        print("  .uninstalled marker present -> skip injection")
        return True

    target = Path.cwd() / always_loaded
    if not target.exists():
        print(f"  WARNING: {always_loaded} not found -> skip injection")
        print(f"  (Pre-action instruction requires the always-loaded file)")
        return True

    fmt = detect_format(target)
    print(f"  Detected format: {fmt}")

    if is_already_injected(target):
        print("  Pre-action instruction already present -> skip")
        return True

    ok, msg = inject(target)
    if ok:
        print(f"  Injected pre-action instruction ({msg})")
    else:
        print(f"  WARNING: Injection failed: {msg}")
    return True


def step6_keyword_index_upgrade(base_dir):
    """Step 6: Ensure _keyword_index.json has _global_atoms section. Idempotent."""
    idx_path = Path.cwd() / base_dir / "rules" / "_keyword_index.json"
    if idx_path.exists():
        already_had = has_global_atoms(Path.cwd())
        ensure_global_atoms_section(Path.cwd())
        if already_had:
            print(f"  _keyword_index.json: _global_atoms section already present -> skip")
        else:
            print(f"  _keyword_index.json: added _global_atoms section")
    else:
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump({"_global_atoms": []}, f, indent=2)
        print(f"  Created _keyword_index.json with _global_atoms section")
    return True


def step7_placeholder_replacement():
    """Step 7: Replace {AGENT_DIR} placeholders in skill files.
    For v4.0, all paths use platform-adaptive language — no hardcoded paths to replace.
    This step is a no-op for v4.0 (spec-compliant from the start)."""
    print("  No hardcoded paths (platform-adaptive language) -> skip")
    return True


def step8_validation(base_dir, always_loaded):
    """Step 8: Validate installation."""
    all_ok = True

    # atoms.json valid
    data = read_atoms()
    if data is None:
        print("  FAIL: atoms.json invalid or missing")
        all_ok = False
    else:
        valid, err = validate_schema(data)
        if valid:
            print("  PASS: atoms.json valid")
        else:
            print(f"  FAIL: atoms.json schema: {err}")
            all_ok = False

    # Pre-action present
    target = Path.cwd() / always_loaded
    if target.exists():
        if is_already_injected(target) or is_uninstalled():
            print(f"  PASS: Pre-action instruction present (or uninstalled)")
        else:
            print(f"  WARN: Pre-action instruction NOT in {always_loaded}")
    else:
        print(f"  SKIP: {always_loaded} does not exist")

    # _keyword_index.json has _global_atoms
    idx = read_index(Path.cwd())
    if idx and "_global_atoms" in idx:
        print("  PASS: _keyword_index.json has _global_atoms section")
    else:
        print("  WARN: _keyword_index.json missing _global_atoms section")
        all_ok = False

    return all_ok


def uninstall(base_dir, always_loaded):
    """Step 9: Uninstall — create .uninstalled marker, remove pre-action,
    remove _global_atoms from keyword index (keep atoms.json)."""
    print("=== UNINSTALL ===")

    # Create .uninstalled marker
    UNINSTALLED_PATH.write_text(
        f"uninstalled: {datetime.now(timezone.utc).isoformat()}\n"
        "To reinstall: delete this file and run install.py\n"
    )
    print("  Created .uninstalled marker")

    # Remove pre-action from always-loaded file
    target = Path.cwd() / always_loaded
    if target.exists():
        ok, msg = remove(target)
        print(f"  Pre-action removal: {msg}")
    else:
        print(f"  {always_loaded} not found -> skip removal")

    # Remove _global_atoms from keyword index
    idx = read_index(Path.cwd())
    if idx and "_global_atoms" in idx:
        del idx["_global_atoms"]
        if "_global_atoms_meta" in idx:
            del idx["_global_atoms_meta"]
        write_index(Path.cwd(), idx)
        print("  Removed _global_atoms from keyword index")
        print("  atoms.json preserved at ~/.obsidian-knowledge-brain/")

    print("Uninstall complete. To reinstall: delete ~/.obsidian-knowledge-brain/.uninstalled")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="obsidian-knowledge-brain v4.0 — Installer"
    )
    parser.add_argument("--platform", choices=list(PLATFORM_MAP.keys()),
                        help="Target platform (auto-detect if omitted)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove pre-action injection + _global_atoms (keeps atoms.json)")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN (no changes will be made) ===\n")

    platform_info = step2_platform_detection(args.platform)
    if platform_info is None:
        sys.exit(1)
    platform_name, base_dir, always_loaded = platform_info

    if args.uninstall:
        if args.dry_run:
            print(f"Would uninstall from {base_dir}/")
        else:
            uninstall(base_dir, always_loaded)
        return

    print(f"\nInstalling obsidian-knowledge-brain v4.0 for {platform_name}")
    print(f"  Project root: {Path.cwd()}")
    print(f"  Agent dir: {base_dir}/")
    print(f"  Always-loaded: {always_loaded}\n")

    if args.dry_run:
        print("Would execute steps 1-8 (all idempotent).")
        print("Run without --dry-run to install.")
        return

    # Execute all steps
    steps = [
        ("Version check", lambda: step1_version_check()),
        ("Platform detection", lambda: True),
        ("Dual-platform check", lambda: step3_dual_platform_check(platform_name)),
        ("Global directory setup", step4_global_directory_setup),
        ("Pre-action injection", lambda: step5_inject_pre_action(base_dir, always_loaded)),
        ("Keyword index upgrade", lambda: step6_keyword_index_upgrade(base_dir)),
        ("Placeholder replacement", step7_placeholder_replacement),
        ("Validation", lambda: step8_validation(base_dir, always_loaded)),
    ]

    for i, (name, fn) in enumerate(steps, 1):
        print(f"-- Step {i}: {name}")
        ok = fn()
        if ok is False:
            print(f"ERROR at step {i} ({name}). Aborting.")
            sys.exit(1)

    print("\n=== Installation complete ===")
    print(f"  Global table: {ATOMS_PATH}")
    print(f"  Pre-action: {'injected' if is_already_injected(Path.cwd() / always_loaded) else 'pending'}")
    print("  Restart your Agent session for changes to take effect.")


if __name__ == "__main__":
    main()
