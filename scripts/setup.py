#!/usr/bin/env python3
"""Interactive setup script for Obsidian Knowledge Brain.

Creates the vault directory structure, prompts for paths and project names,
generates config.yaml, copies templates, and validates everything.
"""

import os
import sys
import yaml
import shutil
from pathlib import Path


def expand_path(path_str):
    """Expand ~ and environment variables in a path."""
    return os.path.expandvars(os.path.expanduser(path_str))


def prompt(prompt_text, default=None):
    """Prompt with optional default value."""
    if default:
        result = input(f"{prompt_text} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt_text}: ").strip()


def prompt_required(prompt_text, validate_exists=False):
    """Prompt for a required value. Optionally validate that the path exists."""
    while True:
        value = prompt(prompt_text)
        if not value:
            print("  This field is required. Please enter a value.")
            continue
        if validate_exists:
            expanded = expand_path(value)
            if not os.path.exists(expanded):
                print(f"  Path not found: {expanded}")
                yn = prompt("  Create it? (y/n)", "y").lower()
                if yn == 'y':
                    os.makedirs(expanded, exist_ok=True)
                    print(f"  Created: {expanded}")
                    return value
                print("  Please enter a valid path.")
                continue
        return value


def detect_defaults():
    """Auto-detect default paths based on the current environment."""
    defaults = {}

    # Python path
    defaults['python_path'] = sys.executable

    # Claude project path
    home = os.path.expanduser("~")
    claude_projects = os.path.join(home, ".claude", "projects")
    if os.path.exists(claude_projects):
        # List available project dirs
        subdirs = [d for d in os.listdir(claude_projects)
                   if os.path.isdir(os.path.join(claude_projects, d))]
        if subdirs:
            print(f"\nDetected Claude projects at: {claude_projects}")
            print("Available project directories:")
            for i, d in enumerate(subdirs):
                print(f"  [{i+1}] {d}")
            # Default to first one
            defaults['claude_project_path'] = os.path.join(claude_projects, subdirs[0])
        else:
            defaults['claude_project_path'] = claude_projects
    else:
        defaults['claude_project_path'] = os.path.join(home, ".claude", "projects")

    # Claude settings.json
    settings_path = os.path.join(home, ".claude", "settings.json")
    if os.path.exists(settings_path):
        defaults['settings_json'] = settings_path

    # Vault path
    defaults['vault_path'] = os.path.join(home, "ObsidianBrain")

    # CLAUDE.md
    for candidate in [
        os.path.join(home, "projects", "CLAUDE.md"),
        os.path.join(os.getcwd(), "CLAUDE.md"),
    ]:
        if os.path.exists(candidate):
            defaults['claude_md_path'] = candidate
            break
    if 'claude_md_path' not in defaults:
        defaults['claude_md_path'] = ""

    return defaults


def create_vault_structure(vault_path):
    """Create the full vault directory structure with README files."""
    vault = expand_path(vault_path)
    os.makedirs(vault, exist_ok=True)

    dirs = [
        "00-Rules/_inbox/_rejected",
        "00-Rules/_archive",
        "01-Projects",
        "02-Templates",
        "03-Maps",
        "04-Feedback/_logs",
        "04-Feedback/_raw-sessions",
        "04-Feedback/_rollback",
        "04-Feedback/weekly-reports",
    ]

    for d in dirs:
        dpath = os.path.join(vault, d)
        os.makedirs(dpath, exist_ok=True)

    # Write vault README.md with frontmatter
    readme_content = f"""---
vault_version: "1.0"
created: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
vault_name: "Obsidian Knowledge Brain"
description: "AI-human shared knowledge brain — dual-channel approval system for project memory and cross-project rules"
---

# Obsidian Knowledge Brain

> AI-human shared knowledge vault. Weekly scanner detects patterns, proposes rules, maintains indices.

## Structure

| Directory | Purpose |
|-----------|---------|
| `00-Rules/` | Active rules, inbox approval cards, archive |
| `01-Projects/` | One folder per project with Memory/sessions/ |
| `02-Templates/` | Markdown templates for sessions, decisions, pitfalls |
| `03-Maps/` | Auto-generated topic index, timeline, search index |
| `04-Feedback/` | Weekly reports, scanner logs, raw session backups |

## Getting Started

1. Project folders are created automatically by the scanner
2. Session summaries go in `01-Projects/<name>/Memory/sessions/`
3. Rules start in `00-Rules/_inbox/` as approval cards
4. The weekly scanner rebuilds `03-Maps/` automatically
"""
    with open(os.path.join(vault, "README.md"), 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # Write error-taxonomy.md template
    taxonomy_content = """---
version: "1.0"
categories:
  - name: env
    english: "Environment / Platform"
    chinese: "环境与平台"
    subcategories:
      - env_os_path_separator
      - env_encoding_mismatch
      - env_permission_denied
      - env_dependency_conflict
      - env_network_restriction
  - name: api
    english: "API / Interface"
    chinese: "接口调用"
    subcategories:
      - api_parameter_error
      - api_auth_failure
      - api_rate_limit
      - api_endpoint_change
      - api_unexpected_response
  - name: data
    english: "Data / Format"
    chinese: "数据格式"
    subcategories:
      - data_missing_column
      - data_type_mismatch
      - data_corrupted_file
      - data_encoding_garbled
      - data_schema_violation
  - name: lang
    english: "Language / Runtime"
    chinese: "语言运行时"
    subcategories:
      - lang_version_incompat
      - lang_package_conflict
      - lang_segfault_crash
      - lang_memory_overflow
      - lang_silent_failure
  - name: logic
    english: "Logic / Algorithm"
    chinese: "逻辑算法"
    subcategories:
      - logic_off_by_one
      - logic_assumption_violated
      - logic_edge_case_unhandled
      - logic_race_condition
      - logic_infinite_loop
  - name: pipeline
    english: "Pipeline / Workflow"
    chinese: "流程编排"
    subcategories:
      - pipeline_step_order_wrong
      - pipeline_missing_dependency
      - pipeline_output_format_mismatch
      - pipeline_intermediate_file_stale
      - pipeline_parallel_conflict
  - name: render
    english: "Rendering / Output"
    chinese: "渲染输出"
    subcategories:
      - render_color_greyscale
      - render_text_cropped
      - render_font_missing
      - render_resolution_mismatch
      - render_device_driver_issue
  - name: network
    english: "Network / Remote"
    chinese: "网络远程"
    subcategories:
      - network_tcp_reset
      - network_ssl_handshake_failure
      - network_timeout
      - network_dns_failure
      - network_firewall_block
  - name: config
    english: "Configuration"
    chinese: "配置管理"
    subcategories:
      - config_key_missing
      - config_type_wrong
      - config_conflict_between_files
      - config_stale_cache
      - config_secret_leaked
  - name: tool
    english: "Tool / External"
    chinese: "外部工具"
    subcategories:
      - tool_binary_not_found
      - tool_version_mismatch
      - tool_flag_changed
      - tool_output_parse_error
      - tool_lock_contention
  - name: human
    english: "Human / Process"
    chinese: "人为流程"
    subcategories:
      - human_forgot_checkpoint
      - human_skipped_verification
      - human_wrong_order
      - human_assumed_default
      - human_typo
---

# Error Taxonomy

> 11 categories x 5 subcategories each = 55 error types.
> Customize subcategories to match your stack.
> 11大类 x 每类5个子类 = 55种错误类型。根据你的技术栈自定义子类。

## How to Use

When writing session summaries, tag errors with one of these subcategory codes in the `errors_encountered` frontmatter field. The scanner's analyzer will count occurrences and propose rules when >=2 sessions share the same error type.
"""
    with open(os.path.join(vault, "04-Feedback", "error-taxonomy.md"), 'w', encoding='utf-8') as f:
        f.write(taxonomy_content)

    # Write heartbeat.md placeholder
    heartbeat_content = f"""---
last_scan: null
scan_status: never_run
sessions_processed: 0
processed_sessions: {{}}
errors: []
script_version: "1.0.0"
---

# Scanner Heartbeat

The weekly scanner has not run yet. Run `runner.py` to start the first scan.
"""
    with open(os.path.join(vault, "04-Feedback", "heartbeat.md"), 'w', encoding='utf-8') as f:
        f.write(heartbeat_content)

    return vault


def create_project_folders(vault_path, project_names):
    """Create project directories with Memory/sessions/ subdirectories."""
    vault = expand_path(vault_path)
    projects_dir = os.path.join(vault, "01-Projects")
    created = []

    for name in project_names:
        name = name.strip().replace(" ", "-").lower()
        if not name:
            continue
        proj_dir = os.path.join(projects_dir, name)
        memory_dir = os.path.join(proj_dir, "Memory")
        sessions_dir = os.path.join(memory_dir, "sessions")

        os.makedirs(proj_dir, exist_ok=True)
        os.makedirs(sessions_dir, exist_ok=True)

        # Create decisions.md
        decisions_path = os.path.join(memory_dir, "decisions.md")
        if not os.path.exists(decisions_path):
            with open(decisions_path, 'w', encoding='utf-8') as f:
                f.write(f"""---
project: "{name}"
decisions: []
updated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
---

# Decisions — {name}

Key technical decisions made across sessions.
""")

        # Create pitfalls.md
        pitfalls_path = os.path.join(memory_dir, "pitfalls.md")
        if not os.path.exists(pitfalls_path):
            with open(pitfalls_path, 'w', encoding='utf-8') as f:
                f.write(f"""---
project: "{name}"
pitfalls: []
updated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
---

# Pitfalls — {name}

Hard-won lessons and known issues.
""")

        created.append(name)

    return created


def validate_setup(vault_path, config_path):
    """Validate the vault structure and config."""
    vault = expand_path(vault_path)
    errors = []

    # Check required directories
    required_dirs = [
        "00-Rules/_inbox",
        "00-Rules/_archive",
        "01-Projects",
        "03-Maps",
        "04-Feedback/_logs",
        "04-Feedback/_raw-sessions",
        "04-Feedback/weekly-reports",
    ]
    for d in required_dirs:
        dpath = os.path.join(vault, d)
        if not os.path.exists(dpath):
            errors.append(f"Missing directory: {d}")

    # Check required files
    required_files = [
        "README.md",
        "04-Feedback/error-taxonomy.md",
        "04-Feedback/heartbeat.md",
    ]
    for f in required_files:
        fpath = os.path.join(vault, f)
        if not os.path.exists(fpath):
            errors.append(f"Missing file: {f}")

    # Validate config.yaml
    if not os.path.exists(config_path):
        errors.append("config.yaml not found")
    else:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        for key in ['vault_path', 'claude_project_path', 'python_path']:
            if not cfg.get(key):
                errors.append(f"config.yaml: {key} is empty")

    return errors


def main():
    print("=" * 60)
    print("  Obsidian Knowledge Brain — Setup")
    print("  AI-human shared knowledge vault")
    print("=" * 60)
    print()

    defaults = detect_defaults()

    # Step 1: Gather paths
    print("--- Path Configuration ---")
    print()

    vault_path = prompt_required(
        f"Vault path (where the Obsidian vault lives)",
        validate_exists=False
    )
    if vault_path and not expand_path(vault_path):
        vault_path = defaults['vault_path']

    claude_project_path = prompt_required(
        f"Claude projects directory (where JSONL sessions are stored)"
    )
    if not claude_project_path:
        claude_project_path = defaults['claude_project_path']

    python_path = prompt(
        "Python 3 interpreter path",
        defaults['python_path']
    )

    claude_md_path = prompt(
        "Path to CLAUDE.md (for compiler step, optional)",
        defaults.get('claude_md_path', '')
    )

    settings_json = prompt(
        "Path to Claude settings.json (for API key, optional)",
        defaults.get('settings_json', '')
    )

    print()

    # Step 2: Project names
    print("--- Projects ---")
    print()
    print("Enter project names, separated by commas.")
    print('Example: "my-research, side-project, blog"')
    project_input = prompt("Project names", "")
    project_names = [p.strip() for p in project_input.split(",") if p.strip()] if project_input else []

    print()

    # Step 3: Scan schedule
    print("--- Scanner Schedule ---")
    print()
    scan_day = prompt("Day of week for scanner", "SUN").upper()
    scan_hour = int(prompt("Hour (0-23)", "15"))
    scan_minute = int(prompt("Minute (0-59)", "0"))
    print()

    # Step 4: Topic map (optional)
    print("--- Topic Map (Optional) ---")
    print()
    print("The topic map groups session tags into topics for the auto-generated index.")
    print("Leave empty to skip — you can add topics later in config.yaml.")
    topic_map_input = prompt(
        "Add a topic? Format: tag, Topic Name / 中文名称, Description",
        ""
    )
    topic_map = {}
    if topic_map_input:
        parts = [p.strip() for p in topic_map_input.split(",", 2)]
        if len(parts) >= 2:
            topic_map[parts[0]] = [parts[1], parts[2] if len(parts) > 2 else ""]

    print()

    # Step 5: Confirm
    print("--- Summary ---")
    print(f"  Vault path:        {vault_path}")
    print(f"  Claude projects:   {claude_project_path}")
    print(f"  Python:            {python_path}")
    print(f"  CLAUDE.md:         {claude_md_path or '(not set)'}")
    print(f"  API settings:      {settings_json or '(not set)'}")
    print(f"  Projects:          {project_names if project_names else '(none — add later)'}")
    print(f"  Scan schedule:     {scan_day} at {scan_hour:02d}:{scan_minute:02d}")
    print()

    confirm = prompt("Proceed with setup? (y/n)", "y").lower()
    if confirm != 'y':
        print("Setup cancelled.")
        sys.exit(0)

    # Step 6: Create vault structure
    print()
    print("Creating vault structure...")
    vault = create_vault_structure(vault_path)
    print(f"  Vault created at: {vault}")

    # Step 7: Create project folders
    if project_names:
        print("Creating project folders...")
        created = create_project_folders(vault_path, project_names)
        for name in created:
            print(f"  + {name}")

    # Step 8: Generate config.yaml
    config = {
        'version': '1.0',
        'vault_path': vault_path,
        'claude_project_path': claude_project_path,
        'claude_md_path': claude_md_path,
        'python_path': python_path,
        'api': {
            'settings_json': settings_json,
            'base_url': None,
            'model': None,
            'temperature': 0.3,
            'max_tokens': 2000,
            'max_retries': 3,
            'retry_backoff_sec': [2, 4, 8],
        },
        'log_level': 'INFO',
        'log_dir': '',
        'scan': {
            'day': scan_day,
            'hour': scan_hour,
            'minute': scan_minute,
        },
        'topic_map': topic_map if topic_map else {},
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.yaml")
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"  Config written to: {config_path}")

    # Step 9: Validate
    print()
    print("Validating setup...")
    errors = validate_setup(vault_path, config_path)
    if errors:
        print("  WARNINGS:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  All checks passed!")

    # Step 10: Next steps
    print()
    print("=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print(f"  1. Open Obsidian and load vault: {vault_path}")
    print(f"  2. Add more projects: create folders under 01-Projects/")
    print(f"     Each project needs: Memory/sessions/  Memory/decisions.md  Memory/pitfalls.md")
    print(f"  3. Customize error taxonomy: 04-Feedback/error-taxonomy.md")
    print(f"  4. Customize topic map: edit config.yaml -> topic_map")
    print(f"  5. Run first scan:")
    print(f"     cd {script_dir}")
    print(f"     python runner.py --full")
    print(f"  6. Set up weekly cron/scheduled task for runner.py")
    print()


if __name__ == '__main__':
    main()
