# providers/void.py
import subprocess
import shutil
from pathlib import Path
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
NC = '\033[0m'

def run_cmd(cmd: list, cwd: Path = None) -> bool:
    """Helper to run a subprocess command."""
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

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
        return run_cmd(["sudo", "xbps-install", "-y"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "xbps-remove", "-y"] + packages)

    def update(self) -> bool:
        return run_cmd(["sudo", "xbps-install", "-Syu"])

    def search(self, package: str) -> bool:
        return run_cmd(["xbps-query", "-Rs", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["xbps-query", "-l"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            packages = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    pkg_full = line.split(' ')[1]
                    pkg_name = pkg_full.rsplit('-', 2)[0]
                    packages.add(pkg_name)
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        # <-- CHANGE: Added snapper -->
        return {
            "yq": "sudo xbps-install -y yq",
            "timeshift": "sudo xbps-install -y timeshift",
            "snapper": "sudo xbps-install -y snapper",
            "xtools": "sudo xbps-install -y xtools"
        }

    def get_base_packages(self) -> dict:
        # <-- CHANGE: Added timeshift (Void default) -->
        return {
            "description": "Base packages for all Void machines",
            "packages": [
                "NetworkManager",
                "vim",
                "git",
                "yq",
                "xtools", # For xbps-src
                "timeshift"
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
