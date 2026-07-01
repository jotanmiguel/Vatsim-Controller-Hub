import os
import subprocess
import sys

from utils.detect import ProgramDetector
from utils.settings import SETTINGS_PATH, build_entry, load_settings, normalize_settings, save_settings
from logger import logger

APP_SPECS = [
    ("euroscope", "EuroScope"),
    ("trackaudio", "TrackAudio"),
    ("vacs", "VACS"),
]


def is_valid_exe(path):
    logger.debug(f"DEBUG: Checking if path is valid exe: {path}")
    return bool(path) and os.path.isfile(path) and path.lower().endswith(".exe")


def get_settings_path(settings_entry):
    """Returns the executable path from a settings entry or legacy string."""
    logger.debug(f"DEBUG: Getting settings path from entry: {settings_entry}")
    if isinstance(settings_entry, dict):
        logger.debug(f"DEBUG: Settings entry is a dict, returning path: {settings_entry.get('path')}")
        return settings_entry.get("path")
    logger.debug(f"DEBUG: Settings entry is not a dict, returning as-is: {settings_entry}")
    return settings_entry


def get_program_path(program_name, settings, settings_override=None, detector=None):
    """
    Gets the path to a program using priority:
    1. Settings file override
    2. Auto-detection via registry/disk
    """
    logger.debug(f"DEBUG: Getting program path for {program_name} with settings override: {settings_override}")
    if settings_override and settings_override in settings:
        settings_path = get_settings_path(settings[settings_override])
        if is_valid_exe(settings_path):
            return settings_path
    
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
    """Creates or refreshes settings.json with detected installation paths."""
    settings = normalize_settings(load_settings())
    detector = ProgramDetector()
    updated = False

    for setting_key, display_name in APP_SPECS:
        current_entry = settings.get(setting_key, {})
        current_path = get_settings_path(current_entry)
        if is_valid_exe(current_path):
            if not (isinstance(current_entry, dict) and current_entry.get("timestamp")):
                via = current_entry.get("via", "Legacy") if isinstance(current_entry, dict) else "Legacy"
                settings[setting_key] = build_entry(current_path, via)
                updated = True
            continue

        detected_path, via = detect_program_with_source(detector, setting_key)
        if detected_path:
            settings[setting_key] = build_entry(detected_path, via)
            updated = True
            print(f"SETUP: {display_name} -> {detected_path} ({via})")
        else:
            print(f"SETUP: {display_name} not found automatically")

    if updated or not SETTINGS_PATH.exists():
        save_settings(settings)
        print(f"SETUP: saved to {SETTINGS_PATH}")

    return settings


def launch_app(path, app_name):
    """Launches an application."""
    if not path:
        logger.error("Could not find %s", app_name)
        return False
    
    if not os.path.exists(path):
        logger.error("Path not found: %s", path)
        return False
    
    try:
        subprocess.Popen(path)
        logger.info("Launched %s from path: %s", app_name, path)
        return True
    except Exception as e:
        logger.error("Failed to launch %s: %s", app_name, e)
        return False


def launch_all():
    """Launches all required applications."""
    settings = ensure_setup()
    
    for setting_key, display_name in APP_SPECS:
        path = get_program_path(setting_key, settings, setting_key)
        if not launch_app(path, display_name):
            logger.error("Failed to launch %s. Please check the settings file at %s.", display_name, SETTINGS_PATH)
            return False
    
    return True


if __name__ == "__main__":
    success = launch_all()
    sys.exit(0 if success else 1)