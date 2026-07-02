try:
    from version import VERSION as CURRENT_VERSION
except ImportError:
    CURRENT_VERSION = "dev"


def get_version():
    """Returns the current version of the application."""
    return CURRENT_VERSION