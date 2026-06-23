#!/usr/bin/env python3
"""
Session Harvester — called by Claude Code hooks.
- Stop hook (--mode stop): harvest the just-ended transcript → trigger incremental scan
- SessionStart hook (--mode start): harvest unprocessed transcripts → Agent Memory updated before AI loads

Design principles:
- Never loses data: all writes are atomic (.tmp → rename)
- Never crashes the hook: every step has try/except
- Works without proxy: no network calls in harvest phase
- Works without transcript path: falls back to scanning agent memory
- Idempotent: running twice on the same transcript doesn't duplicate
"""
import os
import sys
import re
import json
import yaml
import shutil
import subprocess
import hashlib
import argparse
from datetime import datetime, timezone, timedelta

# ── Configuration ──────────────────────────────────────────────
VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", "D:/Obsidian/a")
AGENT_MEMORY = str(Path.home() / ".claude" / "projects" / "d--C-file")
SCANNER_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 7892

# Known project names (used for auto-detection from file paths)
PROJECT_KEYWORDS = {
    "CSTB-pan-cancer": ["cstb", "CSTB_paper", "CSTB-pan-cancer"],
    "ITIP-NSCLC": ["itip", "NSCLC", "itip_p1"],
    "AI-VAST": ["AI-VAST", "ai-vast", "vast"],
    "Spatial-Agent": ["spatial_agent", "spatial", "spatial-agent"],
    "single-gene-pan-cancer": ["single-gene-pan-cancer", "single_gene"],
    "Zotero-toolchain": ["zotero", "zotero-auto-cite"],
    "Patent-workflow": ["patent", "paper2patent", "patent-disclosure"],
    "Resume-RenderCV": ["resume", "rendercv", "RenderCV"],
    "Project-Infra": ["obsidian", "neat-freak", "scanner", ".claude"],
}

# Local timezone (China Standard Time)
CST = timezone(timedelta(hours=8))


# ── Main ───────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Session Harvester")
    parser.add_argument("--mode", choices=["stop", "start"], default="stop",
                       help="stop: harvest current transcript (Stop hook). "
                            "start: scan for unprocessed transcripts (SessionStart hook).")
    args = parser.parse_args()

    if args.mode == "start":
        return start_mode()
    else:
        return stop_mode()


def stop_mode():
    """Stop hook: harvest the just-ended transcript, then trigger incremental scanner."""
    transcript_path = find_transcript()
    if not transcript_path:
        print("[harvester] No transcript found — nothing to harvest")
        return 0

    result = process_transcript(transcript_path)
    if result:
        run_scanner_incremental()
    return 0


def start_mode():
    """SessionStart hook: find unprocessed transcripts and harvest them.
    Fast — no scanner trigger. The daily cron handles deep analysis."""
    # Load heartbeat to find already-processed transcripts
    processed = load_processed_from_heartbeat()

    # Find all transcripts in agent memory modified in last 48 hours
    candidates = find_recent_transcripts(processed, hours=48)

    if not candidates:
        print("[harvester:start] No unprocessed transcripts found")
        return 0

    print(f"[harvester:start] Found {len(candidates)} unprocessed transcript(s)")
    harvested = 0
    for tp in candidates:
        if process_transcript(tp):
            harvested += 1

    print(f"[harvester:start] Harvested {harvested}/{len(candidates)} transcripts")
    return 0


def process_transcript(transcript_path):
    """Harvest a single transcript: extract knowledge, write to vault.
    Returns True if anything was written."""
    print(f"[harvester] Processing: {transcript_path}")

    content = read_transcript(transcript_path)
    decisions = extract_decisions(content)
    errors = extract_errors(content)
    summary = extract_session_summary(content)
    meta = extract_meta(content)

    total_found = len(decisions) + len(errors) + (1 if summary else 0)
    if total_found == 0:
        print("[harvester] No [DECISION]/[ERROR]/[SESSION_SUMMARY] found")
        return False

    print(f"[harvester] Found: {len(decisions)} decisions, {len(errors)} errors, "
          f"{'1 summary' if summary else 'no summary'}")

    project = detect_project(content, meta)
    session_id = generate_session_id(transcript_path, meta)
    date_str = meta.get("date", datetime.now(CST).strftime("%Y-%m-%d"))

    written = write_session_to_vault(session_id, date_str, project, meta,
                                     decisions, errors, summary)

    if decisions:
        append_decisions(project, decisions, session_id, date_str)
    if errors:
        append_errors_to_pitfalls(project, errors, session_id, date_str)

    print(f"[harvester] Done: project={project}, session={session_id}")
    return written > 0


# ── SessionStart Helpers ────────────────────────────────────────

def load_processed_from_heartbeat():
    """Load set of already-processed transcript IDs from heartbeat."""
    hb_path = os.path.join(VAULT_PATH, "04-Feedback", "heartbeat.md")
    if not os.path.exists(hb_path):
        return set()
    try:
        with open(hb_path, 'r', encoding='utf-8') as f:
            content = f.read()
        parts = content.split('---', 2)
        if len(parts) < 3:
            return set()
        fm = yaml.safe_load(parts[1])
        processed = fm.get('processed_sessions', {})
        return set(processed.keys())
    except Exception:
        return set()


def find_recent_transcripts(processed_ids, hours=48):
    """Find JSONL transcripts in agent memory modified recently but not yet processed.
    Returns list of file paths sorted by modification time (newest first)."""
    candidates = []
    cutoff = datetime.now().timestamp() - (hours * 3600)

    search_dirs = [
        AGENT_MEMORY,
        os.path.expanduser("~/.claude/transcripts"),
        os.path.expanduser("~/.claude/projects"),
    ]

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            depth = root.replace(search_dir, "").count(os.sep)
            if depth > 4:
                continue
            for f in files:
                if not f.endswith(".jsonl") or f.startswith("agent-"):
                    continue
                fp = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(fp)
                    if mtime < cutoff:
                        continue
                except OSError:
                    continue

                # Check if already processed
                session_id = f.replace(".jsonl", "")
                if session_id in processed_ids:
                    continue

                candidates.append((mtime, fp))

    # Sort by modification time, newest first
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [fp for _, fp in candidates]


# ── Transcript Discovery ───────────────────────────────────────
def find_transcript():
    """Find the transcript file. Try hook env vars first, then scan agent memory."""
    # Try all known env var names for the transcript path
    for varname in ["CLAUDE_TRANSCRIPT_PATH", "TRANSCRIPT_PATH",
                    "CLAUDE_SESSION_TRANSCRIPT", "CLAUDE_TRANSCRIPT"]:
        path = os.environ.get(varname)
        if path and os.path.exists(path):
            print(f"[harvester] Found transcript via ${varname}: {path}")
            return path

    # Fallback: scan agent memory for most recently modified .jsonl files
    return find_latest_transcript_in_memory()


def find_latest_transcript_in_memory():
    """Scan agent memory directories for the most recent transcript JSONL."""
    best_path = None
    best_mtime = 0

    # Look in standard Claude Code transcript directories
    search_dirs = [
        AGENT_MEMORY,
        os.path.expanduser("~/.claude/transcripts"),
        os.path.expanduser("~/.claude/projects"),
    ]

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            # Limit depth to avoid scanning too much
            depth = root.replace(search_dir, "").count(os.sep)
            if depth > 4:
                continue
            for f in files:
                if f.endswith(".jsonl") and not f.startswith("agent-"):
                    fp = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(fp)
                        # Only consider files modified in the last 24 hours
                        if mtime > best_mtime and (datetime.now().timestamp() - mtime) < 86400:
                            best_mtime = mtime
                            best_path = fp
                    except OSError:
                        continue

    if best_path:
        print(f"[harvester] Fallback: using most recent transcript: {best_path}")
    return best_path


# ── Content Extraction ─────────────────────────────────────────
def read_transcript(path):
    """Read JSONL transcript, returning raw text of all assistant + user messages."""
    if not path or not os.path.exists(path):
        return ""

    # If it's a directory of JSONL files, read the most recent one
    if os.path.isdir(path):
        jsonl_files = sorted([f for f in os.listdir(path) if f.endswith(".jsonl")],
                             key=lambda f: os.path.getmtime(os.path.join(path, f)),
                             reverse=True)
        if jsonl_files:
            path = os.path.join(path, jsonl_files[0])
        else:
            return ""

    if not path.endswith(".jsonl"):
        return ""

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError):
        return ""

    # Extract all message content
    parts = []
    for line in lines:
        try:
            rec = json.loads(line)
            msg = rec.get("message", {})
            content_list = msg.get("content", [])
            if isinstance(content_list, list):
                for block in content_list:
                    if isinstance(block, dict) and "text" in block:
                        parts.append(block["text"])
                    elif isinstance(block, str):
                        parts.append(block)
            elif isinstance(content_list, str):
                parts.append(content_list)
        except (json.JSONDecodeError, KeyError):
            continue

    return "\n".join(parts)


def extract_decisions(text):
    """Extract all [DECISION: ...] blocks from text."""
    pattern = r"\[DECISION:\s*(.*?)\s*\|\s*context:\s*(.*?)\]"
    matches = re.findall(pattern, text, re.DOTALL)
    return [{"text": m[0].strip().replace("\n", " "),
             "context": m[1].strip().replace("\n", " ")}
            for m in matches]


def extract_errors(text):
    """Extract all [ERROR: type=... | resolution=...] blocks from text."""
    pattern = r"\[ERROR:\s*type=(\S+)\s*\|\s*resolution=(.*?)\]"
    matches = re.findall(pattern, text, re.DOTALL)
    return [{"type": m[0].strip(),
             "resolution": m[1].strip().replace("\n", " ")}
            for m in matches]


def extract_session_summary(text):
    """Extract [SESSION_SUMMARY] block if present."""
    pattern = r"\[SESSION_SUMMARY\](.*?)\[/SESSION_SUMMARY\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_meta(text):
    """Extract basic metadata from transcript content."""
    meta = {}
    # Try to find a date in the first few lines
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text[:500])
    if date_match:
        meta["date"] = date_match.group(1)
    else:
        meta["date"] = datetime.now(CST).strftime("%Y-%m-%d")

    # Try to find project name mentions
    project_counts = {}
    for proj, keywords in PROJECT_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text.lower())
        if count > 0:
            project_counts[proj] = count
    if project_counts:
        meta["project_hints"] = project_counts

    return meta


# ── Project Detection ──────────────────────────────────────────
def detect_project(text, meta):
    """Determine which project this session belongs to."""
    # Use project_hints from meta if available
    hints = meta.get("project_hints", {})

    # Also scan for file paths in the text (strong signal)
    path_pattern = r"(?:d:|D:)[/\\.]C-file[/\\]([^/\s\\]+)"
    path_matches = re.findall(path_pattern, text, re.IGNORECASE)
    for m in path_matches:
        for proj, keywords in PROJECT_KEYWORDS.items():
            if any(kw.lower() in m.lower() for kw in keywords):
                hints[proj] = hints.get(proj, 0) + 3  # File paths are strong signals

    if hints:
        return max(hints, key=hints.get)

    # Default: most recently active project
    return "Project-Infra"


# ── Session ID Generation ──────────────────────────────────────
def generate_session_id(transcript_path, meta):
    """Generate a stable, unique session ID."""
    # Use transcript filename as base
    basename = os.path.basename(transcript_path)
    session_id = basename.replace(".jsonl", "")

    # If it looks like a UUID already, use it
    if len(session_id) >= 32:
        return session_id

    # Otherwise, hash the path for stability
    date_str = meta.get("date", datetime.now(CST).strftime("%Y-%m-%d"))
    path_hash = hashlib.md5(transcript_path.encode()).hexdigest()[:8]
    return f"{date_str}-{path_hash}"


# ── Vault Writing ──────────────────────────────────────────────
def write_session_to_vault(session_id, date_str, project, meta,
                           decisions, errors, summary):
    """Write session summary .md to vault. Returns count of files written."""
    sessions_dir = os.path.join(VAULT_PATH, "01-Projects", project, "Memory", "sessions")
    os.makedirs(sessions_dir, exist_ok=True)

    filename = f"{date_str}-{session_id}.md" if not session_id.startswith(date_str) else f"{session_id}.md"
    filepath = os.path.join(sessions_dir, filename)

    # Check if already exists (idempotent)
    if os.path.exists(filepath):
        print(f"[harvester] Session file already exists: {filepath} — appending new items only")
        # Read existing, merge new decisions/errors
        existing = read_existing_session(filepath)
        decisions = merge_unique(decisions, existing.get("decisions", []), "text")
        errors = merge_unique(errors, existing.get("errors", []), "type")
        if not decisions and not errors:
            return 0

    # Build frontmatter
    tags = list(set(
        tag for d in decisions for tag in extract_tags_from_decision(d)
    ))
    tags.extend([e["type"].split("_")[0] for e in errors])  # category as tag

    fm = {
        "session_id": session_id,
        "date": date_str,
        "project": project,
        "ai_title": generate_title(decisions, errors),
        "summary_status": "draft",
        "summary_type": "session",
        "decisions_made": decisions,
        "errors_encountered": errors,
        "tags": list(set(tags)),
        "harvested_by": "session_harvester.py",
        "harvested_at": datetime.now(CST).isoformat(),
    }

    # Build body
    body_parts = [f"# {fm['ai_title']}\n"]
    body_parts.append(f"Session: {session_id} | Date: {date_str} | Project: {project}\n")

    if decisions:
        body_parts.append("\n## Decisions\n")
        for i, d in enumerate(decisions, 1):
            body_parts.append(f"{i}. **{d['text']}**\n")
            body_parts.append(f"   - Context: {d['context']}\n")

    if errors:
        body_parts.append("\n## Errors Encountered\n")
        for i, e in enumerate(errors, 1):
            body_parts.append(f"{i}. `{e['type']}`\n")
            body_parts.append(f"   - Resolution: {e['resolution']}\n")

    if summary:
        body_parts.append("\n## Session Summary\n")
        body_parts.append(summary + "\n")

    body = "\n".join(body_parts)

    # Atomic write
    fm_yaml = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n{body}"

    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, filepath)

    print(f"[harvester] Wrote session: {filepath}")
    return 1


def read_existing_session(filepath):
    """Read existing session .md and return its frontmatter."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1]) or {}
    except Exception:
        pass
    return {}


def merge_unique(new_items, existing_items, key_field):
    """Merge new items into existing, deduplicating by key_field."""
    existing_keys = {item.get(key_field, "") for item in existing_items}
    truly_new = [item for item in new_items if item.get(key_field, "") not in existing_keys]
    return truly_new


def generate_title(decisions, errors):
    """Generate a human-readable title from harvested content."""
    parts = []
    if decisions:
        parts.append(decisions[0]["text"][:60])
    if errors:
        parts.append(f"{len(errors)} error(s)")
    if not parts:
        parts.append("Session")
    return " / ".join(parts)


def extract_tags_from_decision(decision):
    """Extract relevant tags from a decision text."""
    tags = []
    text = decision.get("text", "") + " " + decision.get("context", "")
    text_lower = text.lower()
    # Map common keywords to tags
    tag_map = {
        "r 4.5": "R-bug", "ggplot": "R-bug", "identity": "identity-fill",
        "python": "python-encoding", "encoding": "encoding", "gbk": "encoding",
        "zotero": "zotero", "citation": "citation",
        "gfw": "gfw", "proxy": "gfw", "ssl": "ssl",
        "ci": "infra", "test": "infra", "hook": "infra",
        "cbioportal": "cBioPortal", "gdc": "GDC", "api": "API",
        "figure": "figure", "color": "figure", "plot": "figure",
        "docx": "DOCX", "word": "DOCX",
        "patent": "patent",
        "module": "module",
    }
    for kw, tag in tag_map.items():
        if kw in text_lower:
            tags.append(tag)
    return tags


# ── Append to Project Files ────────────────────────────────────
def append_decisions(project, decisions, session_id, date_str):
    """Append decisions to project's decisions.md."""
    dec_path = os.path.join(VAULT_PATH, "01-Projects", project, "Memory", "decisions.md")
    os.makedirs(os.path.dirname(dec_path), exist_ok=True)

    # Read existing decisions to check for duplicates
    existing_texts = set()
    if os.path.exists(dec_path):
        try:
            with open(dec_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Extract existing decision texts from frontmatter
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1])
                for d in fm.get("decisions", []):
                    existing_texts.add(d.get("text", ""))
            existing_body = parts[2] if len(parts) > 2 else ""
        except Exception:
            existing_body = ""
    else:
        existing_body = ""

    # Filter out duplicates
    new_decisions = [d for d in decisions if d["text"] not in existing_texts]
    if not new_decisions:
        return

    # Append to body
    new_lines = []
    for d in new_decisions:
        new_lines.append(f"- [{date_str}] **{d['text']}** | context: {d['context']} | session: {session_id}")

    updated_body = existing_body.rstrip() + "\n" + "\n".join(new_lines) + "\n"

    # Rewrite file with updated frontmatter
    _rewrite_project_md(dec_path, "decisions", new_decisions, updated_body, session_id)


def append_errors_to_pitfalls(project, errors, session_id, date_str):
    """Append errors to project's pitfalls.md."""
    pit_path = os.path.join(VAULT_PATH, "01-Projects", project, "Memory", "pitfalls.md")
    os.makedirs(os.path.dirname(pit_path), exist_ok=True)

    # Read existing errors
    existing_types = set()
    if os.path.exists(pit_path):
        try:
            with open(pit_path, "r", encoding="utf-8") as f:
                content = f.read()
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1])
                for p in fm.get("pitfalls", []):
                    existing_types.add(p.get("type", ""))
            existing_body = parts[2] if len(parts) > 2 else ""
        except Exception:
            existing_body = ""
    else:
        existing_body = ""

    new_errors = [e for e in errors if e["type"] not in existing_types]
    if not new_errors:
        return

    new_lines = []
    for e in new_errors:
        new_lines.append(f"- [{date_str}] **{e['type']}** → {e['resolution']} | session: {session_id}")

    updated_body = existing_body.rstrip() + "\n" + "\n".join(new_lines) + "\n"

    _rewrite_project_md(pit_path, "pitfalls", new_errors, updated_body, session_id)


def _rewrite_project_md(filepath, key, new_items, body, session_id):
    """Rewrite a project .md file with updated frontmatter list."""
    try:
        # Build frontmatter
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()
            parts = old_content.split("---", 2)
            old_fm = yaml.safe_load(parts[1]) if len(parts) >= 3 and parts[1].strip() else {}
        else:
            old_fm = {}

        existing = old_fm.get(key, [])
        existing.extend(new_items)
        old_fm[key] = existing
        old_fm["last_updated"] = datetime.now(CST).isoformat()

        fm_yaml = yaml.dump(old_fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        content = f"---\n{fm_yaml}---\n\n{body}"

        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, filepath)
    except Exception as e:
        print(f"[harvester] WARNING: Could not update {filepath}: {e}")


# ── Scanner Trigger ────────────────────────────────────────────
def run_scanner_incremental():
    """Run scanner in incremental mode (analyze + maintain + report + compile)."""
    runner = os.path.join(SCANNER_DIR, "runner.py")
    if not os.path.exists(runner):
        print("[harvester] WARNING: runner.py not found, skipping incremental scan")
        return

    # Check proxy — if down, skip LLM-dependent steps
    proxy_up = check_proxy()
    if not proxy_up:
        print("[harvester] Proxy DOWN — running scanner in keyword-only mode (no LLM clustering)")
        # Still run — analyzer falls back to keyword-only when API key is empty

    cmd = [PYTHON, runner, "--step", "analyze", "--step", "maintain",
           "--step", "report", "--step", "compile"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                cwd=SCANNER_DIR, env=os.environ.copy())
        if result.returncode != 0:
            print(f"[harvester] Scanner completed with warnings:\n{result.stderr[:500]}")
        else:
            print(f"[harvester] Incremental scanner completed successfully")
        # Print summary line
        for line in result.stdout.strip().split("\n")[-3:]:
            print(f"  {line}")
    except subprocess.TimeoutExpired:
        print("[harvester] WARNING: Scanner timed out after 120s")
    except Exception as e:
        print(f"[harvester] WARNING: Scanner failed: {e}")


def check_proxy():
    """Check if proxy is available."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((PROXY_HOST, PROXY_PORT))
        s.close()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
