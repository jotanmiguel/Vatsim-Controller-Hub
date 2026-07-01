import json
from datetime import datetime, timezone
from pathlib import Path

from logger import logger
from utils.version import get_version


BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_DIR = BASE_DIR / "settings"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"
LEGACY_SETTINGS_PATH = BASE_DIR / "config" / "config.json"


def load_settings():
    """Loads settings from the JSON file if it exists."""
    source_path = SETTINGS_PATH if SETTINGS_PATH.exists() else LEGACY_SETTINGS_PATH

    if source_path.exists():
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                logger.info(f"INFO: Loaded settings from {source_path}")
                return normalize_settings(json.load(f))
        except (json.JSONDecodeError, OSError):
            logger.error(f"ERROR: Failed to load settings from {source_path}")
            return {}
    return {}


def save_settings(settings):
    """Saves settings to the JSON file."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    payload = normalize_settings(settings)
    payload["version"] = get_version()

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        logger.info(f"INFO: Saved settings to {SETTINGS_PATH}")
        json.dump(payload, f, indent=2, ensure_ascii=False)


def normalize_settings(settings):
    """Normalizes legacy string-based settings into the current dict format."""
    normalized = {"version": (settings or {}).get("version", get_version())}

    for key, value in (settings or {}).items():
        if key == "version":
            continue

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
    """Builds a settings entry using the current format."""
    return {
        "path": path,
        "via": via,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }