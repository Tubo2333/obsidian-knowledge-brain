#!/usr/bin/env python3
"""
obsidian-knowledge-brain v4.0 — Benchmark Harness.
Measures wall-clock time, success rate, and error types for 8 representative tasks.
All measurements are real (no estimation). Outputs JSON for analysis.
"""
import json
import sys
import time
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from global_atoms import (
    init_atoms, read_atoms, write_atoms, validate_schema,
    compute_atom_id, promote_atom, mark_demoted, cleanup_demoted,
    acquire_lock, release_lock, active_atom_count, ensure_atoms_dir,
    ATOMS_PATH, BAK_PATH, LOCK_PATH
)
from keyword_index import (
    read_index, write_index, safe_merge_sync,
    ensure_global_atoms_section, has_global_atoms
)
from pre_action import detect_format, inject, remove, is_already_injected

# ── Instrumentation ──

class BenchmarkRun:
    def __init__(self, name, category, difficulty):
        self.name = name
        self.category = category
        self.difficulty = difficulty
        self.start_time = None
        self.end_time = None
        self.success = None
        self.error_type = None
        self.error_detail = None
        self.operations = 0  # function calls
        self.notes = ""

    def start(self):
        self.start_time = time.perf_counter()
        return self

    def stop(self, success=True, error_type=None, error_detail=None):
        self.end_time = time.perf_counter()
        self.success = success
        self.error_type = error_type
        self.error_detail = error_detail
        return self

    @property
    def elapsed_sec(self):
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 4)
        return None

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "difficulty": self.difficulty,
            "elapsed_sec": self.elapsed_sec,
            "success": self.success,
            "error_type": self.error_type,
            "error_detail": self.error_detail,
            "operations": self.operations,
            "notes": self.notes,
        }


results = []

def op(run, n=1):
    run.operations += n

def force_empty_atoms():
    """Force-create empty atoms.json (unlike init_atoms, always creates new skeleton)."""
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

def cleanup_test_atoms(data):
    """Remove TEST-* atoms from data."""
    if data and data.get("atoms"):
        data["atoms"] = [a for a in data["atoms"] if not a["id"].startswith("TEST-")]
    return data


# ── Task 1: install.py --dry-run ──
run1 = BenchmarkRun("install.py --dry-run", "CLI/Install", "simple").start()
try:
    import subprocess
    r = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "install.py"), "--dry-run"],
        capture_output=True, text=True, timeout=15, cwd=str(SCRIPT_DIR.parent.parent.parent.parent)
    )
    op(run1)
    run1.stop(success=r.returncode == 0,
              error_type="cli-exit-code" if r.returncode != 0 else None,
              error_detail=r.stderr[:200] if r.returncode != 0 else None)
    run1.notes = f"exit_code={r.returncode}"
except Exception as e:
    run1.stop(success=False, error_type="exception", error_detail=str(e)[:200])
results.append(run1)


# ── Task 2: force_empty + schema validate ──
run2 = BenchmarkRun("init + validate schema", "Data Layer", "simple").start()
try:
    orig = read_atoms()
    op(run2)

    skeleton = force_empty_atoms()
    op(run2)
    valid, err = validate_schema(skeleton)
    op(run2)

    assert valid, f"Empty skeleton should be valid: {err}"
    assert skeleton["meta"]["version"] == "4.0"
    assert skeleton["meta"]["max_atoms"] == 20
    assert skeleton["atoms"] == []
    run2.stop(success=True)
    run2.notes = f"version={skeleton['meta']['version']}, max_atoms={skeleton['meta']['max_atoms']}, atoms=0"

    # Restore
    if orig:
        write_atoms(cleanup_test_atoms(orig))
        op(run2)
except Exception as e:
    run2.stop(success=False, error_type=type(e).__name__, error_detail=str(e)[:200])
    # Best-effort restore
    try:
        if orig:
            write_atoms(cleanup_test_atoms(orig))
    except:
        pass
results.append(run2)


# ── Task 3: promote_atom full protocol ──
run3 = BenchmarkRun("promote_atom (new + reactivate + evict)", "Promotion", "medium").start()
try:
    orig = read_atoms()
    op(run3)

    # Start with clean slate
    force_empty_atoms()
    op(run3)

    # Promote a new atom
    aid = compute_atom_id("TEST", "benchmark-promote", "never")
    atom = {
        "id": aid,
        "type": "never",
        "phase": "pre",
        "trigger": ["benchmark-test"],
        "pointer": "rules/test.md#L1-L3",
        "project_origin": ["ProjectA", "ProjectB"],
        "one_liner": "NEVER use benchmark-test — it's a test"
    }
    ok, msg = promote_atom(atom)
    op(run3)
    assert ok, f"Promote failed: {msg}"

    # Verify
    data = read_atoms()
    op(run3)
    active = active_atom_count(data)
    assert active == 1, f"Expected 1 active atom, got {active}"
    found = any(a["id"] == aid for a in data["atoms"])
    assert found, f"Atom {aid} not found in table"

    # Reactivate test (demote then re-promote)
    mark_demoted(aid)
    op(run3)
    atom2 = {
        "id": aid,
        "type": "never",
        "phase": "pre",
        "trigger": ["benchmark-test"],
        "pointer": "rules/test.md#L1-L3",
        "project_origin": ["ProjectA", "ProjectB", "ProjectC"],
        "one_liner": "NEVER use benchmark-test — it's a test"
    }
    ok, msg = promote_atom(atom2)
    op(run3)
    assert ok, f"Reactivate failed: {msg}"

    data = read_atoms()
    op(run3)
    for a in data["atoms"]:
        if a["id"] == aid:
            assert not a.get("demoted", False), "Should be reactivated"
            break

    run3.stop(success=True)
    run3.notes = f"atom_id={aid}, reactivated=true, active={active_atom_count(data)}"

    # Restore original (cleaned)
    if orig:
        write_atoms(cleanup_test_atoms(orig))
        op(run3)
except Exception as e:
    run3.stop(success=False, error_type=type(e).__name__, error_detail=str(e)[:200])
    try:
        if orig:
            write_atoms(cleanup_test_atoms(orig))
    except:
        pass
results.append(run3)


# ── Task 4: safe_merge_sync ──
run4 = BenchmarkRun("safe_merge_sync (empty skip + new + update)", "Keyword Index", "medium").start()
try:
    project_root = Path("D:/C-file")
    orig_idx = read_index(project_root)
    op(run4)

    # Test 1: ensure_global_atoms_section
    ok = ensure_global_atoms_section(project_root)
    op(run4)
    assert ok, "ensure_global_atoms_section failed"
    assert has_global_atoms(project_root), "should have _global_atoms"

    # Test 2: safe_merge_sync (should detect mtime or run merge)
    changed, msg = safe_merge_sync(project_root)
    op(run4)
    # changed may be True or False depending on mtime — both OK
    run4.stop(success=True)
    run4.notes = f"changed={changed}, msg={msg}, has_global_atoms={has_global_atoms(project_root)}"

    # Restore
    if orig_idx:
        write_index(project_root, orig_idx)
        op(run4)
except Exception as e:
    run4.stop(success=False, error_type="assertion", error_detail=str(e)[:200])
results.append(run4)


# ── Task 5: pre_action inject + detect + remove ──
run5 = BenchmarkRun("pre_action inject/detect/remove", "Pre-Action", "medium").start()
try:
    test_content = "# Test Project\n\nSome content here.\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        tmp = f.name
    op(run5)

    # Detect format
    fmt = detect_format(Path(tmp))
    op(run5)
    assert fmt == 'markdown', f"Expected markdown, got {fmt}"

    # Inject
    ok, msg = inject(Path(tmp))
    op(run5)
    assert ok, f"Inject failed: {msg}"
    assert is_already_injected(Path(tmp)), "Should be injected"

    # Remove
    ok, msg = remove(Path(tmp))
    op(run5)
    assert ok, f"Remove failed: {msg}"
    assert not is_already_injected(Path(tmp)), "Should be removed"

    # Verify original content preserved (rough check)
    with open(tmp, 'r') as f2:
        final = f2.read()
    op(run5)
    assert "Test Project" in final
    assert "Some content" in final

    os.unlink(tmp)
    run5.stop(success=True)
    run5.notes = f"format={fmt}, inject+remove roundtrip OK"
except Exception as e:
    run5.stop(success=False, error_type="assertion", error_detail=str(e)[:200])
    try:
        os.unlink(tmp)
    except:
        pass
results.append(run5)


# ── Task 6: mark_demoted + cleanup_demoted ──
run6 = BenchmarkRun("mark_demoted + cleanup", "Lifecycle", "medium").start()
try:
    orig = read_atoms()
    op(run6)

    # Seed a test atom
    aid = compute_atom_id("TEST", "benchmark-lifecycle", "pitfall")
    atom = {
        "id": aid,
        "type": "pitfall",
        "phase": "post",
        "trigger": ["lifecycle-test"],
        "pointer": "rules/test.md#L1-L3",
        "project_origin": ["ProjectX"],
        "one_liner": "Test lifecycle atom"
    }
    ok, msg = promote_atom(atom)
    op(run6)
    assert ok, f"Seed promote failed: {msg}"

    # Mark demoted
    ok = mark_demoted(aid)
    op(run6)
    assert ok, "mark_demoted failed"

    data = read_atoms()
    op(run6)
    found = False
    for a in data["atoms"]:
        if a["id"] == aid:
            assert a["demoted"] == True, "Should be demoted"
            assert a["demoted_date"] is not None, "Should have demoted_date"
            found = True
            break
    assert found, f"Atom {aid} not found"
    assert active_atom_count(data) < len(data["atoms"]), "Demoted atoms excluded from active count"

    # Cleanup with -1 days (force immediate removal)
    removed = cleanup_demoted(older_than_days=-1)
    op(run6)
    assert aid in removed, f"Should clean up test atom, removed={removed}"

    run6.stop(success=True)
    run6.notes = f"atom_id={aid}, demoted+cleaned OK"

    # Restore (cleaned)
    if orig:
        write_atoms(cleanup_test_atoms(orig))
    op(run6)
except Exception as e:
    run6.stop(success=False, error_type=type(e).__name__, error_detail=str(e)[:200])
    try:
        if orig:
            write_atoms(cleanup_test_atoms(orig))
    except:
        pass
results.append(run6)


# ── Task 7: Corruption recovery ──
run7 = BenchmarkRun("corruption recovery (.bak fallback)", "Recovery", "complex").start()
try:
    orig_data = read_atoms()
    op(run7)

    # Corrupt atoms.json
    with open(ATOMS_PATH, 'w') as f:
        f.write("not valid json!!!")
    op(run7)

    # Should recover from .bak
    recovered = read_atoms()
    op(run7)
    assert recovered is not None, "Should recover from .bak"
    assert recovered.get("meta", {}).get("version") == "4.0"
    run7.stop(success=True)
    run7.notes = "recovered from .bak successfully"

    # Restore
    write_atoms(orig_data)
    op(run7)
except Exception as e:
    run7.stop(success=False, error_type="assertion", error_detail=str(e)[:200])
    # Try to recover
    try:
        if BAK_PATH.exists():
            with open(BAK_PATH) as f:
                good = json.load(f)
            write_atoms(good)
    except:
        pass
results.append(run7)


# ── Task 8: Lock acquire/release ──
run8 = BenchmarkRun("lock acquire/release (incl. stale cleanup)", "Concurrency", "medium").start()
try:
    # Ensure no leftover lock
    if LOCK_PATH.exists():
        LOCK_PATH.unlink()

    # Acquire
    ok = acquire_lock()
    op(run8)
    assert ok, "Should acquire lock"
    assert LOCK_PATH.exists()

    # Release
    release_lock()
    op(run8)
    assert not LOCK_PATH.exists(), "Lock should be released"

    # Stale lock test
    old_lock = {"pid": 99999, "timestamp": "2026-06-20T00:00:00"}
    with open(LOCK_PATH, 'w') as f:
        json.dump(old_lock, f)
    op(run8)

    # Should clean stale lock and succeed
    ok = acquire_lock()
    op(run8)
    assert ok, "Should acquire after stale lock cleanup"
    release_lock()
    op(run8)

    run8.stop(success=True)
    run8.notes = "stale lock auto-cleaned"
except Exception as e:
    run8.stop(success=False, error_type="assertion", error_detail=str(e)[:200])
    try:
        release_lock()
    except:
        pass
results.append(run8)


# ── Summarize ──

print("\n" + "=" * 80)
print("OBSIDIAN KNOWLEDGE BRAIN v4.0 — BENCHMARK RESULTS")
print("=" * 80)

total = len(results)
successes = sum(1 for r in results if r.success)
times = [r.elapsed_sec for r in results if r.elapsed_sec is not None]
total_ops = sum(r.operations for r in results)

print(f"\nTasks: {total} | Success: {successes}/{total} ({successes/total*100:.1f}%)")
print(f"Total wall-clock: {sum(times):.4f}s")
print(f"Avg time/task: {sum(times)/len(times):.4f}s")
print(f"Min time: {min(times):.4f}s | Max time: {max(times):.4f}s")
print(f"Total operations (function calls): {total_ops}")
print(f"Avg ops/task: {total_ops/total:.1f}")

print(f"\n{'Task':<40} {'Category':<15} {'Diff':<8} {'Time(s)':<10} {'Ops':<5} {'OK':<5}")
print("-" * 85)
for r in results:
    ok = "[PASS]" if r.success else "[FAIL]"
    err = f" [{r.error_type}]" if r.error_type else ""
    print(f"{r.name:<40} {r.category:<15} {r.difficulty:<8} {str(r.elapsed_sec):<10} {r.operations:<5} {ok:<5}{err}")

print(f"\n{'AVERAGE':<40} {'':<15} {'':<8} {sum(times)/len(times):.4f}s     {total_ops/total:.1f}   {successes/total*100:.0f}%")

# ── Error breakdown ──
errors = [r for r in results if not r.success]
if errors:
    print(f"\n── Error Breakdown ──")
    for r in errors:
        print(f"  [{r.error_type}] {r.name}: {r.error_detail}")

# ── By difficulty ──
print(f"\n── By Difficulty ──")
for diff in ["simple", "medium", "complex"]:
    group = [r for r in results if r.difficulty == diff]
    if group:
        avg_t = sum(r.elapsed_sec for r in group) / len(group)
        rate = sum(1 for r in group if r.success) / len(group) * 100
        print(f"  {diff}: {len(group)} tasks, avg {avg_t:.4f}s, {rate:.0f}% success")

# ── By category ──
print(f"\n── By Category ──")
cats = {}
for r in results:
    cats.setdefault(r.category, []).append(r)
for cat, group in sorted(cats.items()):
    avg_t = sum(r.elapsed_sec for r in group) / len(group)
    print(f"  {cat}: {len(group)} tasks, avg {avg_t:.4f}s")

# ── NOTES ──
print(f"""
── Notes ──
Token/cost metrics: N/A. These are pure Python operations — no LLM API calls involved.
The v4.0 core modules (global_atoms, keyword_index, pre_action, install.py) use stdlib only.
Token consumption happens when an AI Agent reads SKILL.md and follows protocols — that is
session-dependent and varies by project size and Agent model.

Model pricing reference (for Agent sessions, not these Python benchmarks):
  Claude Opus 4:    $15.00/M input, $75.00/M output
  Claude Sonnet 4:  $3.00/M input, $15.00/M output
  DeepSeek v4:      ~$0.14/M input, ~$0.28/M output

Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
Python: {sys.version.split()[0]}
""")

# ── Write JSON ──
output_json = Path("D:/C-file/docs/superpowers/benchmark_results.json")
output_json.parent.mkdir(parents=True, exist_ok=True)
with open(output_json, 'w') as f:
    json.dump({
        "meta": {
            "skill": "obsidian-knowledge-brain",
            "version": "4.0",
            "date": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
        },
        "summary": {
            "total_tasks": total,
            "success_count": successes,
            "success_rate_pct": round(successes / total * 100, 1),
            "total_time_sec": round(sum(times), 4),
            "avg_time_sec": round(sum(times) / len(times), 4),
            "min_time_sec": round(min(times), 4),
            "max_time_sec": round(max(times), 4),
            "total_operations": total_ops,
            "avg_ops_per_task": round(total_ops / total, 1),
        },
        "tasks": [r.to_dict() for r in results],
    }, f, indent=2, ensure_ascii=False)

print(f"JSON written to: {output_json}")
