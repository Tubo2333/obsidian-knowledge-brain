"""Load configuration from config.yaml."""
import os
import sys
import yaml
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    # Validate required keys
    required = ['vault_path', 'claude_project_path', 'python_path']
    for key in required:
        if key not in cfg:
            raise KeyError(f"config.yaml missing required key: {key}")
    # Validate paths exist
    for key in ['vault_path', 'claude_project_path']:
        if not os.path.exists(cfg[key]):
            raise FileNotFoundError(f"config path not found: {key}={cfg[key]}")
    return cfg

def get_api_config(cfg):
    """Read API configuration from config.yaml + settings.json.
    Returns {key, base_url, model, temperature, max_tokens, max_retries, retry_backoff_sec}.
    Base URL and model can be overridden in config.yaml; if null, read from settings.json.
    API key lives in settings.json's 'env' block (Claude Code convention).
    """
    api_cfg = cfg.get('api', {})
    settings_path = api_cfg.get('settings_json', '')
    settings = {}
    if settings_path and os.path.exists(settings_path):
        import json
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)

    # API key is nested under 'env' in Claude Code's settings.json
    env = settings.get('env', {})
    api_key = (api_cfg.get('key') or
               env.get('ANTHROPIC_AUTH_TOKEN') or
               settings.get('ANTHROPIC_AUTH_TOKEN') or
               '')

    return {
        'key': api_key,
        'base_url': (api_cfg.get('base_url') or
                     env.get('ANTHROPIC_BASE_URL') or
                     settings.get('ANTHROPIC_BASE_URL') or
                     'https://api.anthropic.com/v1'),
        'model': (api_cfg.get('model') or
                  env.get('ANTHROPIC_MODEL') or
                  settings.get('ANTHROPIC_MODEL') or
                  'claude-sonnet-4-20250514'),
        'temperature': api_cfg.get('temperature', 0.3),
        'max_tokens': api_cfg.get('max_tokens', 4000),
        'max_retries': api_cfg.get('max_retries', 3),
        'retry_backoff_sec': api_cfg.get('retry_backoff_sec', [2, 4, 8]),
    }

def get_api_key(cfg):
    """Read API key from Claude settings.json (not stored in config.yaml).
    DEPRECATED: use get_api_config()['key'] instead.
    """
    return get_api_config(cfg)['key']
