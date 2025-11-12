# providers/debian.py
import subprocess
import os
import shutil
import re
from pathlib import Path
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'

def _run_cmd_interactive(cmd: list) -> bool:
    """Helper to run an interactive subprocess command (like apt install)."""
    try:
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        subprocess.run(cmd, check=True, env=env)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Command cancelled.{NC}")
        return False

def _run_cmd_capture(cmd: list) -> subprocess.CompletedProcess:
    """Helper to run a non-interactive command and capture output."""
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    return subprocess.run(cmd, capture_output=True, text=True, env=env, errors='ignore')


class Provider(BaseProvider):
    """Debian/Ubuntu provider implementation."""
    
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
            
        if not shutil.which("dpkg"):
            print(f"{RED}Error: 'dpkg' not found. This provider cannot function.{NC}")
            self.can_compare = False
        else:
            self.can_compare = True

    def install(self, packages: list) -> bool:
        """Installs packages one-by-one to show progress."""
        all_ok = True
        total = len(packages)
        for i, pkg in enumerate(packages):
            print(f"\n--- Installing {pkg} ({i+1}/{total}) ---")
            if not _run_cmd_interactive(["sudo", "apt", "install", "-y", pkg]):
                print(f"{YELLOW}Warning: Failed to install {pkg}{NC}")
                all_ok = False
        return all_ok

    def remove(self, packages: list) -> bool:
        return _run_cmd_interactive(["sudo", "apt", "remove", "-y"] + packages)

    def update(self, ignore_list: list) -> bool:
        """Updates packages, respecting holds."""
        if ignore_list:
            print(f"{YELLOW}Holding {len(ignore_list)} packages: {', '.join(ignore_list)}{NC}")
            if not _run_cmd_interactive(["sudo", "apt-mark", "hold"] + ignore_list):
                print(f"{RED}Error setting package holds.{NC}")
                return False
        
        print(f"{BLUE}Running apt update...{NC}")
        _run_cmd_interactive(["sudo", "apt", "update"])
        
        print(f"{BLUE}Running apt upgrade...{NC}")
        all_ok = _run_cmd_interactive(["sudo", "apt", "upgrade", "-y"])
        
        if ignore_list:
            print(f"{YELLOW}Un-holding {len(ignore_list)} packages...{NC}")
            if not _run_cmd_interactive(["sudo", "apt-mark", "unhold"] + ignore_list):
                print(f"{RED}Error removing package holds.{NC}")
                all_ok = False
        
        return all_ok

    def search(self, package: str) -> bool:
        return _run_cmd_interactive(["apt", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = _run_cmd_capture(["dpkg-query", "-W", "-f", "${binary:Package}\n"])
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()
            
    # --- NEW: Version Pinning Methods ---
    
    def get_package_version(self, package: str) -> str:
        try:
            result = _run_cmd_capture(["dpkg-query", "-W", "-f", "${Version}", package])
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def get_installed_packages_with_versions(self) -> dict:
        pkg_map = {}
        try:
            result = _run_cmd_capture(["dpkg-query", "-W", "-f", "${binary:Package}\t${Version}\n"])
            for line in result.stdout.strip().split('\n'):
                if line and '\t' in line:
                    try:
                        name, version = line.split('\t')
                        pkg_map[name] = version
                    except ValueError:
                        pass
            return pkg_map
        except (subprocess.CalledProcessError, FileNotFoundError):
            return pkg_map
            
    def compare_versions(self, v1: str, v2: str) -> int:
        if not self.can_compare: return 0
        try:
            # dpkg --compare-versions <v1> <op> <v2>
            # Returns 0 for true, 1 for false.
            if _run_cmd_capture(["dpkg", "--compare-versions", v1, "gt", v2]).returncode == 0:
                return 1
            if _run_cmd_capture(["dpkg", "--compare-versions", v1, "lt", v2]).returncode == 0:
                return 2
            return 0 # They must be equal
        except Exception:
            return 0 # Failsafe
            
    def downgrade(self, package: str, version: str) -> bool:
        """Downgrades a package to a specific version."""
        print(f"  {BLUE}Attempting to install {package}={version}...{NC}")
        # apt install <pkg=version> is the standard way
        if not _run_cmd_interactive(["sudo", "apt", "install", "-y", f"{package}={version}"]):
            print(f"  {YELLOW}Could not install {package}={version}. It may not be available in your repos.{NC}")
            return False
        return True

    def show_package_versions(self, package: str):
        # 2. Repo version
        try:
            result = _run_cmd_capture(["apt", "policy", package])
            # Look for "Candidate:"
            repo_ver = re.search(r"Candidate:\s*(.*)", result.stdout).group(1)
            print(f"  {BLUE}Available:{NC} {repo_ver.strip()}")
        except (subprocess.CalledProcessError, AttributeError):
            print(f"  {YELLOW}Not found in repositories{NC}")
        # 3. Cached versions (not easily queryable like pacman)
        print(f"  {BLUE}In Cache:{NC} (Run 'apt-cache policy {package}' for details)")
        
    # --- End of Versioning Methods ---

    def get_deps(self) -> dict:
        return {
            "yq": "sudo apt install yq",
            "timeshift": "sudo apt install timeshift",
            "snapper": "sudo apt install snapper",
            "flatpak": "sudo apt install flatpak",
            "software-properties-common": "sudo apt install software-properties-common",
            "dirmngr": "sudo apt install dirmngr"
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
                "yq",
                "software-properties-common",
                "dirmngr",
                "timeshift",
                "flatpak"
            ],
            "debian_ppa": {
                "ppa:lutris-team/lutris": ["lutris"]
            }
        }

    def install_ppa(self, ppa_map: dict) -> bool:
        if not self.can_add_ppa:
            print(f"{RED}Error: 'add-apt-repository' is not available. Cannot add PPAs.{NC}")
            return False
        
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
            print(f"Installing packages from PPAs...")
            # Install one-by-one to give feedback
            if not self.install(all_packages_to_install):
                all_ok = False
                
        return all_ok
