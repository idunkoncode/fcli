# providers/fedora.py
import subprocess
from .base_provider import BaseProvider

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        # Use subprocess.run directly for output streaming
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """Fedora provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "dnf", "install", "-y"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "dnf", "remove", "-y"] + packages)

    def update(self) -> bool:
        return run_cmd(["sudo", "dnf", "update", "-y"])

    def search(self, package: str) -> bool:
        return run_cmd(["dnf", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["rpm", "-qa", "--qf", "%{NAME}\n"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        # <-- CHANGE: Added snapper -->
        return {
            "yq": "sudo dnf install yq",
            "timeshift": "sudo dnf install timeshift",
            "snapper": "sudo dnf install snapper"
        }

    def get_base_packages(self) -> dict:
        # <-- CHANGE: Added snapper (Fedora default) -->
        return {
            "description": "Base packages for all Fedora machines",
            "packages": [
                "@core",
                "kernel",
                "linux-firmware",
                "NetworkManager",
                "vim-enhanced",
                "git",
                "yq",
                "snapper"
            ],
            "fedora_copr": {
                "atim/heroic-games-launcher": ["heroic-games-launcher"]
            }
        }

    def install_copr(self, copr_map: dict) -> bool:
        all_ok = True
        all_packages = []
        for repo, packages in copr_map.items():
            if not run_cmd(["sudo", "dnf", "copr", "enable", "-y", repo]):
                print(f"Warning: Failed to enable COPR repo: {repo}")
                all_ok = False
            else:
                all_packages.extend(packages)
        
        if all_packages:
            if not self.install(all_packages):
                all_ok = False
        return all_ok
