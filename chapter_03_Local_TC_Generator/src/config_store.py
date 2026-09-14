import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULTS = {
    "jira_url": "",
    "jira_email": "",
    "jira_api_token": "",
    "llm_provider": "local",
    "groq_api_key": "",
}


def _first_env(*names):
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return ""


def load_config() -> dict:
    """Load config from config.json, falling back to .env for first run."""
    load_dotenv(BASE_DIR / ".env")

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    env_map = {
        "jira_url": ("JIRA_URL", "jira_url"),
        "jira_email": ("JIRA_EMAIL", "Jira_EMAIL", "jira_email", "Jira_Email"),
        "jira_api_token": ("JIRA_API_TOKEN", "jira_api_token"),
        "groq_api_key": ("GROQ_API_KEY", "groq_api_key"),
        "llm_provider": ("LLM_PROVIDER", "llm_provider", "PROVIDER"),
    }

    for key, env_names in env_map.items():
        if not config.get(key):
            config[key] = _first_env(*env_names) or DEFAULTS.get(key, "")

    return config


def save_config(config: dict) -> None:
    """Persist config dict to config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_setting(key: str) -> str:
    return load_config().get(key, DEFAULTS.get(key, ""))


def set_setting(key: str, value: str) -> None:
    config = load_config()
    config[key] = value
    save_config(config)
