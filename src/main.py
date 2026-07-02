from launcher import launch_all
from logger import logger

try:
    from utils.version import get_version
except ImportError:
    from utils.version import VERSION

    def get_version():
        return VERSION


if __name__ == "__main__":
    version = get_version()
    banner_version = "dev" if version == "dev" else f"v{version}"
    logger.info("ControllerHub - VATSIM Controller Hub Launcher (%s)", banner_version)
    logger.info("Starting application launcher...")
    # Check if all apps launched successfully. Later change this to a more user-friendly message or GUI. 
    # Use try-except to catch any unexpected errors and print them.
    # use logging module to log errors instead of print statements for better debugging and maintenance.
    if launch_all():
        logger.info("All apps launched successfully ✅")
    else:
        logger.error("Some apps failed to start ❌")