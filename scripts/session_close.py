#!/usr/bin/env python3
"""session_close.py -- Session-end protocol validator and prompt generator.
--prompt: output Phase 1 + Phase 2 close protocol for Agent.
--validate: check Agent's writes, exit 0/1.
Design: docs/superpowers/specs/2026-06-16-obsidian-brain-v3-design.md S4.2

v3.0: T2 "收尾" is the PRIMARY knowledge capture moment. Agent reviews session
transcript at session end and extracts all decisions/errors — no mid-session annotation.
"""

import os, sys, re
from pathlib import Path
from datetime import date


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
RULES_D = BASE / "rules"
PROJS_D = BASE / "projects"
ROOT_MD = PROJECT_ROOT / "CLAUDE.md"
INBOX = BASE / "memory" / "_phase1_inbox.md"

CEIL = {"root": 100, "rule": 80, "project": 60}
ST_R = {"active", "archived"}
ST_P = {"active", "completed", "archived"}
REQ_R = ["schema_version", "domain", "priority", "last_triggered", "status"]
REQ_P = ["schema_version", "project", "status", "updated"]
# v3.0 extended format: [DECISION: summary | context: why | project: slug | scope: project|cross-project]
# v3.0 extended format: [ERROR: type=taxonomy | resolution: fix | project: slug]
DEC_RE = re.compile(
    r"\[DECISION:\s*(.+?)\s*\|\s*context:\s*(.+?)"
    r"(?:\s*\|\s*project:\s*(.+?))?"
    r"(?:\s*\|\s*scope:\s*(project|cross-project))?"
    r"\]"
)
ERR_RE = re.compile(
    r"\[ERROR:\s*type\s*=\s*(.+?)\s*\|\s*resolution\s*=\s*(.+?)"
    r"(?:\s*\|\s*project:\s*(.+?))?"
    r"\]"
)


def parse_fm(text):
    """Parse simple YAML frontmatter -> dict or None."""
    if not text.startswith("---"): return None
    parts = text.split("---", 2)
    if len(parts) < 3: return None
    fm = {}
    for line in parts[1].strip().split("\n"):
        m = re.match(r"^(\w[\w_-]*)\s*:\s*(.+)$", line.strip())
        if m: fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm or None


def rd(p):
    """Read file -> (lines_list, err_str)."""
    try:
        with open(p, "r", encoding="utf-8") as f: return f.readlines(), ""
    except FileNotFoundError: return [], ""
    except Exception as e: return [], str(e)


def lc(p):
    ls, _ = rd(p)
    return sum(1 for l in ls if l.strip())


def detect_project():
    """Data-driven: read Path: field from project files, match against CWD."""
    cwd = os.getcwd().replace("\\", "/").lower()
    for pf in sorted(PROJS_D.glob("*.md")):
        if pf.name.startswith("_"): continue
        body, _ = rd(pf)
        m = re.search(r"\*\*Path\*\*:\s*`([^`]+)`", "".join(body))
        pp = m.group(1).replace("\\", "/").rstrip("/").lower() if m else ""
        if pp and pp in cwd: return pf.stem
    # Fallback: monorepo root — check for recently active project via inbox
    if INBOX.exists():
        try:
            inbox_text = "".join(rd(INBOX)[0])
            # Find the most recent project mention in annotations
            m = re.findall(r"project:\s*(\S+)", inbox_text)
            if m: return m[-1]  # last mentioned project
        except Exception:
            pass
    return None


def fm_check(fm, required, allowed_st):
    """Check required fields + status enum + date format. Returns error list."""
    errs = []
    for f in required:
        if f not in fm: errs.append(f"missing '{f}'")
    s = fm.get("status","")
    if s and s not in allowed_st: errs.append(f"bad status '{s}' (allowed:{allowed_st})")
    for df in ("last_triggered","updated"):
        v = fm.get(df,"")
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(v)):
            errs.append(f"bad {df} format '{v}' (need YYYY-MM-DD)")
    return errs


def validate_fm_dir(d, required, allowed_st, label, ceiling_key):
    """Validate all .md files in directory d. Returns error list."""
    errs = []
    for f in sorted(d.glob("*.md")):
        if f.name.startswith("_"): continue
        lines, e = rd(f)
        if e: errs.append(f"{label}/{f.name}: {e}"); continue
        fm = parse_fm("".join(lines))
        if not fm: errs.append(f"{label}/{f.name}: bad/missing frontmatter"); continue
        for ve in fm_check(fm, required, allowed_st):
            errs.append(f"{label}/{f.name}: {ve}")
        n = lc(f)
        if n > CEIL[ceiling_key]:
            errs.append(f"{label}/{f.name}: {n}L > ceiling {CEIL[ceiling_key]}")
    return errs


# ── Prompt mode ─────────────────────────────────────────────────────────────

def mode_prompt():
    today = date.today().isoformat()
    slug = detect_project()
    def _summarize(d, label):
        out = []
        for f in sorted(d.glob("*.md")):
            if f.name.startswith("_"): continue
            fm = parse_fm("".join(rd(f)[0]))
            if fm:
                if label == "rules":
                    out.append(f"  {f.name} ltr={fm.get('last_triggered','?')} pri={fm.get('priority','?')} st={fm.get('status','?')}")
                else:
                    out.append(f"  {f.name} st={fm.get('status','?')} upd={fm.get('updated','?')}")
        return "\n".join(out) if out else "  (none)"

    root_note = ""
    if ROOT_MD.exists():
        n = lc(ROOT_MD)
        if n > 80: root_note = f"\n  CLAUDE.md: {n} lines (guideline: 80, ceiling: {CEIL['root']})"

    print(f"""## Session Close Protocol / 会话关闭协议 — {today}

### Active: {slug or 'Unknown (specify in Q3)'}

**Rules:**
{_summarize(RULES_D, 'rules')}

**Projects:**
{_summarize(PROJS_D, 'projects')}

**Ceiling proximity:**{root_note or ' OK'}

---

### Phase 1 — Quick Close / 快速关闭 (MUST execute / 必须执行)

**Review the session transcript first.** Scan for decisions, resolved errors, and user preferences. Extract them NOW — do NOT rely on having written annotations mid-session. You were focused on work, not note-taking. The transcript is your raw material. / 先回顾会话 transcript，从中提取所有决策和错误修复——不要依赖会话中途的笔记。

Write to `.claude/memory/_phase1_inbox.md` unless otherwise specified.

**① Decisions / 技术决策**
Format: `[DECISION: <summary> | context: <why> | project: <slug> | scope: project|cross-project]`
→ Project-scoped: `<projects/<slug>.md>` Recent Milestones
→ Cross-project: `.claude/memory/decisions/<slug>.md`
→ Fallback: `<inbox>`

**② Errors / 错误及方案**
Format: `[ERROR: type=<from-taxonomy> | resolution=<fix> | project: <slug>]`
→ `.claude/memory/pitfalls/<slug>.md` or `<inbox>`
Anti-pollution (反污染): Only store FIXED errors. UNRESOLVED → leave in inbox.
Duplicate (same type+root_cause_id) → update sessions_observed counter only.

**③ Project Status / 项目状态**
Update `projects/<slug>.md` frontmatter: `updated: {today}`. If `status` enum changed → update `status` too. Or "No change."

**④ Rule Trigger Update / 规则触发更新 (CRITICAL — do now)**
Search `rules/*.md` by `domain` field in YAML frontmatter → update `last_triggered: {today}`. Not found → write to inbox. This MUST happen in Phase 1 — deferred audit may never run on non-CC platforms.

**⑤ Hard Ceiling Check / 硬上限检查 (CRITICAL — do now)**
Check root=100, rule=80, project=60. Any file exceeds ceiling → flag in [SESSION_SUMMARY] + trigger Split Protocol or warn user.

**MVA Check (最低可行标注)**: [DECISION:] needs summary+context+project. [ERROR:] needs type+resolution+project. Missing → mark `# MVA_FAIL:<field>` and leave in inbox.

### Phase 2 — Deferred Audit / 延迟审计 (Optional, T3 can supplement)

**⑥ Rules created/modified?** Update `rules/<domain>.md` or "None."
**⑦ Rules outdated?** Add `<!-- DEPRECATED: <reason> -->` in rule file or "None."

### [SESSION_SUMMARY]
After answering, emit summary block:
`[SESSION_SUMMARY: decisions: [...], errors: [...], rules_triggered: [...], project_status_changed: true|false, files_over_ceiling: [...]]`

---
**Note**: F2 (user口令 "收尾") is the PRIMARY knowledge capture mechanism — works on ALL platforms. F3 auto-checkpoints are a best-effort bonus. T2 supplements with context, metadata, and cross-references.
_Run: `python .claude/skills/obsidian-knowledge-brain/scripts/session_close.py --validate` after answering._""")


# ── Validate mode ───────────────────────────────────────────────────────────

def validate_inbox():
    """Validate _phase1_inbox.md exists and contains well-formed entries."""
    errs = []
    if not INBOX.exists():
        errs.append("_phase1_inbox.md: MISSING — inbox file does not exist (HIGH severity)")
        return errs
    lines, e = rd(INBOX)
    if e:
        errs.append(f"_phase1_inbox.md: read error: {e}")
        return errs
    if not lines or all(not l.strip() or l.strip().startswith('#') or l.strip().startswith('>') or l.strip() == '---' for l in lines):
        # File exists but has no annotation entries — this is OK for a fresh project
        return errs
    text = "".join(lines)
    for m in DEC_RE.finditer(text):
        if not m.group(1).strip(): errs.append("_phase1_inbox.md: [DECISION:] empty summary")
        if not m.group(2).strip(): errs.append("_phase1_inbox.md: [DECISION:] missing context")
        if m.group(4) and m.group(4) not in ("project", "cross-project"):
            errs.append(f"_phase1_inbox.md: [DECISION:] invalid scope '{m.group(4)}' (must be project|cross-project)")
    for m in ERR_RE.finditer(text):
        if not m.group(1).strip(): errs.append("_phase1_inbox.md: [ERROR:] empty type=")
        if not m.group(2).strip(): errs.append("_phase1_inbox.md: [ERROR:] missing resolution")
    return errs


def mode_validate():
    all_errs = (
        validate_inbox() +
        validate_fm_dir(RULES_D, REQ_R, ST_R, "rules", "rule") +
        validate_fm_dir(PROJS_D, REQ_P, ST_P, "projects", "project")
    )
    # Root CLAUDE.md ceiling check
    if ROOT_MD.exists():
        n = lc(ROOT_MD)
        if n > CEIL["root"]: all_errs.append(f"CLAUDE.md: {n}L > ceiling {CEIL['root']}")
    if all_errs:
        print("INVALID:")
        for e in all_errs: print(f"  - {e}")
        print(f"\n{len(all_errs)} error(s).")
        sys.exit(1)
    print("VALID")
    sys.exit(0)


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: session_close.py --prompt | --validate"); sys.exit(1)
    m = sys.argv[1]
    if m == "--prompt": mode_prompt()
    elif m == "--validate": mode_validate()
    else: print(f"Unknown mode: {m}\nUsage: session_close.py --prompt | --validate"); sys.exit(1)
