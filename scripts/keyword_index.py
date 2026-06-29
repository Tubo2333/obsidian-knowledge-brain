#!/usr/bin/env python3
"""
obsidian-knowledge-brain v4.0 — Keyword Index operations.
Manages _keyword_index.json with _global_atoms section, safe-merge sync,
.bak protection, and keyword cleanup for demoted atoms.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Re-use from global_atoms
sys.path.insert(0, str(Path(__file__).resolve().parent))
from global_atoms import read_atoms, ATOMS_PATH


def index_path(project_root: Path) -> Path:
    """Get _keyword_index.json path for a project."""
    agent_dir = _detect_agent_dir(project_root)
    return agent_dir / "rules" / "_keyword_index.json"


def bak_path(project_root: Path) -> Path:
    """Get _keyword_index.json.bak path."""
    return Path(str(index_path(project_root)) + ".bak")


def _detect_agent_dir(project_root: Path) -> Path:
    """Detect which agent directory exists (.claude/, .cursor/, etc.)."""
    for candidate in [".claude", ".cursor", ".gemini", ".codex"]:
        d = project_root / candidate
        if d.exists():
            return d
    return project_root / ".claude"  # default


def read_index(project_root: Path) -> dict | None:
    """Read _keyword_index.json with .bak fallback and directory rebuild.
    Returns None only if both index and .bak are unrecoverable."""
    ip = index_path(project_root)
    bp = bak_path(project_root)

    for path in (ip, bp):
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            continue

    # Both broken -> rebuild from directory scan
    return _rebuild_from_scan(project_root)


def write_index(project_root: Path, data: dict) -> bool:
    """Write _keyword_index.json with .bak protection + read-back validate.
    Returns True on success."""
    ip = index_path(project_root)
    bp = bak_path(project_root)

    # Backup
    if ip.exists():
        try:
            with open(ip, "r", encoding="utf-8") as f:
                bak_content = f.read()
            with open(bp, "w", encoding="utf-8") as f:
                f.write(bak_content)
        except OSError:
            pass

    # Write
    ip.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ip, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        return False

    # Validate
    try:
        with open(ip, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, OSError):
        if bp.exists():
            with open(bp, "r", encoding="utf-8") as f:
                rollback = json.load(f)
            with open(ip, "w", encoding="utf-8") as f:
                json.dump(rollback, f, indent=2, ensure_ascii=False)
        return False


def _rebuild_from_scan(project_root: Path) -> dict:
    """Rebuild index from rules/ directory scan. Returns minimal valid index."""
    result = {"_global_atoms": []}
    agent_dir = _detect_agent_dir(project_root)
    rules_dir = agent_dir / "rules"
    if rules_dir.exists():
        for f in sorted(rules_dir.glob("*.md")):
            key = f.stem.lower().replace("-", " ")
            if key not in result:
                result[key] = []
            rel_path = str(f.relative_to(agent_dir)).replace("\\", "/")
            if rel_path not in result[key]:
                result[key].append(rel_path)
    return result


def safe_merge_sync(project_root: Path) -> tuple[bool, str]:
    """Safe-merge atoms.json into _keyword_index.json _global_atoms section.
    Per spec:
    - atoms.json empty (new machine) -> skip sync, preserve existing _global_atoms
    - New atoms not in local _global_atoms -> append
    - Updated atoms -> update in place
    - Local atoms not in atoms.json -> keep (don't delete)
    - Atom has demoted: true -> remove from _global_atoms, clean keyword refs
    - Debounce: skip if atoms.json mtime unchanged
    Returns (changed, message)."""
    atoms_data = read_atoms()
    idx = read_index(project_root)
    if idx is None:
        return False, "Cannot read keyword index"

    # atoms.json empty -> skip sync, preserve existing _global_atoms
    if atoms_data is None or not atoms_data.get("atoms"):
        return False, "atoms.json empty or unreadable -> skip sync"

    # Debounce: skip if atoms.json mtime unchanged
    if ATOMS_PATH.exists():
        current_mtime = ATOMS_PATH.stat().st_mtime
        stored_mtime = idx.get("_global_atoms_meta", {}).get("atoms_mtime", 0)
        if abs(current_mtime - stored_mtime) < 0.5:
            return False, "atoms.json mtime unchanged -> skip sync"

    existing_global = {a["id"]: a for a in idx.get("_global_atoms", [])}
    current_atoms = {a["id"]: a for a in atoms_data.get("atoms", [])}
    changed = False

    # Demoted atoms: remove from _global_atoms, clean keyword refs
    for aid in list(existing_global.keys()):
        if aid in current_atoms and current_atoms[aid].get("demoted", False):
            _remove_atom_from_keywords(idx, aid)
            del existing_global[aid]
            changed = True

    # New or updated atoms
    for aid, atom in current_atoms.items():
        if atom.get("demoted", False):
            continue  # skip demoted
        cached = {
            "id": atom["id"],
            "type": atom["type"],
            "phase": atom["phase"],
            "pointer": atom["pointer"],
            "one_liner": atom["one_liner"],
            "trigger": atom.get("trigger", [])
        }
        if aid not in existing_global:
            # New atom -> append to _global_atoms, add keyword entries
            existing_global[aid] = cached
            _add_atom_to_keywords(idx, cached)
            changed = True
        elif existing_global[aid] != cached:
            # Updated -> refresh _global_atoms entry
            existing_global[aid] = cached
            changed = True

    if changed:
        idx["_global_atoms"] = list(existing_global.values())
        idx["_global_atoms_meta"] = {
            "atoms_mtime": ATOMS_PATH.stat().st_mtime,
            "last_sync": datetime.now(timezone.utc).isoformat()
        }
        ok = write_index(project_root, idx)
        return ok, "synced" if ok else "write failed"
    return False, "no changes"


def _add_atom_to_keywords(idx: dict, atom: dict):
    """Add keyword->atom_id entries for an atom's triggers."""
    for keyword in atom.get("trigger", []):
        key = keyword.lower()
        if key not in idx:
            idx[key] = []
        if atom["id"] not in idx[key]:
            idx[key].append(atom["id"])


def _remove_atom_from_keywords(idx: dict, atom_id: str):
    """Remove all references to atom_id from keyword entries.
    If atom_id was the last entry for a keyword and no local file refs remain,
    remove the keyword entry entirely."""
    to_remove = []
    for key, refs in idx.items():
        if key.startswith("_"):
            continue
        if isinstance(refs, list) and atom_id in refs:
            refs.remove(atom_id)
            if not refs:
                to_remove.append(key)
    for key in to_remove:
        del idx[key]


def has_global_atoms(project_root: Path) -> bool:
    """Check if _keyword_index.json has _global_atoms section."""
    idx = read_index(project_root)
    return idx is not None and "_global_atoms" in idx


def ensure_global_atoms_section(project_root: Path) -> bool:
    """Add _global_atoms section if missing. Idempotent."""
    idx = read_index(project_root)
    if idx is None:
        idx = {"_global_atoms": []}
        return write_index(project_root, idx)
    if "_global_atoms" not in idx:
        idx["_global_atoms"] = []
        return write_index(project_root, idx)
    return True


def search_atoms(project_root: Path, keyword: str, phase: str = None) -> list[dict]:
    """Search for atoms matching a keyword, optionally filtered by phase.
    Returns list of atom dicts from _global_atoms section, priority-sorted:
    same phase: never > how-to > pitfall. same type: load all."""
    idx = read_index(project_root)
    if idx is None:
        return []

    key = keyword.lower()
    matched_ids = set()

    # Direct keyword match
    if key in idx:
        refs = idx[key]
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, str) and "-" in ref:
                    parts = ref.rsplit("-", 1)
                    if len(parts) == 2 and len(parts[1]) == 8:
                        try:
                            int(parts[1], 16)
                            matched_ids.add(ref)
                        except ValueError:
                            pass

    # Also search _global_atoms trigger fields directly
    for atom in idx.get("_global_atoms", []):
        for trigger in atom.get("trigger", []):
            if key in trigger.lower() or trigger.lower() in key:
                matched_ids.add(atom["id"])

    # Build result from _global_atoms
    result = []
    for atom in idx.get("_global_atoms", []):
        if atom["id"] in matched_ids:
            if phase and atom.get("phase") != phase:
                continue
            result.append(atom)

    # Sort: never > how-to > pitfall within same phase
    type_priority = {"never": 0, "how-to": 1, "pitfall": 2}
    result.sort(key=lambda a: type_priority.get(a.get("type"), 3))

    return result
