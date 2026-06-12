"""Step 4: Generate weekly report, update metrics, rebuild index, update heartbeat.

Generates:
- Weekly report Markdown file in 04-Feedback/weekly-reports/
- Rebuilt search index (03-Maps/search-index.md)
- Auto-rebuilt topic index and timeline (03-Maps/topic-index.md, timeline.md)
- Updated heartbeat with processed_sessions for incremental scanning

The topic_map for auto-generated maps is read from config.yaml.
"""

import os
import yaml
import re
from datetime import datetime
from collections import defaultdict


def run(cfg, dry_run=False, step_results=None, missed_weeks=0):
    vault = cfg['vault_path']
    week = datetime.now().strftime('%Y-W%W')

    report_path = os.path.join(vault, '04-Feedback', 'weekly-reports',
                                f'{week}.md')

    # Gather data from previous steps
    backup = step_results.get('backup', {}) if step_results else {}
    analyze = step_results.get('analyze', {}) if step_results else {}
    maintain = step_results.get('maintain', {}) if step_results else {}

    patterns = analyze.get('patterns', [])
    cards = maintain.get('cards_generated', 0)
    archived = maintain.get('rules_archived', 0)

    # Build session count
    sessions_scanned = analyze.get('sessions_scanned', 0)
    sessions_total = count_session_files(vault)
    processed_sessions = backup.get('processed_ids', {})

    # Generate report content
    patterns_list = ''
    if patterns:
        patterns_list = '\n'.join([
            f"- **{p.get('error_type', 'unknown')}**: "
            f"{p.get('count', 0)} occurrences in {p.get('projects', [])}"
            for p in patterns
        ])
    else:
        patterns_list = 'No new patterns this week.'

    report_content = f"""---
week: "{week}"
date: {datetime.now().strftime('%Y-%m-%d')}
scan_status: ok
sessions_scanned: {sessions_scanned}
sessions_total: {sessions_total}
scan_duration_sec: 0
errors_during_scan: []
new_patterns_detected: {len(patterns)}
new_rules_proposed: {cards}
rules_awaiting_approval: {count_pending_inbox(vault)}
rules_approved_this_week: 0
rules_archived_this_week: {archived}
missed_weeks: {missed_weeks}
heartbeat_ok: true
---

# Weekly Report {week}

## Metric Snapshot

| Metric | This Week | Baseline Avg | Trend |
|--------|-----------|--------------|-------|
| Repeat Error Rate | - | - | - |
| Rule Hit Rate (by category) | - | - | - |
| Inbox Backlog | {count_pending_inbox(vault)} | - | - |

## New Patterns Detected

{len(patterns)} pattern(s) found.

{patterns_list}

## Pending Approvals

{count_pending_inbox(vault)} rule(s) in inbox.

## Alerts

No alerts this week.

## Weekly Highlight

Weekly scanner running.
"""

    if not dry_run:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        atomic_write(report_path, report_content)

        # Rebuild search index
        rebuild_search_index(vault)

        # Auto-rebuild maps (topic-index + timeline) so they never go stale
        # 自动重建地图，确保主题索引和时间线永不过时
        topic_map = cfg.get('topic_map', {})
        rebuild_maps(vault, topic_map)

        # Update heartbeat with processed_sessions for incremental scan
        update_heartbeat(vault, sessions_scanned, processed_sessions)
    else:
        # Dry-run: still validate paths, don't write
        pass

    return {
        "report": report_path,
        "week": week,
        "patterns_reported": len(patterns),
        "index_rebuilt": not dry_run
    }


def atomic_write(filepath, content):
    """Write content to file atomically: write to .tmp then os.rename."""
    tmp_path = filepath + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp_path, filepath)


def count_session_files(vault):
    """Count total session summary .md files across all projects."""
    count = 0
    projects_dir = os.path.join(vault, '01-Projects')
    if not os.path.exists(projects_dir):
        return 0
    for proj in os.listdir(projects_dir):
        sessions_dir = os.path.join(projects_dir, proj, 'Memory', 'sessions')
        if os.path.exists(sessions_dir):
            count += len([f for f in os.listdir(sessions_dir)
                          if f.endswith('.md') and not f.startswith('_')])
    return count


def count_pending_inbox(vault):
    """Count pending approval cards."""
    inbox_dir = os.path.join(vault, '00-Rules', '_inbox')
    if not os.path.exists(inbox_dir):
        return 0
    count = 0
    for f in os.listdir(inbox_dir):
        if not f.endswith('.md'):
            continue
        fp = os.path.join(inbox_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm = yaml.safe_load(content.split('---')[1])
            if fm.get('status') == 'pending':
                count += 1
        except (yaml.YAMLError, IndexError):
            pass
    return count


def rebuild_search_index(vault):
    """Rebuild 03-Maps/search-index.md from all session summaries and rules."""
    keywords = {}

    # Scan session summaries
    projects_dir = os.path.join(vault, '01-Projects')
    if not os.path.exists(projects_dir):
        return

    for proj in os.listdir(projects_dir):
        sessions_dir = os.path.join(projects_dir, proj, 'Memory', 'sessions')
        if not os.path.exists(sessions_dir):
            continue
        for f in os.listdir(sessions_dir):
            if not f.endswith('.md') or f.startswith('_'):
                continue
            fp = os.path.join(sessions_dir, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            try:
                fm = yaml.safe_load(content.split('---')[1])
            except (yaml.YAMLError, IndexError):
                continue

            session_id = f.replace('.md', '')
            for tag in fm.get('tags', []):
                kw = tag.lower()
                if kw not in keywords:
                    keywords[kw] = {'sessions': [], 'rules': [], 'decisions': []}
                if session_id not in keywords[kw]['sessions']:
                    keywords[kw]['sessions'].append(session_id)

    # Write index atomically
    maps_dir = os.path.join(vault, '03-Maps')
    os.makedirs(maps_dir, exist_ok=True)
    index_path = os.path.join(maps_dir, 'search-index.md')

    index_content = (
        f"---\nlast_rebuilt: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"keywords:\n"
    )
    for kw, data in sorted(keywords.items()):
        index_content += f"  - keyword: \"{kw}\"\n"
        index_content += f"    sessions: {data['sessions']}\n"
        index_content += f"    rules: {data['rules']}\n"
        index_content += f"    decisions: {data['decisions']}\n"
    index_content += "---\n\n# Search Index\n\n"
    index_content += (
        "| Keyword | Sessions | Rules | Decisions |\n"
        "|---------|----------|-------|----------|\n"
    )
    for kw, data in sorted(keywords.items()):
        index_content += (
            f"| {kw} | {len(data['sessions'])} | "
            f"{len(data['rules'])} | {len(data['decisions'])} |\n"
        )

    atomic_write(index_path, index_content)


def update_heartbeat(vault, sessions_processed, processed_sessions=None):
    """Update heartbeat.md after successful scan."""
    hb_path = os.path.join(vault, '04-Feedback', 'heartbeat.md')
    now = datetime.now().isoformat()

    if processed_sessions is None:
        processed_sessions = {}

    # Build processed_sessions YAML
    ps_yaml = yaml.dump(processed_sessions, allow_unicode=True,
                        default_flow_style=False)
    ps_indented = '\n'.join('  ' + line
                            for line in ps_yaml.strip().split('\n'))

    content = f"""---
last_scan: {now}
scan_status: ok
sessions_processed: {sessions_processed}
processed_sessions:
{ps_indented}
errors: []
script_version: "1.0.0"
---

# Scanner Heartbeat

Last scan: {now}
Status: OK
Sessions processed: {sessions_processed}
"""

    atomic_write(hb_path, content)


def rebuild_maps(vault, topic_map=None):
    """Auto-rebuild 03-Maps/: topic-index + timeline.

    Called weekly so they never go stale.
    自动重建地图：主题索引+时间线。每周调用，永不过时。

    Args:
        vault: Path to the Obsidian vault.
        topic_map: Dict mapping tag -> [topic_name, description].
                   Defaults to empty dict if not provided.
    """
    if topic_map is None:
        topic_map = {}

    sessions = []
    projects_dir = os.path.join(vault, '01-Projects')
    if not os.path.exists(projects_dir):
        return

    for proj in os.listdir(projects_dir):
        sessions_dir = os.path.join(projects_dir, proj, 'Memory', 'sessions')
        if not os.path.exists(sessions_dir):
            continue
        for f in os.listdir(sessions_dir):
            if not f.endswith('.md') or f.startswith('_'):
                continue
            fp = os.path.join(sessions_dir, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            try:
                parts = content.split('---', 2)
                if len(parts) < 3:
                    continue
                fm = yaml.safe_load(parts[1])
            except (yaml.YAMLError, IndexError):
                continue

            body = parts[2] if len(parts) > 2 else ''
            title_match = re.search(r'^#\s+(.+)', body, re.MULTILINE)
            title = (title_match.group(1).strip() if title_match
                     else fm.get('ai_title', 'Untitled'))

            sessions.append({
                'date': fm.get('date', 'unknown'),
                'project': proj,
                'session_id': fm.get('session_id', ''),
                'filename': f.replace('.md', ''),
                'title': title,
                'tags': fm.get('tags', []),
                'decisions': fm.get('decisions_made', []),
                'errors': fm.get('errors_encountered', []),
            })

    if not sessions:
        return

    sessions.sort(key=lambda s: s['date'])

    # Build topic -> session list using config-provided topic_map
    topic_sessions = defaultdict(list)
    untagged = []
    for s in sessions:
        matched = False
        for tag in s['tags']:
            if tag in topic_map:
                topic_key = topic_map[tag][0]
                if s not in topic_sessions[topic_key]:
                    topic_sessions[topic_key].append(s)
                matched = True
        if not matched:
            untagged.append(s)

    # Write topic-index.md
    _write_topic_index(vault, topic_map, topic_sessions, untagged)

    # Write timeline.md
    _write_timeline(vault, topic_map, sessions)


def _write_topic_index(vault, topic_map, topic_sessions, untagged):
    """Write 03-Maps/topic-index.md."""
    maps_dir = os.path.join(vault, '03-Maps')
    os.makedirs(maps_dir, exist_ok=True)

    ti = []
    ti.append('---')
    ti.append('title: "Topic Index / 主题索引"')
    ti.append(f'updated: {datetime.now().strftime("%Y-%m-%d")}')
    ti.append('auto_generated: true')
    ti.append('---')
    ti.append('')
    ti.append('# Topic Index / 主题索引')
    ti.append('')
    ti.append('> Browse by topic, not by date. Auto-rebuilt weekly, never stale.')
    ti.append('> 按主题浏览，不按日期。每周自动重建，永不过时。')
    ti.append('')

    # Get unique topic entries from the map
    unique_topics = {}
    for tag, (topic_name, topic_desc) in topic_map.items():
        if topic_name not in unique_topics:
            unique_topics[topic_name] = topic_desc

    for topic_name, topic_desc in sorted(unique_topics.items()):
        if topic_name not in topic_sessions:
            continue
        sl = topic_sessions[topic_name]
        ti.append(f'## {topic_name}')
        ti.append('')
        ti.append(f'> {topic_desc}')
        ti.append('')
        ti.append('| Project / 项目 | What Happened / 内容 | Decisions/Errors |')
        ti.append('|---------------|---------------------|---------------------------|')
        for s in sorted(sl, key=lambda x: x['date']):
            proj = s['project']
            extras = []
            for d in s['decisions'][:2]:
                text = d.get('text', '') if isinstance(d, dict) else str(d)
                extras.append(f'D: {text[:60]}')
            for e in s['errors'][:1]:
                etype = e.get('type', '') if isinstance(e, dict) else str(e)
                extras.append(f'E: {etype[:40]}')
            extra_str = '; '.join(extras) if extras else '-'
            short = s['title'].split(' / ')[0].strip()[:60]
            ti.append(
                f'| {proj} | '
                f'[[sessions/{s["filename"]}\\|{short}]] | '
                f'{extra_str} ({s["date"]}) |'
            )
        ti.append('')

    if untagged:
        ti.append('## Other / 其他')
        ti.append('')
        ti.append('| Project / 项目 | Title / 标题 | Date / 日期 |')
        ti.append('|---------------|------------|------------|')
        for s in sorted(untagged, key=lambda x: x['date']):
            proj = s['project']
            short = s['title'].split(' / ')[0].strip()[:60]
            ti.append(
                f'| {proj} | '
                f'[[sessions/{s["filename"]}\\|{short}]] | '
                f'{s["date"]} |'
            )

    atomic_write(os.path.join(maps_dir, 'topic-index.md'),
                 '\n'.join(ti) + '\n')


def _write_timeline(vault, topic_map, sessions):
    """Write 03-Maps/timeline.md."""
    import datetime as dt_mod

    maps_dir = os.path.join(vault, '03-Maps')
    os.makedirs(maps_dir, exist_ok=True)

    tl = []
    tl.append('---')
    tl.append('title: "Timeline / 时间线"')
    tl.append(f'updated: {datetime.now().strftime("%Y-%m-%d")}')
    tl.append('auto_generated: true')
    tl.append('---')
    tl.append('')
    tl.append('# Timeline / 时间线')
    tl.append('')
    tl.append('> Grouped by week, each entry tagged with topic. '
              'Auto-rebuilt weekly.')
    tl.append('> 按周排列，每条标注主题。每周自动重建。')
    tl.append('')

    week_sessions = defaultdict(list)
    for s in sessions:
        try:
            d = datetime.fromisoformat(s['date'])
            wk = d.strftime('%Y-W%W')
            end = d + dt_mod.timedelta(days=(6 - d.weekday()))
            label = f'{wk} ({d.strftime("%m/%d")}-{end.strftime("%m/%d")})'
        except Exception:
            wk = 'unknown'
            label = 'Unknown Date / 日期未知'
        week_sessions[wk].append((label, s))

    for wk in sorted(week_sessions.keys(), reverse=True):
        entries = week_sessions[wk]
        label = entries[0][0]
        tl.append(f'## {label}')
        tl.append('')
        tl.append('| Project / 项目 | Title / 标题 | Topics / 主题标签 |')
        tl.append('|---------------|------------|------------------|')
        for _, s in sorted(entries, key=lambda x: x[1]['date']):
            proj = s['project']
            short = s['title'].split(' / ')[0].strip()[:60]
            topics = set()
            for tag in s['tags']:
                if tag in topic_map:
                    topics.add(topic_map[tag][0].split(' / ')[0])
            ts = ' #'.join([''] + sorted(topics)[:3]) if topics else ' -'
            d = s['date']
            ds = d[5:] if len(d) >= 10 else d
            tl.append(
                f'| {proj} | '
                f'[[sessions/{s["filename"]}\\|{short}]] |'
                f'{ts} ({ds}) |'
            )
        tl.append('')

    atomic_write(os.path.join(maps_dir, 'timeline.md'),
                 '\n'.join(tl) + '\n')
