import logging
from pathlib import Path
import time

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("ControllerHub")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s    %(levelname)-8s    %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

timestamp = time.time_ns

file_handler = logging.FileHandler(LOG_DIR / f"controllerhub-{timestamp()}.log", encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)