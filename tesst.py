import subprocess

def get_version():
    return subprocess.check_output(["git", "describe", "--tags"]).decode().strip()

get_version()