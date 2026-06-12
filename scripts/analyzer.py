"""Step 2: Pattern detection — keyword screening + LLM semantic clustering.

Two-tier approach:
  Tier 1: Keyword exact match on error_type from error-taxonomy.md
  Tier 2: LLM semantic clustering on detected patterns (optional, needs API key)
"""

import os
import json
import yaml
import time
from config import get_api_config


def run(cfg, dry_run=False, full=False):
    vault = cfg['vault_path']
    sessions_scanned = count_session_files(vault)

    # Tier 1: Keyword exact match on error_type
    taxonomy = load_taxonomy(vault)
    all_error_types = []
    for cat in taxonomy.get('categories', []):
        all_error_types.extend(cat.get('subcategories', []))

    # Scan session summaries for error patterns
    patterns = keyword_screen(vault, all_error_types, taxonomy)

    # Tier 2: LLM semantic clustering on candidates
    # (enriches patterns, doesn't replace keyword results)
    clusters = []
    if patterns and len(patterns) >= 2:
        try:
            api_cfg = get_api_config(cfg)
            if api_cfg.get('key'):
                clusters = llm_cluster(patterns, api_cfg)
                # Enrich patterns with cluster metadata
                patterns = enrich_patterns_with_clusters(patterns, clusters)
            else:
                print("    LLM clustering skipped: no API key configured / "
                      "未配置 API key，跳过 LLM 聚类")
        except Exception as e:
            print(f"    LLM clustering unavailable, using keyword-only mode: "
                  f"{e}")

    return {
        "patterns_found": len(patterns),
        "sessions_scanned": sessions_scanned,
        "patterns": patterns,
        "clusters": clusters
    }


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


def load_taxonomy(vault):
    """Load error taxonomy from vault."""
    path = os.path.join(vault, '04-Feedback', 'error-taxonomy.md')
    if not os.path.exists(path):
        return {'categories': []}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    parts = content.split('---', 2)
    if len(parts) < 2:
        return {'categories': []}
    return yaml.safe_load(parts[1])


def keyword_screen(vault, error_types, taxonomy):
    """Find error_type occurrences >=2 across sessions.

    Returns list of {error_type, count, projects, contexts} dicts.
    """
    from collections import Counter
    error_counts = Counter()
    error_contexts = {}

    # Build category name set for prefix stripping
    category_names = set(c['name'] for c in taxonomy.get('categories', []))

    projects_dir = os.path.join(vault, '01-Projects')
    if not os.path.exists(projects_dir):
        return []

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
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                continue
            for err in fm.get('errors_encountered', []):
                etype = err.get('type', '')
                # Normalize: strip category prefix if present
                # e.g., "env_encoding_mismatch" -> "encoding_mismatch"
                normalized = etype
                if '_' in etype:
                    prefix_parts = etype.split('_', 1)
                    if (len(prefix_parts) == 2 and
                            prefix_parts[0] in category_names):
                        normalized = prefix_parts[1]
                if etype in error_types or normalized in error_types:
                    error_counts[etype] += 1
                    if etype not in error_contexts:
                        error_contexts[etype] = []
                    error_contexts[etype].append({
                        'project': proj,
                        'session': f.replace('.md', ''),
                        'resolution': err.get('resolution', '')
                    })

    # Filter: >=2 occurrences
    return [
        {
            'error_type': etype,
            'count': count,
            'projects': list(set(c['project']
                                 for c in error_contexts[etype])),
            'contexts': error_contexts[etype]
        }
        for etype, count in error_counts.items()
        if count >= 2
    ]


def enrich_patterns_with_clusters(patterns, clusters):
    """Add cluster_id and cluster_confidence to each pattern.

    Preserves the original pattern format (error_type, count, projects,
    contexts).
    """
    for p in patterns:
        p['cluster_id'] = None
        p['cluster_confidence'] = 0.0
        for cl in clusters:
            if p['error_type'] in cl.get('items', []):
                p['cluster_id'] = cl.get('cluster_id', '')
                p['cluster_confidence'] = cl.get('confidence', 0.0)
                break
    return patterns


def llm_cluster(patterns, api_cfg):
    """Group similar error patterns using LLM semantic clustering.

    Returns list of {cluster_id, description, root_cause, items, confidence}
    dicts. Uses configurable API endpoint, model, and retry with exponential
    backoff.
    """
    import requests

    prompt = build_clustering_prompt(patterns)
    max_retries = api_cfg.get('max_retries', 3)
    backoff_sec = api_cfg.get('retry_backoff_sec', [2, 4, 8])

    last_error = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{api_cfg['base_url']}/messages",
                headers={
                    "x-api-key": api_cfg['key'],
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": api_cfg['model'],
                    "max_tokens": api_cfg['max_tokens'],
                    "temperature": api_cfg['temperature'],
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30
            )
            resp.raise_for_status()
            result = resp.json()
            content = result['content'][0]['text']
            clusters = json.loads(content)
            return clusters
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = backoff_sec[min(attempt, len(backoff_sec) - 1)]
                time.sleep(wait)
            else:
                raise last_error


def build_clustering_prompt(patterns):
    """Build a prompt for LLM-based error pattern clustering."""
    errors_text = "\n".join([
        f"- [{p['error_type']}] count={p['count']} "
        f"projects={p['projects']} "
        f"resolutions={[c['resolution'] for c in p['contexts']]}"
        for p in patterns
    ])
    return (
        "You are an error pattern analyst. Given a list of errors from AI "
        "coding sessions, group them into clusters where errors have the "
        "same ROOT CAUSE (not the same symptom).\n\n"
        f"Errors:\n{errors_text}\n\n"
        "Output JSON array: "
        "[{\"cluster_id\": \"CL-001\", \"description\": \"...\", "
        "\"root_cause\": \"...\", \"items\": [\"error_type1\", \"error_type2\"], "
        "\"confidence\": 0.X}]\n\n"
        "Few-shot examples:\n"
        "1. \"render_color_greyscale\" + \"render_font_missing\" -> "
        "SAME cluster (root: rendering engine version regression)\n"
        "2. \"file_not_found (lang_r)\" + \"file_not_found (lang_py)\" -> "
        "DIFFERENT clusters (different path resolution mechanisms)\n"
        "3. \"api_data_missing (project A)\" + \"api_data_missing (project B)\" "
        "-> SAME cluster but note: data limitation, not code error"
    )
