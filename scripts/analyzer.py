"""Step 2: Deep error analysis — keyword screening + LLM root-cause clustering + learning synthesis.

Philosophy: This is not a counter. It's a learner.
- Don't just count errors — find WHY they happen.
- Don't just list patterns — extract the ONE principle that prevents them all.
- Don't pile up rules — check if existing rules already cover this.
"""
import os
import json
import yaml
import time
from datetime import datetime
from config import get_api_config


def run(cfg, dry_run=False, full=False):
    vault = cfg['vault_path']
    sessions_scanned = count_session_files(vault)

    # ── Phase 1: Load taxonomy ──
    try:
        taxonomy = load_taxonomy(vault)
    except Exception as e:
        print(f"    WARNING: Could not load taxonomy ({e}) — using empty taxonomy")
        taxonomy = {"categories": []}

    all_error_types = []
    for cat in taxonomy.get('categories', []):
        if isinstance(cat, dict) and 'subcategories' in cat:
            all_error_types.extend(cat.get('subcategories', []))

    # ── Phase 2: Keyword screening (always runs, no API) ──
    try:
        patterns = keyword_screen(vault, all_error_types, taxonomy)
    except Exception as e:
        print(f"    WARNING: keyword_screen failed ({e}) — no patterns found")
        patterns = []

    # ── Phase 3: Deep root-cause analysis ──
    learnings = []
    if patterns and len(patterns) >= 2:
        api_cfg = get_api_config(cfg)
        if api_cfg.get('key'):
            try:
                # Load existing rules to help the LLM avoid duplicates
                existing_rules = load_existing_rules(vault)
                learnings = llm_deep_analyze(patterns, existing_rules, api_cfg)
                # Enrich patterns with learnings metadata
                patterns = enrich_with_learnings(patterns, learnings)
                print(f"    Deep analysis: {len(learnings)} root cause(s) identified")
            except Exception as e:
                print(f"    LLM deep analysis failed ({e}), using heuristic fallback")
                learnings = heuristic_root_cause_analysis(patterns, taxonomy)
        else:
            print("    LLM analysis skipped: no API key — using heuristic fallback")
            learnings = heuristic_root_cause_analysis(patterns, taxonomy)
    elif patterns:
        learnings = heuristic_root_cause_analysis(patterns, taxonomy)

    # ── Phase 4: Generate summary ──
    summary = synthesize_learnings(learnings, sessions_scanned)

    return {
        "patterns_found": len(patterns),
        "sessions_scanned": sessions_scanned,
        "patterns": patterns,
        "learnings": learnings,
        "summary": summary,
    }


# ── Keyword Screening (fast, no API) ────────────────────────

def count_session_files(vault):
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
    path = os.path.join(vault, '04-Feedback', 'error-taxonomy.md')
    if not os.path.exists(path):
        return {"categories": []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {"categories": []}
    parts = content.split('---')
    if len(parts) < 3:
        return {"categories": []}
    try:
        taxonomy = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {"categories": []}
    if not isinstance(taxonomy, dict) or 'categories' not in taxonomy:
        return {"categories": []}
    return taxonomy


def keyword_screen(vault, error_types, taxonomy):
    """Find error_type occurrences >=2 across sessions."""
    from collections import Counter
    error_counts = Counter()
    error_contexts = {}

    projects_dir = os.path.join(vault, '01-Projects')
    for proj in os.listdir(projects_dir):
        sessions_dir = os.path.join(projects_dir, proj, 'Memory', 'sessions')
        if not os.path.exists(sessions_dir):
            continue
        for filename in os.listdir(sessions_dir):
            if not filename.endswith('.md') or filename.startswith('_'):
                continue
            fp = os.path.join(sessions_dir, filename)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception:
                continue
            fm_parts = content.split('---', 2)
            if len(fm_parts) < 3:
                continue
            try:
                fm = yaml.safe_load(fm_parts[1])
            except yaml.YAMLError:
                continue
            if not isinstance(fm, dict):
                continue
            for err in fm.get('errors_encountered', []):
                if not isinstance(err, dict):
                    continue
                etype = err.get('type', '')
                if not etype:
                    continue
                normalized = etype
                if '_' in etype:
                    type_parts = etype.split('_', 1)
                    if len(type_parts) == 2:
                        cat_names = [c.get('name', '') for c in taxonomy.get('categories', [])
                                    if isinstance(c, dict)]
                        if type_parts[0] in cat_names:
                            normalized = type_parts[1]
                if etype in error_types or normalized in error_types:
                    error_counts[etype] += 1
                    if etype not in error_contexts:
                        error_contexts[etype] = []
                    error_contexts[etype].append({
                        'project': proj,
                        'session': filename.replace('.md', ''),
                        'resolution': err.get('resolution', '')
                    })

    return [
        {
            'error_type': etype,
            'count': count,
            'projects': list(set(c['project'] for c in error_contexts[etype])),
            'contexts': error_contexts[etype]
        }
        for etype, count in error_counts.items()
        if count >= 2
    ]


# ── Heuristic Root-Cause Analysis (fallback when no LLM) ──

# Knowledge base: known root causes → their symptoms and solutions
ROOT_CAUSE_KB = {
    "Windows R 4.5.2 color rendering regression": {
        "symptoms": ["scale_fill_manual_grey", "ragg_greyscale", "ggsave_drop_color",
                     "cairo_pdf_issue", "heatmap_color_distortion"],
        "principle": "R 4.5.2 on Windows has a ggplot2 color rendering bug — always use identity-fill + svglite→rsvg pipeline instead of scale_fill_manual() or ragg::agg_png()",
        "suggested_rule_id": "RULE-FIG-002",
    },
    "GFW network interference": {
        "symptoms": ["ssl_error", "gfw_rst", "timeout", "curl_ssl", "git_hook_fail"],
        "principle": "China GFW injects TCP RST into Git/SSL connections — always check proxy before network I/O, use --ssl-no-revoke for curl, zip-download for GitHub",
        "suggested_rule_id": "RULE-GIT-001",
    },
    "Windows path separator mismatch": {
        "symptoms": ["path_separator_mix", "file_not_found", "permission_denied"],
        "principle": "Windows supports both / and \\ but bash/Python/R handle them differently — always use / in cross-platform scripts",
        "suggested_rule_id": "RULE-WIN-002",
    },
    "R package management on non-standard library path": {
        "symptoms": ["install_fail", "package_not_found", "bioc_version_mismatch",
                    "dependency_conflict"],
        "principle": "R library is at D:/R/library not default — always check before install.packages(), never introduce new deps without updating config",
        "suggested_rule_id": "RULE-R-002",
    },
    "Chinese text encoding in Windows": {
        "symptoms": ["gbk_utf8_mismatch", "chinese_garbled_docx", "chinese_garbled_csv",
                    "path_unicode_error"],
        "principle": "Windows default GBK conflicts with UTF-8 — never use Python for .docx generation, always specify encoding='utf-8' in file operations",
        "suggested_rule_id": "RULE-ZH-001",
    },
    "Rscript -e segfault on Windows": {
        "symptoms": ["segfault_rscript_e"],
        "principle": "Rscript -e crashes on this Windows machine — always write commands to temp .R file and run Rscript temp.R",
        "suggested_rule_id": "RULE-R-001",
    },
    "cBioPortal API parameter quirks": {
        "symptoms": ["http_400_wrong_param"],
        "principle": "cBioPortal API has non-standard parameter requirements — use projection=DETAILED, entrezGeneId=<int> for methylation, always client-side filter geneList results",
        "suggested_rule_id": "RULE-API-001",
    },
}


def heuristic_root_cause_analysis(patterns, taxonomy):
    """Use knowledge base to group errors by root cause without LLM."""
    learnings = []
    seen_errors = set()

    for root_cause, kb in ROOT_CAUSE_KB.items():
        matched_errors = []
        for p in patterns:
            etype = p['error_type']
            # Check if the error type (or its subcategory) matches any symptom
            for symptom in kb['symptoms']:
                if symptom in etype:
                    if etype not in seen_errors:
                        matched_errors.append(p)
                        seen_errors.add(etype)
                    break

        if len(matched_errors) >= 1:
            total_occurrences = sum(p['count'] for p in matched_errors)
            all_projects = list(set(
                proj for p in matched_errors for proj in p['projects']
            ))
            learnings.append({
                "root_cause": root_cause,
                "principle": kb['principle'],
                "affected_errors": [p['error_type'] for p in matched_errors],
                "total_occurrences": total_occurrences,
                "projects_affected": all_projects,
                "impact": "medium" if total_occurrences >= 4 else "low",
                "suggested_rule_id": kb['suggested_rule_id'],
                "action": "reinforce" if rule_exists(kb['suggested_rule_id']) else "new_rule",
            })

    # Any errors not matched by KB → flag as "new territory"
    unmatched = [p for p in patterns if p['error_type'] not in seen_errors]
    if unmatched:
        learnings.append({
            "root_cause": "unmapped_errors",
            "principle": f"{len(unmatched)} error type(s) not yet mapped to known root causes — needs human review",
            "affected_errors": [p['error_type'] for p in unmatched],
            "total_occurrences": sum(p['count'] for p in unmatched),
            "projects_affected": list(set(
                proj for p in unmatched for proj in p['projects']
            )),
            "impact": "unknown",
            "suggested_rule_id": None,
            "action": "review",
        })

    return learnings


def rule_exists(rule_id):
    """Check if a rule already exists in the vault."""
    path = os.path.join("D:/Obsidian/a", '00-Rules', f"{rule_id}.md")
    return os.path.exists(path)


# ── LLM Deep Analysis (high-quality, used when API is available) ──

def load_existing_rules(vault):
    """Load existing rule summaries for the LLM to avoid suggesting duplicates."""
    rules_dir = os.path.join(vault, '00-Rules')
    rules = []
    if not os.path.exists(rules_dir):
        return rules
    for f in sorted(os.listdir(rules_dir)):
        if not f.endswith('.md') or f.startswith('_'):
            continue
        fp = os.path.join(rules_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm = yaml.safe_load(content.split('---')[1])
            rules.append({
                "rule_id": fm.get("rule_id", f.replace(".md", "")),
                "title": fm.get("title", ""),
                "category": fm.get("category", ""),
                "one_liner": fm.get("one_liner", ""),
            })
        except Exception:
            pass
    return rules


def llm_deep_analyze(patterns, existing_rules, api_cfg):
    """Send patterns to LLM for deep root-cause analysis.
    Returns structured learnings with root_cause, principle, and rule suggestions.
    """
    import requests

    prompt = build_deep_analysis_prompt(patterns, existing_rules)
    max_retries = api_cfg.get('max_retries', 3)
    backoff_sec = api_cfg.get('retry_backoff_sec', [2, 4, 8])

    last_error = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{api_cfg['base_url']}/messages",
                headers={
                    "x-api-key": api_cfg['key'],
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": api_cfg['model'],
                    "max_tokens": api_cfg.get('max_tokens', 4000),
                    "temperature": api_cfg.get('temperature', 0.3),
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            # Handle both Anthropic and DeepSeek response formats
            content = ""
            msg_content = result.get('content', [])
            if isinstance(msg_content, list):
                for block in msg_content:
                    if isinstance(block, dict) and 'text' in block:
                        content += block['text']
                    elif isinstance(block, str):
                        content += block
            elif isinstance(msg_content, str):
                content = msg_content
            elif 'choices' in result:  # OpenAI-compatible format
                content = result['choices'][0]['message']['content']

            learnings = json.loads(content)
            return learnings
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = backoff_sec[min(attempt, len(backoff_sec) - 1)]
                time.sleep(wait)
            else:
                raise last_error


def build_deep_analysis_prompt(patterns, existing_rules):
    """Build a comprehensive prompt for deep root-cause analysis.

    This prompt is the product. It determines whether the brain learns or just counts.
    """
    errors_text = "\n".join([
        f"- [{p['error_type']}] {p['count']}× in {p['projects']} — "
        f"resolutions: {[c['resolution'][:100] for c in p['contexts'][:3]]}"
        for p in patterns
    ])

    existing_text = "\n".join([
        f"- {r['rule_id']}: {r['title']} [{r['category']}] — {r.get('one_liner', '')}"
        for r in existing_rules
    ]) if existing_rules else "(no existing rules)"

    return f"""You are an AI error forensics analyst. Your job is NOT to count errors — it's to find the ROOT CAUSE beneath them and extract the ONE PRINCIPLE that prevents them all.

## Errors Found This Scan

{errors_text}

## Existing Rules (do NOT suggest duplicates)

{existing_text}

## Your Task

For each cluster of errors that share the same ROOT CAUSE (not just the same symptom), produce a learning. Follow these rules STRICTLY:

1. **Root cause first**: What is the underlying issue? NOT "they both mention SSL" but "GFW injects TCP RST into TLS handshakes on this machine."

2. **One principle per root cause**: If you couldn't explain it in one sentence to a new developer, it's too vague.

3. **Check existing rules**: If an existing rule already covers this root cause, set action="reinforce" and reference the rule_id. Don't suggest creating a duplicate.

4. **Concrete rule suggestion**: If action is "new_rule" or "merge", provide the ACTUAL rule text that would go into CLAUDE.md. Not "TBD" or "consider adding". The exact words.

5. **Impact estimate**: How much time does this class of error waste? Be honest — not everything is "high impact."

6. **Merge detection**: If ≥2 existing rules cover overlapping ground, suggest merging them into one better rule.

Output JSON array:
```json
[
  {{
    "root_cause": "One-line root cause diagnosis",
    "principle": "ONE sentence that prevents ALL errors in this cluster",
    "affected_errors": ["error_type1", "error_type2"],
    "total_occurrences": N,
    "projects_affected": ["proj1", "proj2"],
    "impact": "high|medium|low",
    "impact_rationale": "why this impact level",
    "suggested_rule_id": "RULE-XXX-NNN",
    "suggested_rule_title": "Title for the rule",
    "suggested_rule_text": "The exact rule text that would go into CLAUDE.md. Be SPECIFIC. Include what to DO, not just what to AVOID.",
    "existing_rule_coverage": "none|partial|full",
    "related_existing_rules": ["RULE-XXX-NNN"],
    "action": "new_rule|reinforce|merge|monitor|review",
    "merge_suggestion": null or "RULE-A and RULE-B should merge into one rule because..."
  }}
]
```

## Quality Gates (self-check before output)

- [ ] Every root_cause is DIFFERENT from every other root_cause (no duplicates)
- [ ] Every principle passes the "one-sentence test" (explainable to a new dev in 1 sentence)
- [ ] Every suggested_rule_text is a CONCRETE instruction, not a vague direction
- [ ] No suggested rule duplicates an existing rule
- [ ] Impact levels are honest — not everything is "high"
- [ ] Merges are suggested where appropriate (don't pile up similar rules)

Output ONLY the JSON array. No preamble, no explanations outside the JSON."""


def enrich_with_learnings(patterns, learnings):
    """Attach learning metadata to each pattern."""
    error_to_learning = {}
    for l in learnings:
        for etype in l.get('affected_errors', []):
            error_to_learning[etype] = {
                'root_cause': l.get('root_cause', ''),
                'principle': l.get('principle', ''),
                'suggested_rule_id': l.get('suggested_rule_id', ''),
                'action': l.get('action', ''),
            }

    for p in patterns:
        meta = error_to_learning.get(p['error_type'], {})
        p['root_cause'] = meta.get('root_cause', '')
        p['principle'] = meta.get('principle', '')
        p['suggested_rule_id'] = meta.get('suggested_rule_id', '')
        p['action'] = meta.get('action', '')

    return patterns


def synthesize_learnings(learnings, sessions_scanned):
    """Generate a one-paragraph human-readable summary of what was learned."""
    if not learnings:
        return f"Scanned {sessions_scanned} sessions. No error patterns detected — system is stable."

    high_impact = [l for l in learnings if l.get('impact') == 'high']
    new_rules = [l for l in learnings if l.get('action') == 'new_rule']
    reinforces = [l for l in learnings if l.get('action') == 'reinforce']
    merges = [l for l in learnings if l.get('action') == 'merge']
    reviews = [l for l in learnings if l.get('action') == 'review']

    parts = []

    # Lead with the most important finding
    if high_impact:
        l = high_impact[0]
        parts.append(
            f"[CRITICAL] {l['root_cause']}. "
            f"This root cause led to {l['total_occurrences']} errors "
            f"across {len(l['projects_affected'])} project(s). "
            f"Principle: {l['principle']}"
        )

    # What's new
    if new_rules:
        parts.append(
            f"[NEW RULES] {len(new_rules)} proposed: "
            + "; ".join(l['suggested_rule_id'] for l in new_rules)
        )

    # What's confirmed
    if reinforces:
        parts.append(
            f"[CONFIRMED] {len(reinforces)} existing rules validated: "
            + "; ".join(l['suggested_rule_id'] for l in reinforces)
        )

    # What needs merging
    if merges:
        for l in merges:
            parts.append(f"[MERGE] {l.get('merge_suggestion', '')}")

    # Unknown territory
    if reviews:
        parts.append(
            f"[REVIEW] {len(reviews)} new patterns need human review: "
            + "; ".join(
                ', '.join(l['affected_errors'][:2]) for l in reviews
            )
        )

    if not parts:
        parts.append(
            f"扫描了 {sessions_scanned} 个 session。"
            f"所有检测到的错误已有规则覆盖，系统在稳定运行。"
        )

    return "\n\n".join(parts)
