# providers/void.py
import subprocess
import shutil
import re
from pathlib import Path
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
NC = '\033[0m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'

def run_cmd(cmd: list, cwd: Path = None) -> bool:
    """Helper to run an interactive command."""
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
        
def run_cmd_capture(cmd: list) -> subprocess.CompletedProcess:
    """Helper to run a non-interactive command and capture output."""
    return subprocess.run(cmd, check=True, text=True, capture_output=True, errors='ignore')

class Provider(BaseProvider):
    """Void Linux provider implementation."""
    
    def __init__(self):
        self.src_repo_path = Path.home() / "void-packages"
        if not shutil.which("xbps-src"):
             print(f"{YELLOW}Warning: 'xbps-src' not found. 'void_src' packages will not work.{NC}")
             print("Please install 'xtools' and clone the void-packages git repo.")
             self.can_build_src = False
        else:
             self.can_build_src = True

    def install(self, packages: list) -> bool:
        """Installs packages one-by-one to show progress."""
        all_ok = True
        total = len(packages)
        for i, pkg in enumerate(packages):
            # xbps-install can take version strings like 'package>=1.0'
            pkg_name = pkg.replace("==", "-").replace("=", "")
            print(f"\n--- Installing {pkg_name} ({i+1}/{total}) ---")
            if not run_cmd(["sudo", "xbps-install", "-y", pkg_name]):
                print(f"{YELLOW}Warning: Failed to install {pkg_name}{NC}")
                all_ok = False
        return all_ok

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "xbps-remove", "-y"] + packages)

    def update(self, ignore_list: list) -> bool:
        cmd = ["sudo", "xbps-install", "-Syu"]
        if ignore_list:
            print(f"{YELLOW}Ignoring {len(ignore_list)} packages: {', '.join(ignore_list)}{NC}")
            for pkg in ignore_list:
                cmd.append(f"--exclude={pkg}")
        return run_cmd(cmd)

    def search(self, package: str) -> bool:
        return run_cmd(["xbps-query", "-Rs", package])

    def get_installed_packages(self) -> set:
        try:
            result = run_cmd_capture(["xbps-query", "-l"])
            packages = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    pkg_full = line.split(' ')[1]
                    pkg_name = pkg_full.rsplit('-', 2)[0]
                    packages.add(pkg_name)
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    # --- NEW: Version Pinning Methods ---
    
    def get_package_version(self, package: str) -> str:
        try:
            result = run_cmd_capture(["xbps-query", "-p", "version", package])
            return result.stdout.strip().split('-')[0] # 'version_rev' -> 'version'
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def get_installed_packages_with_versions(self) -> dict:
        pkg_map = {}
        try:
            result = run_cmd_capture(["xbps-query", "-l"])
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        pkg_full = line.split(' ')[1]
                        pkg_name = pkg_full.rsplit('-', 2)[0]
                        version = pkg_full.rsplit('-', 2)[1]
                        pkg_map[pkg_name] = version
                    except (ValueError, IndexError):
                        pass
            return pkg_map
        except (subprocess.CalledProcessError, FileNotFoundError):
            return pkg_map
            
    def compare_versions(self, v1: str, v2: str) -> int:
        try:
            # xbps-uhelper version-cmp v1 v2
            proc = subprocess.run(["xbps-uhelper", "version-cmp", v1, v2], capture_output=True, text=True)
            result = proc.returncode
            if result == 1: return 1 # v1 > v2
            if result == 2: return 2 # v1 < v2
            return 0 # v1 == v2
        except FileNotFoundError:
            # Fallback for simple string compare
            if v1 > v2: return 1
            if v1 < v2: return 2
            return 0
            
    def downgrade(self, package: str, version: str) -> bool:
        """Downgrading on Void requires xdowngrade or manual intervention."""
        print(f"  {YELLOW}Downgrading on Void is not supported automatically.{NC}")
        print(f"  Please use 'xdowngrade' or install {package}-{version} manually.")
        return False

    def show_package_versions(self, package: str):
        # 2. Repo version
        try:
            result = run_cmd_capture(["xbps-query", "-Rs", package])
            repo_ver = re.search(r"version:\s*(.*)", result.stdout).group(1)
            print(f"  {BLUE}Available:{NC} {repo_ver.strip()}")
        except (subprocess.CalledProcessError, AttributeError):
            print(f"  {YELLOW}Not found in repositories{NC}")
        # 3. Cached versions
        print(f"  {BLUE}In Cache:{NC} (check /var/cache/xbps)")
        
    # --- End of Versioning Methods ---

    def get_deps(self) -> dict:
        return {
            "yq": "sudo xbps-install -y yq",
            "timeshift": "sudo xbps-install -y timeshift",
            "snapper": "sudo xbps-install -y snapper",
            "flatpak": "sudo xbps-install -y flatpak",
            "xtools": "sudo xbps-install -y xtools"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Void machines",
            "packages": [
                "NetworkManager",
                "vim",
                "git",
                "yq",
                "xtools",
                "timeshift",
                "flatpak"
            ],
            "void_src": [
                "heroic"
            ]
        }

    def install_src(self, packages: list) -> bool:
        if not self.can_build_src:
            print("Error: 'xbps-src' not found. Cannot build from source.")
            return False
            
        if not self.src_repo_path.exists():
            print(f"Void packages repo not found at {self.src_repo_path}")
            print("Cloning 'void-packages' from GitHub...")
            if not run_cmd(["git", "clone", "https://github.com/void-linux/void-packages.git", str(self.src_repo_path)]):
                print("Error: Failed to clone void-packages repo.")
                return False
        
        print("Updating void-packages repo...")
        if not run_cmd(["git", "pull", "origin", "master"], cwd=self.src_repo_path):
            print("Warning: 'git pull' failed, proceeding anyway...")
        
        if not run_cmd(["./xbps-src", "bootstrap-update"], cwd=self.src_repo_path):
            print("Error: './xbps-src bootstrap-update' failed.")
            return False
            
        all_ok = True
        for pkg in packages:
            print(f"Building {pkg} from source...")
            if not run_cmd(["./xbps-src", "pkg", pkg], cwd=self.src_repo_path):
                print(f"Warning: Failed to build {pkg}")
                all_ok = False
        
        print("Installing built packages...")
        repo_path = self.src_repo_path / "host/binpkgs"
        if not run_cmd(["sudo", "xbps-install", f"--repository={repo_path}", "-y"] + packages):
             print("Warning: Some packages may not have installed.")
             all_ok = False
             
        return all_ok
