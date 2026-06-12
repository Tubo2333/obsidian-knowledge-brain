"""Step 1: Backup new JSONL sessions to vault.

Copies JSONL session files from the Claude projects directory into the vault's
_raw-sessions/ folder, and generates lightweight Markdown summaries.

JSONL record type detection is configurable via the `session_title_type` key
in config.yaml. If not set, defaults to 'ai-title' (Claude Code convention).
Set to null or 'first-user' to use the first user message as title.
"""

import os
import json
import shutil
from datetime import datetime


def run(cfg, dry_run=False, full=False):
    vault = cfg['vault_path']
    source = cfg['claude_project_path']
    raw_dir = os.path.join(vault, '04-Feedback', '_raw-sessions')
    heartbeat_path = os.path.join(vault, '04-Feedback', 'heartbeat.md')

    # Load processed sessions from heartbeat
    processed = load_processed_sessions(heartbeat_path)

    # Configurable JSONL record type for extracting title
    # 'ai-title' = Claude Code convention
    # 'first-user' = use first user message as title
    # null = no title extraction
    title_type = cfg.get('session_title_type', 'ai-title')

    # Find new/changed sessions
    new_sessions = []
    skipped_agent = 0
    for root, dirs, files in os.walk(source):
        for f in files:
            if not f.endswith('.jsonl'):
                continue
            fp = os.path.join(root, f)
            session_id = f.replace('.jsonl', '')

            # Filter: skip agent sub-sessions (inflate counts, share parent
            # context)
            if session_id.startswith('agent-') or 'subagent' in root.lower():
                skipped_agent += 1
                continue

            file_size = os.path.getsize(fp)

            if (full or session_id not in processed or
                    processed[session_id] != file_size):
                new_sessions.append((fp, session_id, file_size))

    processed_count = 0
    for fp, session_id, file_size in new_sessions:
        if not dry_run:
            # Atomic copy: copy to .tmp then rename
            dst = os.path.join(raw_dir, f"{session_id}.jsonl")
            os.makedirs(raw_dir, exist_ok=True)
            tmp_dst = dst + '.tmp'
            shutil.copy2(fp, tmp_dst)
            os.replace(tmp_dst, dst)

            # Generate Markdown metadata summary (atomic)
            md_path = os.path.join(raw_dir, f"{session_id}.md")
            tmp_md = md_path + '.tmp'
            generate_md_summary_to_path(fp, tmp_md, title_type=title_type)
            os.replace(tmp_md, md_path)

        processed[session_id] = file_size
        processed_count += 1

    return {
        "new_sessions": processed_count,
        "total_tracked": len(processed),
        "processed_ids": dict(processed),
        "skipped_agent_sessions": skipped_agent
    }


def load_processed_sessions(heartbeat_path):
    """Extract processed_sessions from heartbeat frontmatter."""
    if not os.path.exists(heartbeat_path):
        return {}
    with open(heartbeat_path, 'r', encoding='utf-8') as f:
        content = f.read()
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}
    import yaml
    fm = yaml.safe_load(parts[1])
    return fm.get('processed_sessions', {})


def generate_md_summary_to_path(jsonl_path, md_path, title_type='ai-title'):
    """Generate a lightweight Markdown summary from JSONL metadata.

    Args:
        jsonl_path: Path to the JSONL session file.
        md_path: Output path for the Markdown summary.
        title_type: How to extract the title:
            - 'ai-title': Look for records with type='ai-title' (Claude Code)
            - 'first-user': Use first user message as title
            - None or 'none': Use 'Untitled'
    """
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    first_ts, last_ts, title = None, None, None
    user_msgs = []

    for line in lines[:50]:  # Sample first 50 lines for metadata
        try:
            rec = json.loads(line)
            if not first_ts and 'timestamp' in rec:
                first_ts = rec['timestamp']
            if 'timestamp' in rec:
                last_ts = rec['timestamp']

            # Configurable title extraction
            if title_type and title_type.lower() not in ('none', 'null', ''):
                if (title_type == 'ai-title' and
                        rec.get('type') == 'ai-title'):
                    title = rec.get('title', '')
                elif (title_type == 'first-user' and
                        rec.get('type') == 'user' and
                        'message' in rec and not title):
                    msg = rec['message']
                    if isinstance(msg, str):
                        title = msg[:100]
                    elif isinstance(msg, dict):
                        content = msg.get('content', [])
                        if isinstance(content, list) and content:
                            first_block = content[0]
                            if isinstance(first_block, dict):
                                title = first_block.get('text', '')[:100]
                        elif isinstance(content, str):
                            title = content[:100]

            if rec.get('type') == 'user' and 'message' in rec:
                msg = rec['message'][:200]
                if isinstance(msg, str):
                    user_msgs.append(msg)
        except json.JSONDecodeError:
            continue

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write(f"date: {first_ts[:10] if first_ts else 'unknown'}\n")
        f.write(f"title: \"{title or 'Untitled'}\"\n")
        f.write(f"messages_sampled: {len(user_msgs)}\n")
        f.write("---\n\n")
        f.write(f"# {title or 'Untitled Session'}\n\n")
        f.write(f"Date: {first_ts[:10] if first_ts else 'unknown'}\n\n")
        f.write("## User Messages (first 200 chars each)\n\n")
        for i, msg in enumerate(user_msgs[:5]):
            f.write(f"{i+1}. {msg}\n")


def generate_md_summary(jsonl_path, md_path):
    """DEPRECATED: use generate_md_summary_to_path instead."""
    generate_md_summary_to_path(jsonl_path, md_path)
