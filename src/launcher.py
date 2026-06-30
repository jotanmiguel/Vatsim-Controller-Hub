import os
import subprocess
import sys

from utils.detect import ProgramDetector
from utils.config import CONFIG_PATH, build_entry, load_config, normalize_config, save_config

APP_SPECS = [
    ("euroscope", "EuroScope"),
    ("trackaudio", "TrackAudio"),
    ("vacs", "VACS"),
]


def is_valid_exe(path):
    return bool(path) and os.path.isfile(path) and path.lower().endswith(".exe")


def get_config_path(config_entry):
    """Returns the executable path from a config entry or legacy string."""
    if isinstance(config_entry, dict):
        return config_entry.get("path")
    return config_entry


def get_program_path(program_name, config, config_override=None, detector=None):
    """
    Gets the path to a program using priority:
    1. Config file override
    2. Auto-detection via registry/disk
    """
    if config_override and config_override in config:
        config_path = get_config_path(config[config_override])
        if is_valid_exe(config_path):
            return config_path
    
    detector = detector or ProgramDetector()
    return detector.detect(program_name)


def detect_program_with_source(detector, program_name):
    """Detects a program and returns the path plus the detection source."""
    for via, detector_fn in [
        ("Registry", detector.registry),
        ("Common Paths", detector.common_paths),
    ]:
        path = detector_fn(program_name)
        if path:
            return path, via

    path = detector.open_file_dialog(program_name)
    if path:
        return path, "Manual"

    return None, None


def ensure_setup():
    """Creates or refreshes config.json with detected installation paths."""
    config = normalize_config(load_config())
    detector = ProgramDetector()
    updated = False

    for config_key, display_name in APP_SPECS:
        current_entry = config.get(config_key, {})
        current_path = get_config_path(current_entry)
        if is_valid_exe(current_path):
            if not (isinstance(current_entry, dict) and current_entry.get("timestamp")):
                via = current_entry.get("via", "Legacy") if isinstance(current_entry, dict) else "Legacy"
                config[config_key] = build_entry(current_path, via)
                updated = True
            continue

        detected_path, via = detect_program_with_source(detector, config_key)
        if detected_path:
            config[config_key] = build_entry(detected_path, via)
            updated = True
            print(f"SETUP: {display_name} -> {detected_path} ({via})")
        else:
            print(f"SETUP: {display_name} not found automatically")

    if updated or not CONFIG_PATH.exists():
        save_config(config)
        print(f"SETUP: saved to {CONFIG_PATH}")

    return config


def launch_app(path, app_name):
    """Launches an application."""
    if not path:
        print(f"ERROR: Could not find {app_name}")
        return False
    
    if not os.path.exists(path):
        print(f"ERROR: Path not found: {path}")
        return False
    
    try:
        subprocess.Popen(path)
        return True
    except Exception as e:
        print(f"ERROR: Failed to launch {app_name}: {e}")
        return False


def launch_all():
    """Launches all required applications."""
    config = ensure_setup()
    
    for config_key, display_name in APP_SPECS:
        path = get_program_path(config_key, config, config_key)
        print(f"DEBUG: Launching {display_name} from: {path}")
        if not launch_app(path, display_name):
            return False
    
    return True


if __name__ == "__main__":
    success = launch_all()
    sys.exit(0 if success else 1)