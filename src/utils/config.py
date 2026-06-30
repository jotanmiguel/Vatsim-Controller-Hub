import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"

def load_config():
    """Loads config from JSON file if it exists."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return normalize_config(json.load(f))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(config):
    """Saves config to JSON file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def normalize_config(config):
    """Normalizes legacy string-based configs into the current dict format."""
    normalized = {}

    for key, value in (config or {}).items():
        if isinstance(value, dict):
            path = value.get("path")
            via = value.get("via", "Unknown")
            timestamp = value.get("timestamp")
        else:
            path = value
            via = "Legacy"
            timestamp = None

        normalized[key] = {
            "path": path,
            "via": via,
            "timestamp": timestamp,
        }

    return normalized


def build_entry(path, via, timestamp=None):
    """Builds a config entry using the current format."""
    return {
        "path": path,
        "via": via,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }