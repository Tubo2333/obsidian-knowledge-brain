#!/usr/bin/env python3
"""SessionStart hook — injects a concise briefing into Agent context.

v3.0 T1 Protocol (design: docs/superpowers/specs/2026-06-16-obsidian-brain-v3-design.md S4.1):
  1. Crash recovery: stale .session_active marker
  2. T2 completion check (Scheme C safety net / F4)
  3. Inbox drain: extract [DECISION:] [ERROR:] from _phase1_inbox.md
  4. Cold-start counter: read/update cold_start YAML frontmatter in inbox
  5. Health report summary from HEALTH_REPORT.md
  6. Current project status from projects/<slug>.md

Outputs ≤30-line bilingual briefing. Writes .session_active marker.
"""

import os
import re
import time
from pathlib import Path


# ── Platform-agnostic path detection ──────────────────────────────────────────

BASE_CANDIDATES = [".claude", ".cursor", ".gemini", ".codex"]  # v3.0: multi-platform

def get_project_root():
    """Detect project root from script location or CWD. Checks multiple platform dirs."""
    script_dir = Path(__file__).resolve().parent  # <base>/scripts/
    candidate = script_dir.parent.parent           # project root
    if (candidate / "CLAUDE.md").exists() and any((candidate / d).exists() for d in BASE_CANDIDATES):
        return candidate
    # Fallback: walk up from CWD
    cwd = Path.cwd().resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "CLAUDE.md").exists() and any((p / d).exists() for d in BASE_CANDIDATES):
            return p
    return cwd

PROJECT_ROOT = get_project_root()
# Detect which platform base dir actually exists (v3.0: multi-platform)
BASE = next((PROJECT_ROOT / d for d in BASE_CANDIDATES if (PROJECT_ROOT / d).exists()), PROJECT_ROOT / ".claude")
SESSION_MARKER = BASE / ".session_active"
INBOX = BASE / "memory" / "_phase1_inbox.md"
HEALTH_REPORT = BASE / "HEALTH_REPORT.md"
PROJECTS_DIR = BASE / "projects"
STALE_THRESHOLD = 24 * 3600  # 24 hours


def detect_project():
    """Data-driven project detection: read Path: field from project files, match CWD.
    No hardcoded project_map — reads directly from projects/*.md filesystem."""
    cwd = Path.cwd()
    cwd_str = str(cwd).replace("\\", "/").lower()

    if not PROJECTS_DIR.exists():
        return None

    for pf in sorted(PROJECTS_DIR.glob("*.md")):
        if pf.name.startswith("_"):
            continue
        try:
            with open(pf, encoding="utf-8") as f:
                body = f.read()
        except Exception:
            continue
        m = re.search(r"\*\*Path\*\*:\s*`([^`]+)`", body)
        if m:
            pp = m.group(1).replace("\\", "/").rstrip("/").lower()
            if pp and pp in cwd_str:
                return pf.stem
        # Also try matching slug against directory name
        slug = pf.stem
        if slug in cwd_str:
            return slug

    # Fallback for monorepo root: check inbox for most recent project mention
    if INBOX.exists():
        try:
            with open(INBOX, encoding="utf-8") as f:
                inbox_text = f.read()
            m = re.findall(r"project:\s*(\S+)", inbox_text)
            if m:
                return m[-1]  # last mentioned project
        except Exception:
            pass
    return None


def check_crash():
    """Check if previous session crashed (stale .session_active marker)."""
    if not SESSION_MARKER.exists():
        return None

    try:
        mtime = os.path.getmtime(str(SESSION_MARKER))
        age = time.time() - mtime
        if age > STALE_THRESHOLD:
            with open(SESSION_MARKER, encoding="utf-8") as f:
                old_session = f.read().strip()
            return f"Session `{old_session}` (crashed {age/3600:.1f}h ago)"
    except Exception:
        pass
    return None


def check_t2_completion():
    """Scheme C T1 safety net: check if previous session completed T2 close protocol.
    Returns (completed: bool, message: str)."""
    if not INBOX.exists():
        return False, "Inbox not yet created — first session."
    try:
        inbox_mtime = os.path.getmtime(str(INBOX))
    except Exception:
        return False, "Cannot read inbox modification time."

    if SESSION_MARKER.exists():
        try:
            marker_mtime = os.path.getmtime(str(SESSION_MARKER))
            # If inbox was modified AFTER session marker was created,
            # the previous session wrote to it (T2 or F3 active)
            if inbox_mtime >= marker_mtime - 60:  # 60s tolerance
                return True, "Inbox updated — previous session captured knowledge."
        except Exception:
            pass

    # If we can't verify, assume incomplete
    return False, "Cannot verify T2 completion. Inbox may be stale."


def read_inbox_tail(n=50):
    """Read last N lines of _phase1_inbox.md, extract [DECISION:] and [ERROR:]."""
    if not INBOX.exists():
        return []

    try:
        with open(INBOX, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    tail = lines[-n:] if len(lines) > n else lines
    entries = []
    for line in tail:
        match = re.match(r'\s*\[(DECISION|ERROR):\s*(.+?)\s*\]', line)
        if match:
            entries.append(f"[{match.group(1)}]: {match.group(2)}")
    return entries


def read_health_summary():
    """Read HEALTH_REPORT.md summary line. Returns clean, machine-parseable output."""
    if not HEALTH_REPORT.exists():
        return "Health report: not yet generated."

    try:
        with open(HEALTH_REPORT, encoding="utf-8") as f:
            for line in f:
                if line.startswith("**Summary**"):
                    # Extract clean text: strip markdown formatting
                    clean = line.strip()
                    clean = re.sub(r'\*+', '', clean)  # strip all asterisks
                    clean = clean.replace("Summary:", "").strip()
                    return clean or line.strip()
    except Exception:
        pass
    return "Health report: unreadable."


def read_project_status(slug):
    """Read project status and blockers from projects/<slug>.md."""
    if not slug:
        return None

    proj_file = PROJECTS_DIR / f"{slug}.md"
    if not proj_file.exists():
        return None

    try:
        with open(proj_file, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    status = "unknown"
    blockers = "none"

    m = re.search(r'status:\s*(\S+)', content)
    if m:
        status = m.group(1)

    m = re.search(r'## Blockers\s*\n\s*(.+?)(?:\n|$)', content, re.MULTILINE)
    if m:
        blockers = m.group(1).strip()
        if blockers.startswith("<"):
            blockers = "none"

    return f"Project `{slug}`: status={status}, blockers={blockers}"


def count_annotations_from_filesystem(base):
    """Count total annotations by scanning memory/ subdirectories.
    Each .md file in pitfalls/decisions/preferences/reference = 1 annotation.
    This is the authoritative source — no Agent-dependent manual counting."""
    count = 0
    for subdir in ["pitfalls", "decisions", "preferences", "reference"]:
        d = base / "memory" / subdir
        if d.exists():
            count += len([f for f in d.iterdir() if f.suffix == ".md"])
    return count


def read_cold_start_counter():
    """v3.0 S3.10: Read cold-start counter from _phase1_inbox.md YAML frontmatter.
    Returns dict: {total_annotations, sessions_observed, threshold, mode} or default.
    total_annotations is derived from FILESYSTEM (not Agent memory) — authoritative."""
    default = {"total_annotations": 0, "sessions_observed": 0, "threshold": 20, "mode": "cold_start"}
    if not INBOX.exists():
        return default
    try:
        with open(INBOX, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return default
    # Parse YAML frontmatter
    if not text.startswith("---"):
        return default
    parts = text.split("---", 2)
    if len(parts) < 3:
        return default
    fm_text = parts[1]
    # Look for cold_start block
    cs = {}
    in_cs = False
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("cold_start:"):
            in_cs = True
            continue
        if in_cs:
            m = re.match(r"(\w+):\s*(.+)$", stripped)
            if m:
                key, val = m.group(1), m.group(2).strip().rstrip("#").strip()
                if key == "total_annotations" or key == "sessions_observed":
                    try:
                        cs[key] = int(val)
                    except ValueError:
                        cs[key] = 0
                elif key == "threshold":
                    try:
                        cs[key] = int(val)
                    except ValueError:
                        cs[key] = 20
                elif key == "mode":
                    cs[key] = val.strip('"').strip("'")
            if not stripped or stripped.startswith("---"):
                break
    if cs:
        result = dict(default, **cs)
        # Persist: always increment sessions_observed for this new session
        result["sessions_observed"] = result.get("sessions_observed", 0) + 1
        # Override total_annotations with authoritative filesystem count
        result["total_annotations"] = count_annotations_from_filesystem(BASE)
        return result
    # No YAML block found — use filesystem count as ground truth
    default["total_annotations"] = count_annotations_from_filesystem(BASE)
    return default


def write_cold_start_counter(cs):
    """v3.0 S3.10: Write updated cold-start counter back to _phase1_inbox.md YAML frontmatter."""
    if not INBOX.exists():
        return
    try:
        with open(INBOX, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return
    if not text.startswith("---"):
        return
    parts = text.split("---", 2)
    if len(parts) < 3:
        return
    old_fm = parts[1]
    body = parts[2]

    # Rebuild frontmatter with updated cold_start block
    new_fm_lines = []
    in_cs = False
    for line in old_fm.split("\n"):
        stripped = line.strip()
        if stripped.startswith("cold_start:"):
            in_cs = True
            new_fm_lines.append(line)
            continue
        if in_cs:
            if not stripped or stripped.startswith("---") or not re.match(r"\w+:", stripped):
                in_cs = False
                new_fm_lines.append(line)
                continue
            # Skip old counter lines — we'll append updated ones
            continue
        new_fm_lines.append(line)

    # Append updated cold_start block
    cs_block = (
        f"  total_annotations: {cs['total_annotations']}\n"
        f"  sessions_observed: {cs['sessions_observed']}\n"
        f"  threshold: {cs['threshold']}\n"
        f"  mode: {cs['mode']}"
    )
    # Find cold_start line and replace/append after it
    has_cs_line = any("cold_start:" in l for l in new_fm_lines)
    updated_fm = "\n".join(new_fm_lines)
    if has_cs_line:
        # Append the updated block after cold_start: line
        updated_fm = re.sub(
            r"(cold_start:.*)",
            rf"\1\n{cs_block}",
            updated_fm
        )
    else:
        updated_fm += f"\ncold_start:\n{cs_block}"

    # Write back
    new_text = f"---\n{updated_fm}\n---{body}"
    try:
        with open(INBOX, "w", encoding="utf-8") as f:
            f.write(new_text)
    except Exception:
        pass


def main():
    lines = []
    lines.append("## Session Briefing / 会话简报")
    lines.append("")

    # 1. Crash recovery
    crash = check_crash()
    if crash:
        lines.append(f"**RECOVERY**: Previous session crashed — {crash}.")
        lines.append("Check for partial state before proceeding.")
        lines.append("")

    # 2. T2 completion check (Scheme C safety net / F4)
    t2_ok, t2_msg = check_t2_completion()
    if not t2_ok and not crash and INBOX.exists():
        lines.append(f"**T2 Warning**: Previous session may not have completed close protocol. ({t2_msg})")
        lines.append("")

    # 3. Last session's learnings
    entries = read_inbox_tail()
    if entries:
        lines.append("**Last session**:")
        for e in entries[-5:]:  # Max 5 most recent
            lines.append(f"- {e}")
    else:
        lines.append("**Last session**: No decisions or errors recorded. (This is expected for first sessions.)")
    lines.append("")

    # 4. v3.0 Cold-start counter / 冷启动计数器 (S3.10)
    cs = read_cold_start_counter()
    # Dedup guard: if .session_active is recent (<1h), this is a re-invocation, undo the +1
    if SESSION_MARKER.exists():
        try:
            if time.time() - os.path.getmtime(str(SESSION_MARKER)) < 3600:
                cs["sessions_observed"] = max(0, cs["sessions_observed"] - 1)
        except Exception: pass
    if cs["total_annotations"] >= cs["threshold"] and cs["sessions_observed"] >= 3:
        if cs["mode"] == "cold_start":
            cs["mode"] = "active"
            lines.append("**Memory Engine / 记忆引擎**: ACTIVE. Now detecting patterns across sessions — when the same error appears repeatedly, you'll get automatic warnings with known fixes. / 已激活，现在会自动检测跨会话的错误模式并提供已知修复方案。")
            lines.append("")
    else:
        remaining = cs['threshold'] - cs['total_annotations']
        lines.append(f"**Learning / 学习中**: {cs['total_annotations']}/{cs['threshold']} lessons stored across {cs['sessions_observed']} sessions. After {remaining} more and {3 - cs['sessions_observed']} more sessions, automatic pattern detection starts. / 已存储 {cs['total_annotations']} 条经验，还需 {remaining} 条即可开启自动模式识别。")
        lines.append("")
    write_cold_start_counter(cs)

    # 5. Health report / 健康报告
    health = read_health_summary()
    lines.append(f"**Health / 健康**: {health}")
    lines.append("")

    # 6. Project status
    slug = detect_project()
    if slug:
        proj_status = read_project_status(slug)
        if proj_status:
            lines.append(f"**{proj_status}**")
    else:
        lines.append("**Project**: Not detected (CWD outside known projects).")
    lines.append("")

    # 7. Session marker
    try:
        SESSION_MARKER.parent.mkdir(parents=True, exist_ok=True)
        session_id = os.environ.get("CLAUDE_SESSION_ID")
        if not session_id:
            import uuid
            session_id = f"manual-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        with open(SESSION_MARKER, "w", encoding="utf-8") as f:
            f.write(session_id)
    except Exception:
        pass

    # Enforce 30-line limit
    output = "\n".join(lines[:30])
    print(output)


if __name__ == "__main__":
    main()
