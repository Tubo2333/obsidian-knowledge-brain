"""Step 3: Rule maintenance — approval cards, expiration, cleanup.

Automates the rule lifecycle:
- Generates approval cards for cross-project patterns (>=3 projects)
- Archives expired rules (hard expiry date or 90-day inactivity)
- Promotes beta rules to active after 30-day observation period
- Cleans rejected cards older than 30 days
- Updates rule trigger counts from session summaries
"""

import os
import yaml
import shutil
from datetime import datetime, timedelta


def run(cfg, dry_run=False, step_results=None):
    vault = cfg['vault_path']
    patterns = (step_results.get('analyze', {}).get('patterns', [])
                if step_results else [])

    actions = []

    # Generate approval cards for cross-project patterns (>=3 projects)
    cards_generated = 0
    for p in patterns:
        if len(p.get('projects', [])) >= 3:
            card_id = generate_approval_card(vault, p, dry_run)
            if card_id:
                cards_generated += 1
                actions.append(f"Generated card: {card_id}")

    # Rule maintenance
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
        "rules_archived": len(archived),
        "rules_promoted": len(promoted),
        "rejected_cleaned": len(cleaned),
        "actions": actions
    }


def generate_approval_card(vault, pattern, dry_run):
    """Create an _inbox/ approval card from a detected pattern."""
    inbox_dir = os.path.join(vault, '00-Rules', '_inbox')
    projects = pattern['projects']
    n_projects = len(projects)
    n_occurrences = pattern['count']

    confidence_auto = min(0.95,
                          0.3 * (n_projects ** 0.5) + 0.05 * n_occurrences)

    card_id = f"inbox-{pattern['error_type']}"
    card_path = os.path.join(inbox_dir, f"{card_id}.md")

    if os.path.exists(card_path) and not dry_run:
        return None  # Already exists

    resolutions = list(set(c['resolution']
                           for c in pattern['contexts']
                           if c['resolution']))
    evidence = (f"{n_projects} projects, {n_occurrences} occurrences"
                f" — {', '.join(resolutions[:2])}")

    stability = "stable" if confidence_auto > 0.7 else "emerging"

    content = f"""---
status: pending
proposed: {datetime.now().strftime('%Y-%m-%d')}
proposed_by: scanner
confidence_auto: {confidence_auto:.2f}
confidence_note: "{n_projects} projects, {n_occurrences} occurrences — pattern is {stability}"
one_liner: "Error pattern: {pattern['error_type']} across {', '.join(projects)}"
evidence: "{evidence}"
affected_projects: {projects}
priority: {"high" if confidence_auto > 0.7 else "medium"}
skip_count: 0
skip_until: null
review_deadline: {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}
related_rules: []
approved_by: null
approved_at: null
target_rule_id: null
---

# Proposed Rule: {pattern['error_type']}

## One-Liner
Error type `{pattern['error_type']}` detected in {n_projects} projects \
({n_occurrences} total occurrences).

## Evidence
{evidence}

## Affected Projects
{', '.join(projects)}

## Suggested Rule
(TBD — refine during approval)
"""

    if not dry_run:
        # Backup before write
        if os.path.exists(card_path):
            backup_pre_modification(vault, card_path)
        # Atomic write: .tmp -> rename
        os.makedirs(inbox_dir, exist_ok=True)
        tmp_path = card_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, card_path)

    return card_id


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
                os.makedirs(archive_dir, exist_ok=True)
                shutil.move(fp, os.path.join(archive_dir, f))
            actions.append(f"Archived rule {f}: {reason}")

    return actions


def promote_beta_rules(rules_dir, dry_run):
    """Promote beta rules to active after 30-day observation period."""
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
                    new_fm = yaml.dump(fm, allow_unicode=True)
                    body = content.split('---', 2)[2]
                    new_content = f"---\n{new_fm}---\n{body}"
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
    """Update rule trigger_count from weekly session summaries.

    This runs after analyzer has processed all sessions.
    For now, placeholder — detailed implementation in future iteration.
    """
    return []


def backup_pre_modification(vault, filepath):
    """Copy file to _rollback before modification."""
    rollback_dir = os.path.join(vault, '04-Feedback', '_rollback',
                                 datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(rollback_dir, exist_ok=True)
    rel = os.path.relpath(filepath, vault)
    dst = os.path.join(rollback_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(filepath, dst)
