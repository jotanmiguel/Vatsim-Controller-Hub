import json
import os
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def launch_app(path):
    if os.path.exists(path):
        subprocess.Popen(path)
    else:
        print(f"Not found: {path}")

def launch_all():
    config = load_config()

    launch_app(config["euroscope"])
    launch_app(config["trackaudio"])
    launch_app(config["vacs"])

if __name__ == "__main__":
    launch_all()