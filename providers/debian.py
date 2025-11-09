# providers/debian.py
import subprocess
import os
import shutil
from pathlib import Path
from .base_provider import BaseProvider

# <-- ADDED COLORS -->
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def _run_cmd_interactive(cmd: list) -> bool:
    """Helper to run an interactive subprocess command (like apt install)."""
    try:
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        subprocess.run(cmd, check=True, env=env)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def _run_cmd_capture(cmd: list) -> subprocess.CompletedProcess:
    """Helper to run a non-interactive command and capture output."""
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class Provider(BaseProvider):
    """Debian/Ubuntu provider implementation."""
    
    # <-- CHANGE: Updated __init__ to check for dirmngr -->
    def __init__(self):
        if not shutil.which("add-apt-repository"):
            print(f"{YELLOW}Warning: 'add-apt-repository' not found. PPAs will not work.{NC}")
            print("Please install 'software-properties-common'.")
            self.can_add_ppa = False
        else:
            self.can_add_ppa = True
            
        if not shutil.which("dirmngr"):
            print(f"{YELLOW}Warning: 'dirmngr' not found. PPA key imports may fail.{NC}")
            print("Please install 'dirmngr'.")
            self.can_import_keys = False
        else:
            self.can_import_keys = True

    def install(self, packages: list) -> bool:
        return _run_cmd_interactive(["sudo", "apt", "install", "-y"] + packages)

    def remove(self, packages: list) -> bool:
        return _run_cmd_interactive(["sudo", "apt", "remove", "-y"] + packages)

    def update(self) -> bool:
        _run_cmd_interactive(["sudo", "apt", "update"])
        return _run_cmd_interactive(["sudo", "apt", "upgrade", "-y"])

    def search(self, package: str) -> bool:
        return _run_cmd_interactive(["apt", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f", "${binary:Package}\n"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    # <-- CHANGE: Added dirmngr to deps -->
    def get_deps(self) -> dict:
        return {
            "yq": "sudo apt install yq",
            "timeshift": "sudo apt install timeshift",
            "snapper": "sudo apt install snapper",
            "software-properties-common": "sudo apt install software-properties-common",
            "dirmngr": "sudo apt install dirmngr"
        }

    # <-- CHANGE: Added dirmngr to base packages -->
    def get_base_packages(self) -> dict:
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
                "dirmngr", # <-- This is the key fix
                "timeshift"
            ],
            "debian_ppa": {
                "ppa:lutris-team/lutris": ["lutris"]
            }
        }

    # <-- CHANGE: Updated PPA logic to check for dirmngr -->
    def install_ppa(self, ppa_map: dict) -> bool:
        if not self.can_add_ppa:
            print(f"{RED}Error: 'add-apt-repository' is not available. Cannot add PPAs.{NC}")
            return False
        
        # <-- NEW: Check for dirmngr before starting -->
        if not self.can_import_keys:
            print(f"{RED}Error: 'dirmngr' is not installed. Cannot import PPA GPG keys.{NC}")
            print(f"{YELLOW}Please run 'sudo apt install dirmngr' or add 'dirmngr' to your 'base.yaml' and run 'wcli sync' first.{NC}")
            return False

        all_ok = True
        all_packages_to_install = []
        needs_update = False
        
        for ppa, packages in ppa_map.items():
            print(f"Checking PPA: {ppa}...")
            proc = _run_cmd_capture(["sudo", "add-apt-repository", "-y", ppa])
            
            if proc.returncode != 0:
                print(f"{RED}Error: Failed to add PPA: {ppa}{NC}")
                print(f"{YELLOW}STDERR: {proc.stderr}{NC}")
                all_ok = False
            else:
                all_packages_to_install.extend(packages)
                if "already-enabled" not in proc.stdout and "already enabled" not in proc.stdout:
                    print(f"Successfully added PPA: {ppa}")
                    needs_update = True
                else:
                    print(f"PPA {ppa} is already enabled.")

        
        if needs_update:
            print("Running 'apt update' after adding new PPAs...")
            if not _run_cmd_interactive(["sudo", "apt", "update"]):
                print(f"{RED}Error: 'apt update' failed. Stopping PPA install.{NC}")
                return False
        
        if all_packages_to_install:
            print(f"Installing packages from PPAs: {', '.join(all_packages_to_install)}")
            if not self.install(all_packages_to_install):
                all_ok = False
                
        return all_ok
