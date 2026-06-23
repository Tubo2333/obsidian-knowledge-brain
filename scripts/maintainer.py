"""Step 3: Rule maintenance — smart cards, rule merging, expiration, cleanup.

Philosophy: Every card must contain a CONCRETE rule, not "TBD".
Before creating a new rule, check if existing rules already cover it.
When rules overlap, suggest merging — don't pile up.
"""
import os
import re
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def _get_project_root():
    """Detect project root from script location or CWD."""
    sd = Path(__file__).resolve().parent
    c = sd.parent.parent
    if (c / "CLAUDE.md").exists() and (c / ".claude").exists():
        return str(c)
    cwd = Path.cwd().resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "CLAUDE.md").exists() and (p / ".claude").exists():
            return str(p)
    return str(cwd)

_DEFAULT_ROOT = _get_project_root()
_DEFAULT_CLAUDE_MD = os.path.join(_DEFAULT_ROOT, "CLAUDE.md")

def run(cfg, dry_run=False, step_results=None):
    vault = cfg['vault_path']
    learnings = step_results.get('analyze', {}).get('learnings', []) if step_results else []
    patterns = step_results.get('analyze', {}).get('patterns', []) if step_results else []

    actions = []
    cards_generated = 0
    merges_suggested = 0

    # ── Process learnings (from deep analysis) ──
    for l in learnings:
        action = l.get('action', 'review')
        if action == 'new_rule':
            card_id = generate_learning_card(vault, l, dry_run)
            if card_id:
                cards_generated += 1
                actions.append(f"New rule card: {card_id}")
        elif action == 'merge':
            card_id = generate_merge_card(vault, l, dry_run)
            if card_id:
                merges_suggested += 1
                actions.append(f"Merge card: {card_id}")
        elif action == 'reinforce':
            # Update last_triggered on the existing rule
            rule_id = l.get('suggested_rule_id', '')
            if rule_id:
                touch_rule(vault, rule_id, dry_run)
                actions.append(f"Reinforced: {rule_id}")

    # Fallback: if no learnings (LLM+heuristic both failed), use raw patterns
    if not learnings:
        for p in patterns:
            if len(p.get('projects', [])) >= 3:
                card_id = generate_pattern_card(vault, p, dry_run)
                if card_id:
                    cards_generated += 1
                    actions.append(f"Pattern card: {card_id}")

    # ── Rule maintenance ──
    rules_dir = os.path.join(vault, '00-Rules')
    archived = expire_rules(rules_dir, dry_run)
    promoted = promote_beta_rules(rules_dir, dry_run)
    actions.extend(archived)
    actions.extend(promoted)

    # Clean _rejected/ (30+ days)
    cleaned = clean_rejected(vault, dry_run)
    actions.extend(cleaned)

    # Update trigger_counts from session summaries
    updated = update_trigger_counts(vault, dry_run)
    actions.extend(updated)

    return {
        "cards_generated": cards_generated,
        "merges_suggested": merges_suggested,
        "rules_archived": len(archived),
        "rules_promoted": len(promoted),
        "rejected_cleaned": len(cleaned),
        "actions": actions
    }


# ── Smart Card Generation (from deep learnings) ────────────

def generate_learning_card(vault, learning, dry_run):
    """Create an _inbox/ approval card with CONCRETE rule text from a learning.
    Returns card_id or None if already exists."""
    inbox_dir = os.path.join(vault, '00-Rules', '_inbox')
    rule_id = learning.get('suggested_rule_id', '')
    if not rule_id:
        return None

    card_id = f"inbox-{rule_id.lower()}"
    card_path = os.path.join(inbox_dir, f"{card_id}.md")

    if os.path.exists(card_path) and not dry_run:
        return None

    root_cause = learning.get('root_cause', 'Unknown')
    principle = learning.get('principle', '')
    rule_text = learning.get('suggested_rule_text', '')
    impact = learning.get('impact', 'medium')
    total_occ = learning.get('total_occurrences', 0)
    projects = learning.get('projects_affected', [])

    # If the LLM didn't provide rule text, synthesize from principle
    if not rule_text or rule_text.strip() == '':
        rule_text = f"原则: {principle}\n\n具体操作: (需要人工补充)"

    content = f"""---
status: pending
proposed: {datetime.now().strftime('%Y-%m-%d')}
proposed_by: scanner
rule_id: {rule_id}
root_cause: "{root_cause}"
principle: "{principle}"
impact: {impact}
total_occurrences: {total_occ}
projects_affected: {projects}
priority: {"high" if impact == 'high' else "medium"}
review_deadline: {(datetime.now() + timedelta(days=14 if impact == 'high' else 30)).strftime('%Y-%m-%d')}
---

# 📌 Proposed Rule: {learning.get('suggested_rule_title', rule_id)}

## Root Cause
{root_cause}

## Principle
{principle}

## Evidence
- {total_occ} occurrences across {len(projects)} project(s): {', '.join(projects)}
- Impact: {impact}

## Rule Text
{rule_text}

## Affected Errors
{', '.join(learning.get('affected_errors', []))}

---
Approve: Move this file from _inbox/ to 00-Rules/ and set status: active
Reject: Move to _inbox/_rejected/
"""

    if not dry_run:
        if os.path.exists(card_path):
            backup_pre_modification(vault, card_path)
        tmp_path = card_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, card_path)

    return card_id


def generate_merge_card(vault, learning, dry_run):
    """Create a card suggesting merging of overlapping rules."""
    inbox_dir = os.path.join(vault, '00-Rules', '_inbox')
    related = learning.get('related_existing_rules', [])
    if len(related) < 2:
        return None

    card_id = f"merge-{'-'.join(r.lower().replace('_', '-') for r in related[:3])}"
    card_path = os.path.join(inbox_dir, f"{card_id}.md")

    if os.path.exists(card_path) and not dry_run:
        return None

    merge_text = learning.get('merge_suggestion', '')
    content = f"""---
status: pending
proposed: {datetime.now().strftime('%Y-%m-%d')}
proposed_by: scanner
type: merge
rules_to_merge: {related}
rationale: "{merge_text}"
review_deadline: {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}
---

# 🔀 Merge Suggestion: {' + '.join(related)}

## Rationale
{merge_text}

## Rules to Merge
{chr(10).join(f'- {r}' for r in related)}

## Suggested Action
1. Review each rule's content
2. Create a new unified rule
3. Archive the old rules
"""
    if not dry_run:
        tmp_path = card_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, card_path)
    return card_id


def generate_pattern_card(vault, pattern, dry_run):
    """Fallback: generate a card from a raw pattern (no deep analysis available)."""
    inbox_dir = os.path.join(vault, '00-Rules', '_inbox')
    projects = pattern['projects']
    etype = pattern['error_type']
    n_projects = len(projects)
    n_occurrences = pattern['count']

    confidence_auto = min(0.95, 0.3 * (n_projects ** 0.5) + 0.05 * n_occurrences)

    card_id = f"inbox-{etype}"
    card_path = os.path.join(inbox_dir, f"{card_id}.md")
    if os.path.exists(card_path) and not dry_run:
        return None

    resolutions = list(set(c['resolution'] for c in pattern['contexts'] if c['resolution']))

    content = f"""---
status: pending
proposed: {datetime.now().strftime('%Y-%m-%d')}
proposed_by: scanner (pattern fallback — no deep analysis)
confidence_auto: {confidence_auto:.2f}
one_liner: "Error pattern: {etype} across {', '.join(projects)}"
evidence: "{n_projects} projects, {n_occurrences} occurrences — {', '.join(resolutions[:2])}"
affected_projects: {projects}
priority: {"high" if confidence_auto > 0.7 else "medium"}
review_deadline: {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}
---

# 📌 Proposed Rule: {etype}

## Pattern
Error type `{etype}` detected in {n_projects} projects ({n_occurrences} total).

## Evidence
{chr(10).join(f'- [{c["project"]}] {c["session"]}: {c["resolution"][:100]}' for c in pattern['contexts'][:5])}

## Suggested Rule
⚠️ This card was generated from raw patterns without deep analysis.
A human should review and write the specific rule text.
"""
    if not dry_run:
        tmp_path = card_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, card_path)
    return card_id


def touch_rule(vault, rule_id, dry_run):
    """Update last_triggered timestamp on an existing rule."""
    rule_path = os.path.join(vault, '00-Rules', f"{rule_id}.md")
    if not os.path.exists(rule_path):
        return
    if dry_run:
        return
    try:
        with open(rule_path, 'r', encoding='utf-8') as f:
            content = f.read()
        parts = content.split('---', 2)
        if len(parts) < 3:
            return
        fm = yaml.safe_load(parts[1])
        fm['last_triggered'] = datetime.now().strftime('%Y-%m-%d')
        new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False)
        new_content = f"---\n{new_fm}---\n{parts[2]}"
        tmp = rule_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(new_content)
        os.replace(tmp, rule_path)
    except Exception:
        pass


def expire_rules(rules_dir, dry_run):
    """Archive rules based on expires field and last_triggered age."""
    actions = []
    archive_dir = os.path.join(rules_dir, '_archive')
    today = datetime.now()

    for f in os.listdir(rules_dir):
        if not f.endswith('.md') or f.startswith('_'):
            continue
        fp = os.path.join(rules_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm = yaml.safe_load(content.split('---')[1])
        except (yaml.YAMLError, IndexError):
            continue

        should_archive = False
        reason = ""

        # Hard expiry
        if fm.get('expires'):
            expires_date = datetime.fromisoformat(fm['expires'])
            if today > expires_date:
                should_archive = True
                reason = f"expired {fm['expires']}"

        # Soft expiry: >=90 days since last_triggered
        if not should_archive and fm.get('last_triggered'):
            last_trig = datetime.fromisoformat(fm['last_triggered'])
            if (today - last_trig).days >= 90:
                should_archive = True
                reason = f"unused for {(today - last_trig).days} days"

        if should_archive:
            if not dry_run:
                backup_pre_modification(rules_dir, fp)
                fm['status'] = 'archived'
                fm['archived_at'] = today.strftime('%Y-%m-%d')
                fm['archived_by'] = 'script'
                fm['archival_reason'] = reason
                # Move to _archive
                shutil.move(fp, os.path.join(archive_dir, f))
            actions.append(f"Archived rule {f}: {reason}")

    return actions

def promote_beta_rules(rules_dir, dry_run):
    """Promote beta rules to active after 30-day observation."""
    actions = []
    today = datetime.now()

    for f in os.listdir(rules_dir):
        if not f.endswith('.md') or f.startswith('_'):
            continue
        fp = os.path.join(rules_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm = yaml.safe_load(content.split('---')[1])
        except (yaml.YAMLError, IndexError):
            continue

        if fm.get('status') == 'beta' and fm.get('beta_since'):
            beta_since = datetime.fromisoformat(fm['beta_since'])
            if (today - beta_since).days >= 30:
                if not dry_run:
                    backup_pre_modification(rules_dir, fp)
                    fm['status'] = 'active'
                    new_content = f"---\n{yaml.dump(fm, allow_unicode=True)}---\n{content.split('---', 2)[2]}"
                    # Atomic write
                    tmp_path = fp + '.tmp'
                    with open(tmp_path, 'w', encoding='utf-8') as fh:
                        fh.write(new_content)
                    os.replace(tmp_path, fp)
                actions.append(f"Promoted rule {f}: beta->active")

    return actions

def clean_rejected(vault, dry_run):
    """Delete rejected cards older than 30 days."""
    actions = []
    rejected_dir = os.path.join(vault, '00-Rules', '_inbox', '_rejected')
    if not os.path.exists(rejected_dir):
        return actions
    today = datetime.now()

    for f in os.listdir(rejected_dir):
        fp = os.path.join(rejected_dir, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(fp))
        if (today - mtime).days >= 30:
            if not dry_run:
                os.remove(fp)
            actions.append(f"Cleaned rejected: {f}")

    return actions

def update_trigger_counts(vault, dry_run):
    """Update rule trigger_count from weekly session summaries."""
    actions = []
    # This runs after analyzer has processed all sessions
    # For now, placeholder — detailed implementation in Phase 2 iteration
    return actions

def backup_pre_modification(vault, filepath):
    """Copy file to _rollback before modification."""
    rollback_dir = os.path.join(vault, '04-Feedback', '_rollback', datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(rollback_dir, exist_ok=True)
    rel = os.path.relpath(filepath, vault)
    dst = os.path.join(rollback_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(filepath, dst)


# ═══════ Health Check mode (design spec §8.2) ═══════

def count_lines(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return len(f.readlines())


def parse_frontmatter(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        parts = content.split('---', 2)
        if len(parts) < 3: return None
        fm = yaml.safe_load(parts[1])
        return fm if isinstance(fm, dict) else None
    except (yaml.YAMLError, Exception):
        return None


def _norm(raw):
    """Normalize a directive to a comparable key (lowercase, no stopwords)."""
    stop = {'the','a','an','is','are','was','were','be','been','in','on','at',
            'to','for','of','with','from','by','and','or','not','that','this',
            'it','its','s','all','any','when','where','which','who','whom'}
    c = re.sub(r'`[^`]+`', 'CODE', raw)
    c = re.sub(r'[^\w\s]', ' ', c)
    terms = [w for w in re.sub(r'\s+',' ',c).strip().lower().split() if w not in stop]
    return ' '.join(terms) if len(terms) >= 2 else ''


def check_contradictions(rules_dir):
    """Return [(filepath, detail)] for MUST vs NEVER conflicts across rules."""
    if not os.path.isdir(rules_dir): return []
    must, never = {}, {}
    for f in sorted(os.listdir(rules_dir)):
        if not f.endswith('.md') or f.startswith('_'): continue
        fp = os.path.join(rules_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                text = fh.read()
        except Exception: continue
        for m in re.finditer(r'\*\*MUST\*\*\s+(.+?)(?:\.|\n|$)', text):
            k = _norm(m.group(1).strip())
            if k: must.setdefault(k, []).append(f)
        for m in re.finditer(r'\*\*NEVER\*\*\s+(.+?)(?:\.|\n|$)', text):
            k = _norm(m.group(1).strip())
            if k: never.setdefault(k, []).append(f)
        for m in re.finditer(r'\*\*DO\s+NOT\*\*\s+(.+?)(?:\.|\n|$)', text):
            k = _norm(m.group(1).strip())
            if k: never.setdefault(k, []).append(f)
    out = []
    for k in must:
        if k in never and set(must[k]) != set(never[k]):
            out.append((os.path.join(rules_dir, must[k][0]),
                f"contradiction: MUST vs NEVER re '{k}' — MUST:{must[k]} NEVER:{never[k]}"))
    return out


def regenerate_keyword_index(rules_dir, output_path):
    """Generate _keyword_index.json. Returns keyword count."""
    if not os.path.isdir(rules_dir): return 0
    def _clean(kw):
        kw = kw.strip().lower().strip('\'"`-')
        if len(kw) < 3 or len(kw) > 60: return None
        if '\n' in kw: return None
        if kw[0] not in 'abcdefghijklmnopqrstuvwxyz0123456789': return None
        if any(c in kw for c in '"<>[]'): return None
        return kw

    idx = {}
    for f in sorted(os.listdir(rules_dir)):
        if not f.endswith('.md') or f.startswith('_'): continue
        fp = os.path.join(rules_dir, f)
        ref = f"rules/{f}"
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                text = fh.read()
        except Exception: continue
        fm = parse_frontmatter(fp)
        if fm and fm.get('domain'):
            for p in re.split(r'[-_]', str(fm['domain'])):
                kw = _clean(p)
                if kw: idx.setdefault(kw, []).append(ref)
        for m in re.finditer(r'^##\s+(.+)$', text, re.MULTILINE):
            for kw in re.split(r'[,/&]', m.group(1).strip().lower()):
                kw = re.sub(r'[^\w-]', '', kw)
                kw = _clean(kw)
                if kw: idx.setdefault(kw, []).append(ref)
        for m in re.finditer(r'`([^`\n]+)`', text):
            kw = _clean(m.group(1))
            if kw: idx.setdefault(kw, []).append(ref)
        for m in re.finditer(r'\*\*(MUST|NEVER|DO)\*\*\s+(.+?)(?:\.|\n|$)', text):
            words = re.sub(r'[^\w\s]', ' ', m.group(2).strip()[:60]).split()
            if len(words) >= 2:
                kw = _clean(' '.join(words[:3]))
                if kw: idx.setdefault(kw, []).append(ref)
    for kw in idx:
        seen, uniq = set(), []
        for r in idx[kw]:
            if r not in seen: seen.add(r); uniq.append(r)
        idx[kw] = uniq
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(idx, f, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(output_path + '.tmp', output_path)
    return len(idx)


def find_orphans(root_claude_md, rules_dir, projects_dir):
    """Return list of files in rules/ or projects/ not in root index."""
    orphans = []
    if not os.path.isfile(root_claude_md): return orphans
    try:
        with open(root_claude_md, 'r', encoding='utf-8', errors='replace') as f:
            root_text = f.read()
    except Exception: return orphans
    for d in [rules_dir, projects_dir]:
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            if f.endswith('.md') and not f.startswith('_') and f not in root_text:
                orphans.append(os.path.join(d, f))
    return orphans


def health_check(cfg):
    """Run 9 health checks per design spec §8.2. Returns {violations, notes, fail_count, note_count}."""
    root = os.path.dirname(cfg.get('claude_md_path', _DEFAULT_CLAUDE_MD))
    rules_dir = os.path.join(root, '.claude', 'rules')
    projects_dir = os.path.join(root, '.claude', 'projects')
    scripts_dir = os.path.join(root, '.claude', 'scripts')
    root_md = os.path.join(root, 'CLAUDE.md')
    marker = os.path.join(root, '.claude', '.session_active')
    violations, notes = [], []
    today = datetime.now()

    # Check 1 & 2: Hard ceiling + soft guideline
    limits = [
        (rules_dir, '.md', 80, 60, 'rule'),
        (projects_dir, '.md', 60, 40, 'project'),
        (scripts_dir, '.py', 700, 700, 'script'),
    ]
    for d, ext, ceil, guide, label in limits:
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if f.endswith(ext) and not f.startswith('_'):
                fp = os.path.join(d, f)
                n = count_lines(fp)
                nf = fp.replace('\\', '/')
                if n > ceil:
                    violations.append((nf, f"{label}:{f} exceeds hard ceiling ({n}/{ceil} lines)", "HIGH"))
                elif n > guide:
                    notes.append((nf, f"{label}:{f} over guideline ({n}/{guide} lines)", "LOW"))
    if os.path.isfile(root_md):
        n = count_lines(root_md)
        nf = root_md.replace('\\', '/')
        if n > 100: violations.append((nf, f"root:CLAUDE.md exceeds hard ceiling ({n}/100 lines)", "HIGH"))
        elif n > 80: notes.append((nf, f"root:CLAUDE.md over guideline ({n}/80 lines)", "LOW"))

    # Check 3: Frontmatter completeness
    r_req = {'schema_version','domain','priority','last_triggered','status'}
    p_req = {'schema_version','project','status','updated'}
    for d, req in [(rules_dir, r_req), (projects_dir, p_req)]:
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if not f.endswith('.md') or f.startswith('_'): continue
            fp = os.path.join(d, f)
            fm = parse_frontmatter(fp)
            if fm is None:
                violations.append((fp.replace('\\', '/'), f"missing/invalid YAML frontmatter", "HIGH"))
                continue
            missing = req - set(fm.keys())
            if missing:
                violations.append((fp.replace('\\', '/'), f"missing frontmatter: {sorted(missing)}", "MEDIUM"))

    # Check 4: Inactive rule detection
    if os.path.isdir(rules_dir):
        for f in sorted(os.listdir(rules_dir)):
            if not f.endswith('.md') or f.startswith('_'): continue
            fp = os.path.join(rules_dir, f)
            fm = parse_frontmatter(fp)
            if not fm: continue
            pri = fm.get('priority')
            lt = fm.get('last_triggered')
            if pri is None or not lt: continue
            try:
                lt_date = lt if isinstance(lt, datetime) else datetime.fromisoformat(str(lt).strip())
                days = (today - lt_date).days
                if isinstance(pri, (int, float)):
                    if 1 <= pri <= 5 and days > 180:
                        violations.append((fp.replace('\\', '/'),
                            f"operation rule (pri={int(pri)}) inactive {days}d (threshold 180d)", "MEDIUM"))
                    elif 6 <= pri <= 10 and days > 365:
                        violations.append((fp.replace('\\', '/'),
                            f"domain rule (pri={int(pri)}) inactive {days}d (threshold 365d)", "LOW"))
            except (ValueError, TypeError):
                notes.append((fp.replace('\\', '/'), f"unparseable last_triggered: {lt}", "LOW"))

    # Check 5: Contradiction scan
    for fp, detail in check_contradictions(rules_dir):
        violations.append((fp.replace('\\', '/'), detail, "MEDIUM"))

    # Check 6: Keyword index
    kip = os.path.join(rules_dir, '_keyword_index.json')
    kc = regenerate_keyword_index(rules_dir, kip)
    notes.append(("keyword-index", f"regenerated {kc} keywords → {kip.replace('\\', '/')}", "LOW"))

    # Check 7: Orphan detection
    for fp in find_orphans(root_md, rules_dir, projects_dir):
        violations.append((fp.replace('\\', '/'), "not in root CLAUDE.md index (orphan)", "MEDIUM"))

    # Check 8: Stale session marker
    if os.path.isfile(marker):
        try:
            mt = datetime.fromtimestamp(os.path.getmtime(marker))
            hrs = (today - mt).total_seconds() / 3600
            if hrs > 24:
                violations.append((marker.replace('\\', '/'),
                    f"stale session marker ({hrs:.0f}h, thresh 24h) — possible crash", "MEDIUM"))
        except OSError: pass

    return {'violations': violations, 'notes': notes,
            'fail_count': len(violations), 'note_count': len(notes)}


def generate_health_report(result, cfg):
    """Write HEALTH_REPORT.md (≤30 lines). Returns path."""
    root = os.path.dirname(cfg.get('claude_md_path', _DEFAULT_CLAUDE_MD))
    rp = os.path.join(root, '.claude', 'HEALTH_REPORT.md')
    v = result['violations']
    n = result['notes']
    hi = sum(1 for _, _, s in v if s == 'HIGH')
    md = sum(1 for _, _, s in v if s == 'MEDIUM')
    lo = sum(1 for _, _, s in v if s == 'LOW')
    lines = [f"# Health Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             f"**Summary**: {result['fail_count']} violation(s) [{hi} HIGH, {md} MEDIUM, {lo} LOW]; {result['note_count']} info note(s)", ""]
    if v:
        lines.append("## Violations")
        for fp, desc, sev in v: lines.append(f"- `{fp}` — {desc}  [{sev}]")
        lines.append("")
    if n:
        lines.append("## Info")
        for fp, desc, _ in n: lines.append(f"- `{fp}` — {desc}")
        lines.append("")
    if len(lines) > 30: lines = lines[:29] + [f"... (truncated)"]
    content = '\n'.join(lines).strip() + '\n'
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    with open(rp + '.tmp', 'w', encoding='utf-8') as f: f.write(content)
    os.replace(rp + '.tmp', rp)
    return rp


if __name__ == '__main__':
    import sys
    if '--health-check' in sys.argv:
        try:
            from config import load_config
            cfg = load_config()
        except Exception:
            cfg = {'claude_md_path': _DEFAULT_CLAUDE_MD}
        result = health_check(cfg)
        rp = generate_health_report(result, cfg)
        print(f"Health report: {rp}")
        print(f"  Violations: {result['fail_count']}  |  Info notes: {result['note_count']}")
        for fp, desc, sev in result['violations']:
            print(f"    [{sev}] {desc}")
        sys.exit(0 if result['fail_count'] == 0 else 1)
    else:
        print("Usage: python maintainer.py --health-check")
        sys.exit(1)
