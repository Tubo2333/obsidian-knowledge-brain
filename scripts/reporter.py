"""Step 4: Generate weekly report, update metrics, rebuild index, update heartbeat."""
import os
import yaml
import json
import tempfile
from datetime import datetime

def run(cfg, dry_run=False, step_results=None, missed_weeks=0):
    vault = cfg['vault_path']
    week = datetime.now().strftime('%Y-W%W')

    report_path = os.path.join(vault, '04-Feedback', 'weekly-reports', f'{week}.md')

    # Gather data from previous steps
    backup = step_results.get('backup', {}) if step_results else {}
    analyze = step_results.get('analyze', {}) if step_results else {}
    maintain = step_results.get('maintain', {}) if step_results else {}

    patterns = analyze.get('patterns', [])
    learnings = analyze.get('learnings', [])
    summary_text = analyze.get('summary', '')
    cards = maintain.get('cards_generated', 0)
    merges = maintain.get('merges_suggested', 0)
    archived = maintain.get('rules_archived', 0)

    # Build session count
    sessions_scanned = analyze.get('sessions_scanned', 0)
    sessions_total = count_session_files(vault)
    processed_sessions = backup.get('processed_ids', {})

    # ── Compute real metrics ──
    repeat_rate = compute_repeat_error_rate(vault, analyze)
    rule_hits = compute_rule_hit_rates(vault, analyze)
    inbox_count = count_pending_inbox(vault)

    # Generate report content
    rule_hit_rows = "\n".join([
        f"| {cat} | {rate:.1%} | - | - |"
        for cat, rate in sorted(rule_hits.items())
    ]) if rule_hits else "| — | — | - | - |"

    # Learning cards summary
    learning_cards = ""
    for l in learnings:
        action_label = {"new_rule": "[NEW]", "reinforce": "[OK]", "merge": "[MERGE]",
                       "review": "[REVIEW]", "monitor": "[WATCH]"}
        label = action_label.get(l.get('action', ''), '[NEW]')
        learning_cards += f"""
### {label} {l.get('root_cause', 'Unknown')}

**原则**: {l.get('principle', '')}

| 维度 | 值 |
|------|-----|
| 影响 | {l.get('impact', 'unknown')} |
| 出现次数 | {l.get('total_occurrences', 0)} |
| 涉及项目 | {', '.join(l.get('projects_affected', []))} |
| 建议规则 | {l.get('suggested_rule_id', 'N/A')} |
| 动作 | {l.get('action', 'review')} |

"""

    patterns_text = "\n".join([
        f"- **{p.get('error_type', 'unknown')}**: {p.get('count', 0)} occurrences in {p.get('projects', [])}"
        for p in patterns
    ]) if patterns else 'No new patterns this week.'

    report_content = f"""---
week: "{week}"
date: {datetime.now().strftime('%Y-%m-%d')}
scan_status: ok
sessions_scanned: {sessions_scanned}
sessions_total: {sessions_total}
new_patterns_detected: {len(patterns)}
new_rules_proposed: {cards}
merges_suggested: {merges}
rules_awaiting_approval: {inbox_count}
rules_archived_this_week: {archived}
missed_weeks: {missed_weeks}
repeat_error_rate: {repeat_rate:.3f}
heartbeat_ok: true
---

# Weekly Report {week}

## 💡 这周学到了什么 / What We Learned

{summary_text if summary_text else '_扫描了 ' + str(sessions_scanned) + ' 个 session，未发现新模式。系统稳定。_'}

## 📊 Metric Snapshot

| Metric | This Week | Trend |
|--------|-----------|-------|
| Repeat Error Rate | {repeat_rate:.1%} | {'⚠️ High' if repeat_rate > 0.5 else '✅ OK'} |
| Inbox Backlog | {inbox_count} | {'⚠️ Needs review' if inbox_count > 10 else '✅ OK'} |
| New Rules Proposed | {cards} | — |
| Merges Suggested | {merges} | — |

## 📈 Rule Hit Rates by Category

| Category | Hit Rate |
|----------|----------|
{rule_hit_rows}

## 🔍 根因分析详情 / Root Cause Details
{learning_cards if learning_cards else '_No deep analysis results this scan._'}

## 📌 Pending Approvals

{inbox_count} rule(s) in inbox.

## ⚠️ Alerts

{generate_alerts(repeat_rate, inbox_count, sessions_scanned, missed_weeks)}
"""

    if not dry_run:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        # Atomic write: .tmp -> rename
        atomic_write(report_path, report_content)

        # Update growth-metrics.md with real data
        update_growth_metrics(vault, repeat_rate, rule_hits, inbox_count)

        # Rebuild search index
        rebuild_search_index(vault)

        # Auto-rebuild maps (topic-index + timeline) so they never go stale
        rebuild_maps(vault)

        # Update heartbeat with processed_sessions for incremental scan
        update_heartbeat(vault, sessions_scanned, processed_sessions)
    else:
        # Dry-run: still validate paths, don't write
        pass

    return {
        "report": report_path,
        "week": week,
        "patterns_reported": len(patterns),
        "repeat_error_rate": repeat_rate,
        "index_rebuilt": not dry_run
    }


# ── Metric Computation ─────────────────────────────────────────
def compute_repeat_error_rate(vault, analyze):
    """Compute what fraction of errors this scan have been seen before."""
    patterns = analyze.get('patterns', []) if analyze else []
    if not patterns:
        return 0.0

    # A pattern with count >= 2 is a repeat (seen in >=2 sessions)
    repeat_count = sum(1 for p in patterns if p.get('count', 0) >= 2)
    return repeat_count / len(patterns) if patterns else 0.0


def compute_rule_hit_rates(vault, analyze):
    """Compute per-category rule hit rates from session summaries.
    Hit rate = sessions where rules of this category were relevant / total sessions.
    For now, approximate from error type categories found in patterns."""
    patterns = analyze.get('patterns', []) if analyze else []
    if not patterns:
        return {}

    # Load taxonomy to map error types to categories
    taxonomy_path = os.path.join(vault, '04-Feedback', 'error-taxonomy.md')
    cat_map = {}
    try:
        import yaml
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            content = f.read()
        taxonomy = yaml.safe_load(content.split('---')[1])
        for cat in taxonomy.get('categories', []):
            cat_name = cat.get('name', 'unknown')
            for sub in cat.get('subcategories', []):
                cat_map[sub] = cat_name
    except Exception:
        pass

    # Count patterns per category
    cat_counts = {}
    for p in patterns:
        etype = p.get('error_type', '')
        cat = cat_map.get(etype, 'other')
        cat_counts[cat] = cat_counts.get(cat, 0) + p.get('count', 1)

    # Total sessions scanned
    total = analyze.get('sessions_scanned', 1) or 1
    return {cat: min(1.0, count / total) for cat, count in cat_counts.items()}


def update_growth_metrics(vault, repeat_rate, rule_hits, inbox_count):
    """Write computed metrics to growth-metrics.md."""
    gm_path = os.path.join(vault, '04-Feedback', 'growth-metrics.md')
    today = datetime.now()

    # Build updated metrics
    # Count active rules by age bracket
    rules_dir = os.path.join(vault, '00-Rules')
    age_brackets = {'0-30': 0, '30-60': 0, '60-90': 0, '90+': 0}
    if os.path.exists(rules_dir):
        for f in os.listdir(rules_dir):
            if not f.endswith('.md') or f.startswith('_'):
                continue
            fp = os.path.join(rules_dir, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                age_days = (today - mtime).days
                if age_days < 30:
                    age_brackets['0-30'] += 1
                elif age_days < 60:
                    age_brackets['30-60'] += 1
                elif age_days < 90:
                    age_brackets['60-90'] += 1
                else:
                    age_brackets['90+'] += 1
            except Exception:
                pass

    week_str = today.strftime('%Y-W%W')
    hit_rates_str = "\n".join([
        f"      Rule Hit Rate ({cat}): {rate:.1%}"
        for cat, rate in sorted(rule_hits.items())
    ]) if rule_hits else "      Rule Hit Rate: —"

    content = f"""---
version: "1.0"
baseline_start: 2026-06-12
baseline_end: 2026-07-10
weeks:
  - week: "{week_str}"
    repeat_error_rate: {repeat_rate:.3f}
    rule_hit_rates: {json.dumps(rule_hits)}
    inbox_backlog: {inbox_count}
    notes: "Auto-generated by scanner — real metrics"
---

# Growth Metrics

## Core Metrics (weekly)

| Week | Repeat Error Rate | {chr(10).join(['Rule Hit Rate (' + cat + ')' for cat in sorted(rule_hits.keys())]) if rule_hits else 'Rule Hit Rate'} | Inbox Backlog |
|------|-------------------|{'|'.join(['---' for _ in rule_hits]) if rule_hits else '---'}|---|
| {week_str} | {repeat_rate:.1%} | {' | '.join([f'{rate:.1%}' for rate in sorted(rule_hits.values())]) if rule_hits else '—'} | {inbox_count} |

## Reference Metrics

| Metric | Value |
|--------|-------|
| Rule Interception Count | 0 |
| Knowledge Metabolism (archived+expired/total) | 0/{age_brackets['0-30'] + age_brackets['30-60'] + age_brackets['60-90'] + age_brackets['90+']} |
| Active Rules (0-30 days) | {age_brackets['0-30']} |
| Active Rules (30-60 days) | {age_brackets['30-60']} |
| Active Rules (60-90 days) | {age_brackets['60-90']} |
| Active Rules (90+ days) | {age_brackets['90+']} |

## Baseline Period

First 4 weeks: metrics collected but alerts suppressed.
Week 5+: alerts based on deviation from baseline average.

Baseline started: **2026-06-12**. Alerts suppressed until Week 5 (2026-07-10).
"""

    try:
        atomic_write(gm_path, content)
    except Exception as e:
        print(f"    WARNING: Cannot update growth-metrics: {e}")


def generate_alerts(repeat_rate, inbox_count, sessions_scanned, missed_weeks):
    """Generate alert messages based on metrics."""
    alerts = []
    if repeat_rate > 0.5:
        alerts.append(f"⚠️ **High repeat error rate ({repeat_rate:.0%})** — same errors keep happening. Consider promoting related patterns to rules.")
    if inbox_count > 10:
        alerts.append(f"⚠️ **Inbox backlog ({inbox_count} pending)** — rules need review.")
    if inbox_count > 20:
        alerts.append(f"🚨 **Large inbox backlog ({inbox_count})** — knowledge is rotting in review queue.")
    if sessions_scanned == 0:
        alerts.append("⚠️ **No sessions scanned** — scanner may not be reaching transcripts.")
    if missed_weeks > 0:
        alerts.append(f"⚠️ **{missed_weeks} week(s) missed** — scanner was not running. Data may be stale.")
    if not alerts:
        alerts.append("✅ No alerts this week.")
    return '\n'.join(alerts)


def generate_highlight(patterns, cards, archived, sessions_scanned):
    """Generate a human-readable highlight summary."""
    parts = []
    if patterns:
        parts.append(f"{len(patterns)} error pattern(s) detected across {sessions_scanned} sessions")
    if cards:
        parts.append(f"{cards} approval card(s) generated for cross-project patterns")
    if archived:
        parts.append(f"{archived} stale rule(s) archived")
    if not parts:
        parts.append(f"Scanner processed {sessions_scanned} sessions. No new patterns detected — system is stable.")
    return '; '.join(parts)

def atomic_write(filepath, content):
    """Write content to file atomically: write to .tmp then os.rename."""
    tmp_path = filepath + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp_path, filepath)  # os.replace is atomic on Windows

def count_session_files(vault):
    """Count total session summary .md files across all projects."""
    count = 0
    projects_dir = os.path.join(vault, '01-Projects')
    if not os.path.exists(projects_dir):
        return 0
    for proj in os.listdir(projects_dir):
        sessions_dir = os.path.join(projects_dir, proj, 'Memory', 'sessions')
        if os.path.exists(sessions_dir):
            count += len([f for f in os.listdir(sessions_dir) if f.endswith('.md') and not f.startswith('_')])
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
    import re
    keywords = {}

    # Scan session summaries
    projects_dir = os.path.join(vault, '01-Projects')
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
            # Extract keywords from tags, decisions, errors
            for tag in fm.get('tags', []):
                kw = tag.lower()
                if kw not in keywords:
                    keywords[kw] = {'sessions': [], 'rules': [], 'decisions': []}
                if session_id not in keywords[kw]['sessions']:
                    keywords[kw]['sessions'].append(session_id)

    # Write index atomically
    index_path = os.path.join(vault, '03-Maps', 'search-index.md')
    index_content = f"---\nlast_rebuilt: {datetime.now().strftime('%Y-%m-%d')}\nkeywords:\n"
    for kw, data in sorted(keywords.items()):
        index_content += f"  - keyword: \"{kw}\"\n"
        index_content += f"    sessions: {data['sessions']}\n"
        index_content += f"    rules: {data['rules']}\n"
        index_content += f"    decisions: {data['decisions']}\n"
    index_content += "---\n\n# Search Index\n\n"
    index_content += "| Keyword | Sessions | Rules | Decisions |\n"
    index_content += "|---------|----------|-------|----------|\n"
    for kw, data in sorted(keywords.items()):
        index_content += f"| {kw} | {len(data['sessions'])} | {len(data['rules'])} | {len(data['decisions'])} |\n"

    atomic_write(index_path, index_content)

def update_heartbeat(vault, sessions_processed, processed_sessions=None):
    """Update heartbeat.md after successful scan.
    Includes processed_sessions dict for incremental scanning."""
    hb_path = os.path.join(vault, '04-Feedback', 'heartbeat.md')
    now = datetime.now().isoformat()

    if processed_sessions is None:
        processed_sessions = {}

    # Build processed_sessions YAML
    ps_yaml = yaml.dump(processed_sessions, allow_unicode=True, default_flow_style=False)
    # Indent for nested YAML
    ps_indented = '\n'.join('  ' + line for line in ps_yaml.strip().split('\n'))

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

    # Atomic write
    atomic_write(hb_path, content)

def rebuild_maps(vault):
    """Auto-rebuild 03-Maps/: topic-index + timeline.
    Called weekly so they never go stale.
    自动重建地图：主题索引+时间线。每周调用，永不过时。"""
    import re
    from collections import defaultdict

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
            title = title_match.group(1).strip() if title_match else fm.get('ai_title', 'Untitled')

            # Normalize date: YAML safe_load may parse "2026-06-14" as datetime.date
            date_val = fm.get('date', 'unknown')
            if hasattr(date_val, 'isoformat'):
                date_val = date_val.isoformat()

            sessions.append({
                'date': date_val,
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

    TOPIC_MAP = {
        'identity-fill': ('identity-fill / 身份填充方案', 'R scale_fill_manual greyscale bug lifecycle'),
        '身份填充': ('identity-fill / 身份填充方案', 'R scale_fill_manual greyscale bug lifecycle'),
        'R-bug': ('R 生态系统 / R Ecosystem', 'R package, version, segfault issues'),
        'R缺陷': ('R 生态系统 / R Ecosystem', 'R package, version, segfault issues'),
        'segfault': ('R 生态系统 / R Ecosystem', 'R package, version, segfault issues'),
        'GFW': ('GFW 网络穿透 / GFW Network Bypass', 'TCP RST, GitHub block, SSL workarounds'),
        'gfw': ('GFW 网络穿透 / GFW Network Bypass', 'TCP RST, GitHub block, SSL workarounds'),
        'github': ('GFW 网络穿透 / GFW Network Bypass', 'TCP RST, GitHub block, SSL workarounds'),
        'curl': ('GFW 网络穿透 / GFW Network Bypass', 'TCP RST, GitHub block, SSL workarounds'),
        'ssl': ('GFW 网络穿透 / GFW Network Bypass', 'TCP RST, GitHub block, SSL workarounds'),
        '网络': ('GFW 网络穿透 / GFW Network Bypass', 'TCP RST, GitHub block, SSL workarounds'),
        'zotero': ('Zotero 引用管理 / Zotero Citation', 'CLI, PubMed bridge, auto-cite skill'),
        'Zotero': ('Zotero 引用管理 / Zotero Citation', 'CLI, PubMed bridge, auto-cite skill'),
        'citation': ('Zotero 引用管理 / Zotero Citation', 'CLI, PubMed bridge, auto-cite skill'),
        '引用': ('Zotero 引用管理 / Zotero Citation', 'CLI, PubMed bridge, auto-cite skill'),
        '文献': ('Zotero 引用管理 / Zotero Citation', 'CLI, PubMed bridge, auto-cite skill'),
        'DOCX': ('DOCX 中文编码 / DOCX Chinese Encoding', 'Python GBK/UTF-8 -> Node.js docx-js'),
        'docx': ('DOCX 中文编码 / DOCX Chinese Encoding', 'Python GBK/UTF-8 -> Node.js docx-js'),
        '编码': ('DOCX 中文编码 / DOCX Chinese Encoding', 'Python GBK/UTF-8 -> Node.js docx-js'),
        'encoding': ('DOCX 中文编码 / DOCX Chinese Encoding', 'Python GBK/UTF-8 -> Node.js docx-js'),
        'cBioPortal': ('cBioPortal API / cBioPortal 接口', 'projection=DETAILED, entrezGeneId, client-side filter'),
        'GDC': ('cBioPortal API / cBioPortal 接口', 'projection=DETAILED, entrezGeneId, client-side filter'),
        'API': ('cBioPortal API / cBioPortal 接口', 'projection=DETAILED, entrezGeneId, client-side filter'),
        'CSTB': ('CSTB 论文 / CSTB Thesis', 'Module expansion, 20 cancers, 120 refs'),
        'cstb': ('CSTB 论文 / CSTB Thesis', 'Module expansion, 20 cancers, 120 refs'),
        '论文': ('CSTB 论文 / CSTB Thesis', 'Module expansion, 20 cancers, 120 refs'),
        'thesis': ('CSTB 论文 / CSTB Thesis', 'Module expansion, 20 cancers, 120 refs'),
        'AI-VAST': ('AI-VAST 视觉系统 / AI-VAST Vision', 'Bosch, 8 immutable decisions, dual dataset'),
        'VAST': ('AI-VAST 视觉系统 / AI-VAST Vision', 'Bosch, 8 immutable decisions, dual dataset'),
        '视觉': ('AI-VAST 视觉系统 / AI-VAST Vision', 'Bosch, 8 immutable decisions, dual dataset'),
        'ITIP': ('ITIP 管线 / ITIP Pipeline', 'Phase A-E, ComBat->limma, GDSC2, patent'),
        'itip': ('ITIP 管线 / ITIP Pipeline', 'Phase A-E, ComBat->limma, GDSC2, patent'),
        'NSCLC': ('ITIP 管线 / ITIP Pipeline', 'Phase A-E, ComBat->limma, GDSC2, patent'),
        'patent': ('专利工作流 / Patent Workflow', 'paper2patent, disclosure, claims'),
        '专利': ('专利工作流 / Patent Workflow', 'paper2patent, disclosure, claims'),
        'skill': ('技能与基础设施 / Skills & Infra', 'Skill install, pipeline, CLAUDE.md maintenance'),
        'superpowers': ('技能与基础设施 / Skills & Infra', 'Skill install, pipeline, CLAUDE.md maintenance'),
        'infra': ('技能与基础设施 / Skills & Infra', 'Skill install, pipeline, CLAUDE.md maintenance'),
        'neat-freak': ('技能与基础设施 / Skills & Infra', 'Skill install, pipeline, CLAUDE.md maintenance'),
        'spatial': ('空间组学 / Spatial Transcriptomics', 'Visium HD, Xenium, cross-platform'),
        '空间': ('空间组学 / Spatial Transcriptomics', 'Visium HD, Xenium, cross-platform'),
        'resume': ('简历与职业 / Resume & Career', 'RenderCV, YAML rendering, job requirements'),
        'CV': ('简历与职业 / Resume & Career', 'RenderCV, YAML rendering, job requirements'),
        'Obsidian': ('Scanner 系统 / Scanner System', 'Obsidian Brain construction and maintenance'),
        'obsidian': ('Scanner 系统 / Scanner System', 'Obsidian Brain construction and maintenance'),
        'scanner': ('Scanner 系统 / Scanner System', 'Obsidian Brain construction and maintenance'),
        '扫描': ('Scanner 系统 / Scanner System', 'Obsidian Brain construction and maintenance'),
        'figure': ('图表渲染 / Figure Rendering', 'Nature/journal figures, color pipelines'),
        '图表': ('图表渲染 / Figure Rendering', 'Nature/journal figures, color pipelines'),
        'render': ('图表渲染 / Figure Rendering', 'Nature/journal figures, color pipelines'),
    }

    topic_sessions = defaultdict(list)
    untagged = []
    for s in sessions:
        matched = False
        for tag in s['tags']:
            if tag in TOPIC_MAP:
                topic_key = TOPIC_MAP[tag][0]
                if s not in topic_sessions[topic_key]:
                    topic_sessions[topic_key].append(s)
                matched = True
        if not matched:
            untagged.append(s)

    # Write topic-index.md
    ti = []
    ti.append('---')
    ti.append('title: "主题索引 / Topic Index"')
    ti.append(f'updated: {datetime.now().strftime("%Y-%m-%d")}')
    ti.append('auto_generated: true')
    ti.append('---')
    ti.append('')
    ti.append('# 主题索引 / Topic Index')
    ti.append('')
    ti.append('> 按主题浏览，不按日期。每周自动重建，永不过时。')
    ti.append('> Browse by topic, not by date. Auto-rebuilt weekly, never stale.')
    ti.append('')

    for topic_name, topic_desc in sorted(set(TOPIC_MAP.values())):
        if topic_name not in topic_sessions:
            continue
        sl = topic_sessions[topic_name]
        ti.append(f'## {topic_name}')
        ti.append('')
        ti.append(f'> {topic_desc}')
        ti.append('')
        ti.append('| 项目 / Project | 内容 / What Happened | 决策/错误 / Decisions/Errors |')
        ti.append('|---------------|---------------------|---------------------------|')
        for s in sorted(sl, key=lambda x: x['date']):
            proj = s['project'].replace('-pan-cancer','').replace('-toolchain','')
            extras = []
            for d in s['decisions'][:2]:
                text = d.get('text','') if isinstance(d,dict) else str(d)
                extras.append(f'D: {text[:60]}')
            for e in s['errors'][:1]:
                etype = e.get('type','') if isinstance(e,dict) else str(e)
                extras.append(f'E: {etype[:40]}')
            extra_str = '; '.join(extras) if extras else '-'
            short = s['title'].split(' / ')[0].strip()[:60]
            ti.append(f'| {proj} | [[sessions/{s["filename"]}\\|{short}]] | {extra_str} ({s["date"]}) |')
        ti.append('')

    if untagged:
        ti.append('## 其他 / Other')
        ti.append('')
        ti.append('| 项目 / Project | 标题 / Title | 日期 / Date |')
        ti.append('|---------------|------------|------------|')
        for s in sorted(untagged, key=lambda x: x['date']):
            proj = s['project'].replace('-pan-cancer','').replace('-toolchain','')
            short = s['title'].split(' / ')[0].strip()[:60]
            ti.append(f'| {proj} | [[sessions/{s["filename"]}\\|{short}]] | {s["date"]} |')

    atomic_write(os.path.join(vault, '03-Maps', 'topic-index.md'), '\n'.join(ti) + '\n')

    # Write timeline.md
    tl = []
    tl.append('---')
    tl.append('title: "时间线 / Timeline"')
    tl.append(f'updated: {datetime.now().strftime("%Y-%m-%d")}')
    tl.append('auto_generated: true')
    tl.append('---')
    tl.append('')
    tl.append('# 时间线 / Timeline')
    tl.append('')
    tl.append('> 按周排列，每条标注主题。每周自动重建。')
    tl.append('> Grouped by week, each entry tagged with topic. Auto-rebuilt weekly.')
    tl.append('')

    week_sessions = defaultdict(list)
    for s in sessions:
        try:
            d = datetime.fromisoformat(s['date'])
            wk = d.strftime('%Y-W%W')
            end = d + __import__('datetime').timedelta(days=(6-d.weekday()))
            label = f'{wk} ({d.strftime("%m/%d")}-{end.strftime("%m/%d")})'
        except:
            wk = 'unknown'
            label = '日期未知 / Unknown'
        week_sessions[wk].append((label, s))

    for wk in sorted(week_sessions.keys(), reverse=True):
        entries = week_sessions[wk]
        label = entries[0][0]
        tl.append(f'## {label}')
        tl.append('')
        tl.append('| 项目 / Project | 标题 / Title | 主题标签 / Topics |')
        tl.append('|---------------|------------|------------------|')
        for _, s in sorted(entries, key=lambda x: x[1]['date']):
            proj = s['project'].replace('-pan-cancer','').replace('-toolchain','')
            short = s['title'].split(' / ')[0].strip()[:60]
            topics = set()
            for tag in s['tags']:
                if tag in TOPIC_MAP:
                    topics.add(TOPIC_MAP[tag][0].split(' / ')[0])
            ts = ' #'.join([''] + sorted(topics)[:3]) if topics else ' -'
            d = s['date']
            if isinstance(d, str) and len(d) >= 10:
                ds = d[5:]  # "2026-06-11" -> "06-11"
            else:
                ds = str(d)
            tl.append(f'| {proj} | [[sessions/{s["filename"]}\\|{short}]] |{ts} ({ds}) |')
        tl.append('')

    atomic_write(os.path.join(vault, '03-Maps', 'timeline.md'), '\n'.join(tl) + '\n')

