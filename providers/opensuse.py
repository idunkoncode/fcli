
# providers/opensuse.py
import subprocess
from .base_provider import BaseProvider

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """openSUSE provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "zypper", "install", "--non-interactive"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "zypper", "remove", "--non-interactive"] + packages)

    def update(self) -> bool:
        # 'dup' is standard for Tumbleweed, 'up' for Leap. 'dup' is safer.
        return run_cmd(["sudo", "zypper", "dup", "--non-interactive"])

    def search(self, package: str) -> bool:
        return run_cmd(["zypper", "search", package])

    def get_installed_packages(self) -> set:
        try:
            # Same as Fedora, uses rpm
            result = subprocess.run(
                ["rpm", "-qa", "--qf", "%{NAME}\n"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self)s -> dict:
        return {
            "yq": "sudo zypper install yq",
            "timeshift": "sudo zypper install timeshift"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all openSUSE machines",
            "packages": [
                "patterns-base-base",
                "kernel-default",
                "NetworkManager",
                "vim",
                "git",
                "yq"
            ]
        }
