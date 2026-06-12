"""Load configuration from config.yaml or config.example.yaml (fallback).

Priority:
1. config.yaml (user-specific, git-ignored)
2. config.example.yaml (shipped default, never edited)
"""

import os
import sys
import yaml
import json


def _find_config_dir():
    """Find the directory containing config files.
    Searches: script directory, current working directory, parent directory."""
    candidates = [
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
        os.path.join(os.getcwd(), 'scripts'),
    ]
    for d in candidates:
        if os.path.exists(os.path.join(d, 'config.yaml')):
            return d
        if os.path.exists(os.path.join(d, 'config.example.yaml')):
            return d
    return os.path.dirname(os.path.abspath(__file__))


def load_config():
    """Load configuration, with validation of required keys and paths."""
    config_dir = _find_config_dir()

    # Try config.yaml first, fall back to config.example.yaml
    config_path = os.path.join(config_dir, 'config.yaml')
    if not os.path.exists(config_path):
        config_path = os.path.join(config_dir, 'config.example.yaml')

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    # Validate required keys exist
    required = ['vault_path', 'claude_project_path', 'python_path']
    for key in required:
        if not cfg.get(key):
            raise KeyError(
                f"config.yaml missing required key: {key}\n"
                f"  Run 'python setup.py' to configure, or edit config.yaml manually."
            )

    # Validate that required paths exist (warn but don't abort for vault_path
    # since it may not exist yet on first run)
    for key in ['claude_project_path']:
        path = os.path.expanduser(cfg[key])
        if not os.path.exists(path):
            print(f"WARNING: config path not found: {key}={cfg[key]}")
            print(f"  The scanner may fail. Run setup.py to reconfigure.")

    # Expand paths in config
    for key in ['vault_path', 'claude_project_path', 'python_path',
                 'claude_md_path', 'log_dir']:
        if cfg.get(key):
            cfg[key] = os.path.expanduser(cfg[key])

    # Derive log_dir from vault_path if empty
    if not cfg.get('log_dir'):
        cfg['log_dir'] = os.path.join(cfg['vault_path'],
                                       '04-Feedback', '_logs')

    return cfg


def get_api_config(cfg):
    """Read API configuration from config.yaml + settings.json.

    Returns dict with: key, base_url, model, temperature, max_tokens,
    max_retries, retry_backoff_sec.

    Base URL and model can be overridden in config.yaml;
    if null, they are read from settings.json.
    """
    api_cfg = cfg.get('api', {})
    settings_path = os.path.expanduser(api_cfg.get('settings_json', ''))

    settings = {}
    if settings_path and os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)

    return {
        'key': settings.get('ANTHROPIC_AUTH_TOKEN'),
        'base_url': (api_cfg.get('base_url') or
                     settings.get('ANTHROPIC_BASE_URL',
                                  'https://api.anthropic.com/v1')),
        'model': (api_cfg.get('model') or
                  settings.get('ANTHROPIC_MODEL',
                               'claude-sonnet-4-20250514')),
        'temperature': api_cfg.get('temperature', 0.3),
        'max_tokens': api_cfg.get('max_tokens', 2000),
        'max_retries': api_cfg.get('max_retries', 3),
        'retry_backoff_sec': api_cfg.get('retry_backoff_sec', [2, 4, 8]),
    }


def get_api_key(cfg):
    """Read API key from Claude settings.json (not stored in config.yaml).

    DEPRECATED: use get_api_config()['key'] instead.
    """
    return get_api_config(cfg)['key']
