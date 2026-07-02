import sys


VERSION = "dev"


def get_version():
	"""Returns dev for source runs and the embedded version for frozen binaries."""
	if getattr(sys, "frozen", False):
		return VERSION
	return "dev"
