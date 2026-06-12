#!/usr/bin/env python3
"""3D scoring: decision density x error density x project coverage.

Scores all JSONL sessions to identify the highest-value sessions for
curated history selection. The "3D score" combines:

  - decision_density (40%): Formal [DECISION] annotations + heuristic keyword
  - error_density (40%): Formal [ERROR] annotations + heuristic keyword
  - project_coverage (20%): Number of known projects the session touches

Project detection patterns can be customized via PROJECT_PATTERNS dict below
or by passing --patterns-file pointing to a YAML file.

Usage:
  python score_sessions.py <jsonl_source_dir> [--output results.json]
                            [--top N] [--patterns-file patterns.yaml]
"""

import os
import json
import sys
import re

# ── Configurable project detection patterns ──
# Map project-name -> list of regex patterns to match in session text.
# Customize this for your projects, or load from a YAML file with --patterns-file.
PROJECT_PATTERNS = {
    # Example entries — replace with your own projects
    # 'my-research': [r'my-research', r'MYPROJ', r'my_project'],
    # 'side-project': [r'side.project', r'SIDEPROJ'],
}


# ── Decision and error keyword patterns ──
DECISION_KEYWORDS = [
    r'\b(决定|采用|选择|改用|确定|最终方案|不再|改为|统一用|约定)\b',
    r'\b(decided|chose|switched to|settled on|agreed to|opted for)\b',
]
ERROR_KEYWORDS = [
    r'\b(报错|出错|失败|错误|bug|Bug|异常|崩溃)\b',
    r'\b(error|failed|failure|crash|exception|timeout|segfault)\b',
    r'Traceback', r'segfault', r'SSL.error',
]


def extract_text(rec):
    """Extract text from JSONL record (handles nested message formats)."""
    msg = rec.get('message', '')
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        content = msg.get('content', [])
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    t = block.get('text', '')
                    if isinstance(t, str):
                        texts.append(t)
            return '\n'.join(texts)
    return ''


def score_session(jsonl_path, project_patterns=None):
    """Score a single session JSONL file.

    Args:
        jsonl_path: Path to the session JSONL file.
        project_patterns: Dict of project_name -> [regex patterns].
                          Uses PROJECT_PATTERNS if None.

    Returns dict with score breakdown.
    """
    if project_patterns is None:
        project_patterns = PROJECT_PATTERNS

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    n_assistant = 0
    n_decisions = 0
    n_errors = 0
    all_text = ""

    for line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get('type') == 'assistant':
            n_assistant += 1
            msg = extract_text(rec)
            all_text += msg + '\n'
            # Formal annotations
            if '[DECISION:' in msg or '[DECISION]' in msg:
                n_decisions += 1
            if '[ERROR:' in msg or '[ERROR]' in msg:
                n_errors += 1

    # Heuristic fallback if no formal annotations found
    if n_decisions == 0:
        for pat in DECISION_KEYWORDS:
            n_decisions += len(re.findall(pat, all_text, re.IGNORECASE))
    if n_errors == 0:
        for pat in ERROR_KEYWORDS:
            n_errors += len(re.findall(pat, all_text, re.IGNORECASE))

    # Cap at n_assistant to avoid inflated counts
    n_decisions = min(n_decisions, n_assistant)
    n_errors = min(n_errors, n_assistant)

    decision_density = n_decisions / max(n_assistant, 1)
    error_density = n_errors / max(n_assistant, 1)

    # Detect projects from configurable patterns
    detected_projects = set()
    if project_patterns:
        for proj, patterns in project_patterns.items():
            for pat in patterns:
                if re.search(pat, all_text, re.IGNORECASE):
                    detected_projects.add(proj)
                    break

    project_coverage = 1.0
    total = (decision_density * 0.4 +
             error_density * 0.4 +
             project_coverage * 0.2)

    return {
        'session_id': os.path.basename(jsonl_path).replace('.jsonl', ''),
        'file_size': os.path.getsize(jsonl_path),
        'n_assistant': n_assistant,
        'n_decisions': n_decisions,
        'n_errors': n_errors,
        'decision_density': round(decision_density, 4),
        'error_density': round(error_density, 4),
        'project_coverage': round(project_coverage, 2),
        'total_score': round(total, 4),
        'detected_projects': list(detected_projects),
    }


def load_patterns_from_yaml(yaml_path):
    """Load project detection patterns from a YAML file.

    Expected format:
      project_name:
        - pattern1
        - pattern2
    """
    import yaml
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Score JSONL sessions using 3D metric"
    )
    parser.add_argument('source', help='Directory containing JSONL session files')
    parser.add_argument('--output', default=None,
                        help='Output JSON file path')
    parser.add_argument('--top', type=int, default=20,
                        help='Number of top results to display (default: 20)')
    parser.add_argument('--patterns-file', default=None,
                        help='YAML file with project detection patterns')
    args = parser.parse_args()

    source = args.source
    if not os.path.exists(source):
        print(f"ERROR: Source directory not found: {source}")
        sys.exit(1)

    # Load project patterns
    project_patterns = PROJECT_PATTERNS.copy()
    if args.patterns_file:
        try:
            extra = load_patterns_from_yaml(args.patterns_file)
            project_patterns.update(extra)
            print(f"Loaded {len(extra)} project(s) from {args.patterns_file}")
        except Exception as e:
            print(f"WARNING: Could not load patterns file: {e}")

    if not project_patterns:
        print("WARNING: No project patterns configured. "
              "All sessions will have empty project coverage.")
        print("  Edit PROJECT_PATTERNS in this script or use --patterns-file.")

    # Collect JSONL files
    results = []
    jsonl_files = []
    for root, dirs, files in os.walk(source):
        for f in files:
            if f.endswith('.jsonl'):
                jsonl_files.append(os.path.join(root, f))

    print(f"Scanning {len(jsonl_files)} JSONL files...")
    for i, fp in enumerate(sorted(jsonl_files)):
        if i % 50 == 0:
            print(f"  {i}/{len(jsonl_files)}...")
        results.append(score_session(fp, project_patterns))

    results.sort(key=lambda x: x['total_score'], reverse=True)

    # Display top results
    top_n = min(args.top, len(results))
    print(f"\n=== Top {top_n} Sessions by 3D Score ===\n")
    header = (f"{'#':<4} {'Session ID':<42} {'Score':>8} "
              f"{'Dec':>5} {'Err':>5} {'Asst':>6} {'Size':>8} {'Projects'}")
    print(header)
    print("-" * 115)
    for i, r in enumerate(results[:top_n]):
        sid = r['session_id'][:40]
        size_kb = r['file_size'] // 1024
        projs = ','.join(r['detected_projects'][:2]) or '?'
        print(f"{i+1:<4} {sid:<42} {r['total_score']:>8.4f} "
              f"{r['n_decisions']:>5} {r['n_errors']:>5} "
              f"{r['n_assistant']:>6} {size_kb:>7}KB {projs}")

    # Output results
    if args.output:
        out_path = args.output
    else:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'score_results.json')

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull results -> {out_path}")


if __name__ == '__main__':
    main()
