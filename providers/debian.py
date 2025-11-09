# providers/debian.py
import subprocess
import os
import shutil
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
NC = '\033[0m'

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
    
    def __init__(self):
        if not shutil.which("add-apt-repository"):
            print(f"{YELLOW}Warning: 'add-apt-repository' not found. PPAs will not work.{NC}")
            print("Please install 'software-properties-common'.")
            self.can_add_ppa = False
        else:
            self.can_add_ppa = True

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
        # <-- CHANGE: Added snapper -->
        return {
            "yq": "sudo apt install yq",
            "timeshift": "sudo apt install timeshift",
            "snapper": "sudo apt install snapper",
            "software-properties-common": "sudo apt install software-properties-common"
        }

    def get_base_packages(self) -> dict:
        # <-- CHANGE: Added timeshift (Debian/Ubuntu default) -->
        return {
            "description": "Base packages for all Debian-based machines",
            "packages": [
                "build-essential",
                "linux-image-generic",
                "network-manager",
                "vim",
                "git",
                "yq",
                "software-properties-common",
                "timeshift"
            ],
            "debian_ppa": {
                "ppa:lutris-team/lutris": ["lutris"]
            }
        }

    def install_ppa(self, ppa_map: dict) -> bool:
        if not self.can_add_ppa:
            print("Error: 'add-apt-repository' is not available. Cannot add PPAs.")
            return False

        all_ok = True
        all_packages = []
        needs_update = False
        
        for ppa, packages in ppa_map.items():
            # This is a simple check; a robust version would check /etc/apt/sources.list.d/
            ppa_file = Path(f"/etc/apt/sources.list.d/{ppa.split(':')[1].replace('/', '-')}.list")
            if not ppa_file.exists():
                print(f"Adding PPA: {ppa}")
                if not run_cmd(["sudo", "add-apt-repository", "-y", ppa]):
                    print(f"Warning: Failed to add PPA: {ppa}")
                    all_ok = False
                else:
                    needs_update = True
            
            all_packages.extend(packages)
        
        if needs_update:
            print("Running 'apt update' after adding PPAs...")
            if not run_cmd(["sudo", "apt", "update"]):
                print("Error: 'apt update' failed.")
                return False
        
        if all_packages:
            if not self.install(all_packages):
                all_ok = False
        return all_ok
