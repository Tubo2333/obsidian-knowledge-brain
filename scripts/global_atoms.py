#!/usr/bin/env python3
"""
obsidian-knowledge-brain v4.0 — Global Atom Pointer Table operations.
Single source of truth: ~/.obsidian-knowledge-brain/atoms.json
Read/write with .bak backup, .lock concurrency guard (10-min TTL), and full schema validation.
"""
import json
import hashlib
import os
import time
from pathlib import Path
from datetime import datetime, timezone

ATOMS_DIR = Path.home() / ".obsidian-knowledge-brain"
ATOMS_PATH = ATOMS_DIR / "atoms.json"
BAK_PATH = ATOMS_DIR / "atoms.json.bak"
LOCK_PATH = ATOMS_DIR / "atoms.json.lock"
UNINSTALLED_PATH = ATOMS_DIR / ".uninstalled"
LOCK_TTL_SECONDS = 600  # 10 minutes
VALID_TYPES = {"never", "how-to", "pitfall"}
VALID_PHASES = {"pre", "during", "post"}
MAX_TRIGGERS_PER_ATOM = 5
MAX_ONE_LINER_CHARS = 120

def ensure_atoms_dir() -> Path:
    """Create ~/.obsidian-knowledge-brain/ if it doesn't exist. Idempotent."""
    ATOMS_DIR.mkdir(parents=True, exist_ok=True)
    return ATOMS_DIR

def init_atoms() -> dict:
    """Create empty atoms.json skeleton. Returns the skeleton dict.
    Does NOT overwrite existing valid atoms.json."""
    if ATOMS_PATH.exists():
        existing = read_atoms()
        if existing is not None:
            return existing
    skeleton = {
        "meta": {
            "version": "4.0",
            "max_atoms": 20,
            "promotion_threshold": 2,
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "last_promotion": None
        },
        "atoms": []
    }
    write_atoms(skeleton)
    return skeleton

def compute_atom_id(domain: str, root_cause_id: str, atom_type: str) -> str:
    """Compute atom ID: {DOMAIN}-{SHA256(root_cause_id + type)[:8]}"""
    payload = f"{root_cause_id}{atom_type}"
    hash_hex = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    return f"{domain}-{hash_hex}"

def read_atoms() -> dict | None:
    """Read atoms.json with validation and .bak fallback.
    Returns None only if both atoms.json and .bak are unrecoverable."""
    for path in (ATOMS_PATH, BAK_PATH):
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if validate_schema(data)[0]:
                return data
        except (json.JSONDecodeError, OSError):
            continue
    return None

def write_atoms(data: dict) -> bool:
    """Write atoms.json with .bak backup + read-back validate.
    Returns True on success, False if write failed validation (rolled back)."""
    # Backup existing
    if ATOMS_PATH.exists():
        try:
            with open(ATOMS_PATH, "r", encoding="utf-8") as f:
                bak_content = f.read()
            with open(BAK_PATH, "w", encoding="utf-8") as f:
                f.write(bak_content)
        except OSError:
            pass  # .bak is best-effort

    # Write
    try:
        with open(ATOMS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        return False

    # Read-back validate
    try:
        with open(ATOMS_PATH, "r", encoding="utf-8") as f:
            written = json.load(f)
        valid, _ = validate_schema(written)
        if not valid:
            # Rollback from .bak
            if BAK_PATH.exists():
                with open(BAK_PATH, "r", encoding="utf-8") as f:
                    rollback = json.load(f)
                with open(ATOMS_PATH, "w", encoding="utf-8") as f:
                    json.dump(rollback, f, indent=2, ensure_ascii=False)
            return False
        return True
    except (json.JSONDecodeError, OSError):
        if BAK_PATH.exists():
            with open(BAK_PATH, "r", encoding="utf-8") as f:
                rollback = json.load(f)
            with open(ATOMS_PATH, "w", encoding="utf-8") as f:
                json.dump(rollback, f, indent=2, ensure_ascii=False)
        return False

def validate_schema(data: dict) -> tuple[bool, str]:
    """Full schema validation per spec §6.2 step 4.
    Returns (is_valid, error_message)."""
    if not isinstance(data, dict):
        return False, "atoms.json must be a JSON object"
    meta = data.get("meta")
    if not isinstance(meta, dict):
        return False, "meta block missing or not an object"
    if meta.get("version") != "4.0":
        return False, f"meta.version must be '4.0', got '{meta.get('version')}'"
    if not isinstance(meta.get("max_atoms"), (int, float)):
        return False, "meta.max_atoms missing or not numeric"
    atoms = data.get("atoms")
    if not isinstance(atoms, list):
        return False, "atoms must be a JSON array"

    seen_ids = set()
    for i, atom in enumerate(atoms):
        if not isinstance(atom, dict):
            return False, f"atom[{i}] is not an object"
        # id format: {DOMAIN}-{8hex}
        aid = atom.get("id", "")
        if not _validate_atom_id(aid):
            return False, f"atom[{i}].id '{aid}' must match {{DOMAIN}}-{{8hex}}"
        if aid in seen_ids:
            return False, f"atom[{i}].id '{aid}' duplicates earlier atom"
        seen_ids.add(aid)
        # type enum
        if atom.get("type") not in VALID_TYPES:
            return False, f"atom[{i}].type '{atom.get('type')}' not in {VALID_TYPES}"
        # phase enum
        if atom.get("phase") not in VALID_PHASES:
            return False, f"atom[{i}].phase '{atom.get('phase')}' not in {VALID_PHASES}"
        # trigger array 1-5
        trigger = atom.get("trigger")
        if not isinstance(trigger, list) or not (1 <= len(trigger) <= MAX_TRIGGERS_PER_ATOM):
            return False, f"atom[{i}].trigger must be array of 1-5 strings, got {len(trigger) if isinstance(trigger, list) else type(trigger).__name__}"
        # one_liner ≤ 120 chars
        one_liner = atom.get("one_liner", "")
        if len(one_liner) > MAX_ONE_LINER_CHARS:
            return False, f"atom[{i}].one_liner exceeds {MAX_ONE_LINER_CHARS} chars ({len(one_liner)})"
        # pointer must contain #
        pointer = atom.get("pointer", "")
        if "#" not in pointer:
            return False, f"atom[{i}].pointer '{pointer}' must contain '#' for line range"
        # project_origin must be array
        if not isinstance(atom.get("project_origin"), list):
            return False, f"atom[{i}].project_origin must be an array"
        # promoted must be valid ISO date
        promoted = atom.get("promoted", "")
        if not promoted:
            return False, f"atom[{i}].promoted is required"
        try:
            datetime.fromisoformat(promoted)
        except (ValueError, TypeError):
            return False, f"atom[{i}].promoted '{promoted}' is not a valid ISO date"

    # Cap check: active atoms (demoted != true) ≤ max_atoms
    active_count = sum(1 for a in atoms if not a.get("demoted", False))
    max_atoms = meta["max_atoms"]
    if active_count > max_atoms:
        return False, f"Active atom count ({active_count}) exceeds max_atoms ({max_atoms})"

    return True, ""

def _validate_atom_id(atom_id: str) -> bool:
    """Validate atom ID format: {DOMAIN}-{8 lowercase hex chars}"""
    parts = atom_id.rsplit("-", 1)
    if len(parts) != 2:
        return False
    domain, hash_part = parts
    if not domain or not hash_part:
        return False
    if len(hash_part) != 8:
        return False
    try:
        int(hash_part, 16)
    except ValueError:
        return False
    return True

def active_atom_count(data: dict) -> int:
    """Count active atoms (demoted != true)."""
    return sum(1 for a in data.get("atoms", []) if not a.get("demoted", False))

def acquire_lock() -> bool:
    """Try to acquire the promotion lock. Cleans stale locks (>10 min).
    Returns True if lock acquired, False if genuine contention."""
    if LOCK_PATH.exists():
        try:
            with open(LOCK_PATH, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
            lock_time = datetime.fromisoformat(lock_data["timestamp"])
            # Handle both naive (legacy) and aware timestamps
            if lock_time.tzinfo is None:
                lock_time = lock_time.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - lock_time).total_seconds()
            if age > LOCK_TTL_SECONDS:
                LOCK_PATH.unlink()  # stale, remove
            else:
                return False  # genuine concurrent access
        except (json.JSONDecodeError, KeyError, ValueError, TypeError, OSError):
            LOCK_PATH.unlink()  # corrupt lock, remove

    try:
        with open(LOCK_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "pid": os.getpid(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, f)
        return True
    except OSError:
        return False

def release_lock():
    """Release the promotion lock."""
    try:
        LOCK_PATH.unlink()
    except OSError:
        pass  # already gone

def promote_atom(atom_data: dict) -> tuple[bool, str]:
    """Full promotion write protocol per spec §6.2.
    atom_data must have: id, type, phase, trigger, pointer, project_origin, one_liner
    Returns (success, message)."""
    # Early validation — reject before acquiring lock
    required = ["id", "type", "phase", "trigger", "pointer", "project_origin", "one_liner"]
    missing = [k for k in required if k not in atom_data]
    if missing:
        return False, f"Missing required fields: {missing}"

    if not acquire_lock():
        return False, "Lock contention: another promotion in progress"

    try:
        data = read_atoms()
        if data is None:
            return False, "Cannot read atoms.json"

        # Check for existing atom with same ID
        existing_idx = None
        for i, atom in enumerate(data["atoms"]):
            if atom["id"] == atom_data["id"]:
                existing_idx = i
                break

        if existing_idx is not None:
            existing = data["atoms"][existing_idx]
            if not existing.get("demoted", False):
                # Update project_origin
                for proj in atom_data.get("project_origin", []):
                    if proj not in existing["project_origin"]:
                        existing["project_origin"].append(proj)
                data["atoms"][existing_idx] = existing
                msg = f"Atom {atom_data['id']} updated (project_origin merged)"
            else:
                # Reactivate
                existing["demoted"] = False
                existing["demoted_date"] = None
                existing["pointer_broken"] = False
                existing["promoted"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                for proj in atom_data.get("project_origin", []):
                    if proj not in existing["project_origin"]:
                        existing["project_origin"].append(proj)
                data["atoms"][existing_idx] = existing
                msg = f"Atom {atom_data['id']} 重新激活 (reactivated)"
        else:
            # Check 20-atom cap
            if active_atom_count(data) >= data["meta"]["max_atoms"]:
                # Emergency eviction
                evicted = _emergency_evict(data)
                if evicted is None:
                    release_lock()
                    active_list = sorted(
                        [a for a in data["atoms"] if not a.get("demoted", False)],
                        key=lambda a: a.get("last_triggered", a["promoted"]),
                        reverse=True
                    )
                    return False, (
                        f"20 active atoms at capacity. All are recently triggered. "
                        f"Manual demotion needed. Active atoms: "
                        f"{[(a['id'], a.get('last_triggered', a['promoted'])) for a in active_list]}"
                    )

            # Set defaults for new atom
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            atom_data.setdefault("promoted", now)
            atom_data.setdefault("last_triggered", now)
            atom_data.setdefault("demoted", False)
            atom_data.setdefault("demoted_date", None)
            atom_data.setdefault("pointer_broken", False)
            data["atoms"].append(atom_data)
            data["meta"]["last_promotion"] = now
            msg = f"Atom {atom_data['id']} promoted to global table"

        if not write_atoms(data):
            return False, "Write + validate failed (rolled back)"

        return True, msg
    finally:
        release_lock()

def _emergency_evict(data: dict) -> str | None:
    """Emergency eviction when cap exceeded. Priority:
    1. pointer_broken: true
    2. Longest time since last_triggered
    3. Fewest project_origin entries
    Returns evicted atom ID, or None if no candidate."""
    active = [(i, a) for i, a in enumerate(data["atoms"]) if not a.get("demoted", False)]

    # Priority 1: pointer_broken
    broken = [(i, a) for i, a in active if a.get("pointer_broken", False)]
    if broken:
        broken.sort(key=lambda x: x[1].get("last_triggered", x[1]["promoted"]))
        idx, atom = broken[0]
        data["atoms"][idx]["demoted"] = True
        data["atoms"][idx]["demoted_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return atom["id"]

    # Priority 2: longest time since last_triggered
    # Priority 3 (tiebreaker): fewest project_origin
    active.sort(key=lambda x: (
        x[1].get("last_triggered", x[1]["promoted"]),
        len(x[1].get("project_origin", []))
    ))
    idx, atom = active[0]
    data["atoms"][idx]["demoted"] = True
    data["atoms"][idx]["demoted_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return atom["id"]

def mark_demoted(atom_id: str) -> bool:
    """T3: mark atom as demoted. Does NOT delete (90-day sync window)."""
    if not acquire_lock():
        return False
    try:
        data = read_atoms()
        if data is None:
            return False
        for atom in data["atoms"]:
            if atom["id"] == atom_id:
                atom["demoted"] = True
                atom["demoted_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                return write_atoms(data)
        return False
    finally:
        release_lock()

def cleanup_demoted(older_than_days: int = 90) -> list[str]:
    """T3: final removal of atoms demoted > older_than_days ago.
    Returns list of removed atom IDs."""
    if not acquire_lock():
        return []
    try:
        data = read_atoms()
        if data is None:
            return []
        cutoff = datetime.now(timezone.utc)
        removed = []
        new_atoms = []
        for atom in data["atoms"]:
            if atom.get("demoted", False) and atom.get("demoted_date"):
                try:
                    demoted_date = datetime.fromisoformat(atom["demoted_date"])
                    # Handle timezone-naive datetimes from legacy atoms
                    if demoted_date.tzinfo is None:
                        demoted_date = demoted_date.replace(tzinfo=timezone.utc)
                    if (cutoff - demoted_date).days > older_than_days:
                        removed.append(atom["id"])
                        continue
                except ValueError:
                    pass
            new_atoms.append(atom)
        if removed:
            data["atoms"] = new_atoms
            write_atoms(data)
        return removed
    finally:
        release_lock()

def get_atoms_by_phase(phase: str) -> list[dict]:
    """Get all active atoms for a given phase (pre/during/post)."""
    data = read_atoms()
    if data is None:
        return []
    return [a for a in data.get("atoms", [])
            if a.get("phase") == phase and not a.get("demoted", False)]

def is_uninstalled() -> bool:
    """Check if .uninstalled marker exists."""
    return UNINSTALLED_PATH.exists()
