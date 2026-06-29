#!/usr/bin/env python3
"""
obsidian-knowledge-brain v4.0 — Pre-Action Instruction injection.
Detects file format, injects the v4.0 knowledge triggers instruction at file top.
Format-adaptive: Markdown, HTML, YAML-frontmatter, JS/TS, JSON, plain text.
Idempotent: skips if already injected. Supports removal for uninstall.
"""
from pathlib import Path

# The pre-action instruction from spec §3.5 — exact text, never grows
PRE_ACTION_TEXT = """> **Knowledge triggers（强制 / MUST）**: This project uses Obsidian Knowledge
> Brain v4.0. You MUST execute the following at the specified moments.
>
> **Pre** — Before writing new library imports or system calls in a file.
> (Sync once per file; skip if atoms.json mtime unchanged since last sync.
> If the keyword index doesn't exist — project not bootstrapped — skip this
> entire Pre section and proceed.)
>   1. **Sync**: Read `~/.obsidian-knowledge-brain/atoms.json`. Safe-merge
>      into `_global_atoms` section of your keyword index (locate it under
>      your platform's agent directory: `.claude/rules/`, `.cursor/rules/`,
>      or equivalent). Before editing the index, copy to `.bak`.
>   2. **Grep**: Search the keyword index for keywords matching your code.
>   3. **Load**: For matched atoms where `phase: pre`, open the file at
>      `pointer`, read the specified line range. If pointer lines don't match
>      the topic → fall back to loading the entire file.
>
> **During** — When stuck on the same error >2 attempts:
>   Grep the keyword index for error keywords. Load `phase: during` atoms.
>
> **Post** — After resolving any error, BEFORE writing the permanent fix:
>   1. **Load**: Grep for `phase: post` atoms matching the error.
>   2. **Record**: Immediately append a one-line stub to your platform's
>      `memory/_phase1_inbox.md` (under your agent directory):
>      `[ERROR: type=<type> | resolution=<fix> | project: <slug>]`
>      This is the final step of every error fix. NOT deferred to session end.
>
> **Consequence**: Skipping any MUST step and hitting a documented pitfall →
> `[ERROR: type=missed-atom | atom_id=<id>]`. Missing error stub →
> `[ERROR: type=missed-record | error_type=<type>]`. No exceptions."""

# Sentinel string that marks already-injected instruction
SENTINEL = "Knowledge triggers（强制 / MUST）"


def detect_format(file_path: Path) -> str:
    """Detect file format from first 20 lines.
    Returns: 'markdown', 'yaml-frontmatter', 'html', 'javascript', 'json', 'plain'"""
    if not file_path.exists():
        return 'plain'

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_lines = "".join(f.readline() for _ in range(20))
    except (OSError, UnicodeDecodeError):
        return 'plain'

    if not first_lines.strip():
        return 'plain'

    # Check for YAML frontmatter (--- at very start)
    if first_lines.lstrip().startswith("---"):
        return 'yaml-frontmatter'

    # Check for Markdown heading
    if first_lines.lstrip().startswith("# "):
        return 'markdown'

    # Check for HTML
    if "<!DOCTYPE" in first_lines[:200] or "<html" in first_lines[:200]:
        return 'html'

    # Check for JS/TS comments
    if first_lines.lstrip().startswith("//") or first_lines.lstrip().startswith("/*"):
        return 'javascript'

    # Check for JSON
    stripped = first_lines.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return 'json'

    return 'plain'


def is_already_injected(file_path: Path) -> bool:
    """Check if pre-action instruction is already present."""
    if not file_path.exists():
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return SENTINEL in content
    except (OSError, UnicodeDecodeError):
        return False


def inject(file_path: Path) -> tuple[bool, str]:
    """Inject pre-action instruction at file top. Format-adaptive. Idempotent.
    Returns (success, message)."""
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    if is_already_injected(file_path):
        return False, "Already injected -> skip"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return False, f"Cannot read file: {e}"

    fmt = detect_format(file_path)

    if fmt == 'markdown':
        # After the first heading line (keep heading as line 1)
        lines = content.split("\n")
        injection = PRE_ACTION_TEXT + "\n\n"
        # Find end of first heading block (heading + blank line)
        insert_at = 0
        heading_found = False
        for i, line in enumerate(lines):
            if line.lstrip().startswith("# ") and not heading_found:
                heading_found = True
                continue
            if heading_found and not line.strip():
                insert_at = i + 1
                break
            if heading_found and not line.lstrip().startswith("#"):
                insert_at = i
                break
        if insert_at == 0:
            # No heading found or heading at very end — prepend
            new_content = injection + content
        else:
            new_content = "\n".join(lines[:insert_at]) + "\n" + injection + "\n".join(lines[insert_at:])

    elif fmt == 'yaml-frontmatter':
        # After YAML frontmatter closing ---
        parts = content.split("---", 2)
        if len(parts) >= 3:
            # parts[0] is empty (starts with ---), parts[1] is frontmatter, parts[2] is body
            new_content = "---" + parts[1] + "---\n\n" + PRE_ACTION_TEXT + "\n" + parts[2]
        else:
            # Malformed — prepend as markdown blockquote
            new_content = PRE_ACTION_TEXT + "\n\n" + content

    elif fmt == 'html':
        # After <!DOCTYPE> or <html> tag, as HTML comment
        html_instruction = PRE_ACTION_TEXT.replace("> ", "")
        html_block = "<!--\n" + html_instruction + "\n-->\n\n"
        # Insert after first line if it's doctype/html
        lines = content.split("\n")
        insert_at = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("<!DOCTYPE") or line.strip().startswith("<html"):
                insert_at = i + 1
                break
        if insert_at > 0:
            new_content = "\n".join(lines[:insert_at]) + "\n" + html_block + "\n".join(lines[insert_at:])
        else:
            new_content = html_block + content

    elif fmt == 'javascript':
        # As // comment block
        js_lines = PRE_ACTION_TEXT.split("\n")
        js_block = "\n".join("// " + line.lstrip("> ") for line in js_lines)
        new_content = js_block + "\n\n" + content

    elif fmt == 'json':
        # Minimal _comment key injection
        new_content = '{\n  "_comment": "Knowledge triggers (MUST): This project uses Obsidian Knowledge Brain v4.0. Pre/During/Post instructions — see SKILL.md.",\n' + content[1:]

    else:
        # Plain text: inject raw at top
        new_content = PRE_ACTION_TEXT + "\n\n" + content

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True, f"Injected ({fmt} format)"
    except OSError as e:
        return False, f"Cannot write file: {e}"


def remove(file_path: Path) -> tuple[bool, str]:
    """Remove pre-action instruction from file. Format-adaptive.
    Detects injection format from the SENTINEL line's prefix, then removes
    the entire instruction block. Works for all 6 formats.
    Returns (success, message)."""
    if not file_path.exists():
        return False, "File not found"

    if not is_already_injected(file_path):
        return False, "Not injected -> skip"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return False, f"Cannot read: {e}"

    lines = content.split("\n")
    sentinel_idx = None

    # Find the SENTINEL line
    for i, line in enumerate(lines):
        if SENTINEL in line:
            sentinel_idx = i
            break

    if sentinel_idx is None:
        return False, "Sentinel not found"

    # Detect format from the SENTINEL line's prefix
    sentinel_line = lines[sentinel_idx]
    start_idx = sentinel_idx
    end_idx = sentinel_idx + 1

    if sentinel_line.lstrip().startswith("> "):
        # Markdown blockquote: search backward for block start, forward for block end
        while start_idx > 0 and lines[start_idx - 1].lstrip().startswith(">"):
            start_idx -= 1
        while end_idx < len(lines) and lines[end_idx].lstrip().startswith(">"):
            end_idx += 1
        # Consume trailing blank lines within/below the block
        while end_idx < len(lines) and lines[end_idx].strip() == "":
            end_idx += 1

    elif sentinel_line.lstrip().startswith("// "):
        # JavaScript // comments: find contiguous // block
        while start_idx > 0 and lines[start_idx - 1].lstrip().startswith("// "):
            start_idx -= 1
        while end_idx < len(lines) and lines[end_idx].lstrip().startswith("// "):
            end_idx += 1
        # Consume trailing blank line
        if end_idx < len(lines) and lines[end_idx].strip() == "":
            end_idx += 1

    elif sentinel_line.strip().startswith("<!--"):
        # HTML comment: find <!-- ... --> block
        # Search backward for <!--
        while start_idx > 0 and "<!--" not in lines[start_idx - 1]:
            start_idx -= 1
        # Search forward for -->
        while end_idx < len(lines) and "-->" not in lines[end_idx]:
            end_idx += 1
        if end_idx < len(lines):
            end_idx += 1  # include the --> line
        # Consume trailing blank line
        if end_idx < len(lines) and lines[end_idx].strip() == "":
            end_idx += 1

    elif sentinel_line.strip().startswith('"_comment"') or sentinel_line.strip().startswith('"Knowledge triggers'):
        # JSON _comment key: find the _comment line and remove it + trailing comma if present
        for j in range(sentinel_idx, -1, -1):
            if '"_comment"' in lines[j]:
                start_idx = j
                break
        # The _comment value is a single JSON string line
        end_idx = start_idx + 1

    else:
        # Plain text: remove the raw text block
        # Find the start (first non-blank line of the instruction block)
        while start_idx > 0 and PRE_ACTION_TEXT.split("\n")[0].strip() not in lines[start_idx - 1]:
            start_idx -= 1
            if start_idx == 0:
                break
        # Find the end (after the last line of PRE_ACTION_TEXT)
        pre_lines = [l for l in PRE_ACTION_TEXT.split("\n") if l.strip()]
        if pre_lines:
            last_sentence = pre_lines[-1].strip().lstrip("> ").strip()
            for j in range(sentinel_idx, len(lines)):
                if last_sentence in lines[j]:
                    end_idx = j + 1
                    break
            else:
                end_idx = sentinel_idx + 1
        # Consume trailing blank line
        if end_idx < len(lines) and lines[end_idx].strip() == "":
            end_idx += 1

    # Remove the block
    new_lines = lines[:start_idx] + lines[end_idx:]
    new_content = "\n".join(new_lines)

    # Clean up: remove leading blank lines if we removed from the top
    while new_content.startswith("\n\n"):
        new_content = new_content[1:]

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True, "Removed"
    except OSError as e:
        return False, f"Cannot write: {e}"
