
# providers/debian.py
import subprocess
import os
from .base_provider import BaseProvider

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        # Set non-interactive for apt
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        subprocess.run(cmd, check=True, env=env)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """Debian/Ubuntu provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "apt", "install", "-y"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "apt", "remove", "-y"] + packages)

    def update(self) -> bool:
        run_cmd(["sudo", "apt", "update"])
        return run_cmd(["sudo", "apt", "upgrade", "-y"])

    def search(self, package: str) -> bool:
        return run_cmd(["apt", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f", "${binary:Package}\n"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        return {
            "yq": "sudo apt install yq",
            "timeshift": "sudo apt install timeshift"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Debian-based machines",
            "packages": [
                "build-essential",
                "linux-image-generic",
                "network-manager",
                "vim",
                "git",
                "yq"
            ]
        }
