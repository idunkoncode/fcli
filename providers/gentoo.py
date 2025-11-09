# providers/gentoo.py
import subprocess
import shutil
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
NC = '\033[0m'

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """Gentoo provider implementation."""

    def __init__(self):
        if not shutil.which("eselect"):
            print(f"{YELLOW}Warning: 'eselect' not found. Overlays will not work.{NC}")
            print("Please install 'app-eselect/eselect-repository'.")
            self.can_add_overlay = False
        else:
            self.can_add_overlay = True

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "emerge", "--noreplace", "--verbose"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "emerge", "-C", "--verbose"] + packages)

    def update(self) -> bool:
        run_cmd(["sudo", "emerge", "--sync"])
        return run_cmd(["sudo", "emerge", "-auDN", "@world"])

    def search(self, package: str) -> bool:
        return run_cmd(["emerge", "-s", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["qlist", "-I"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            packages = set()
            for line in result.stdout.strip().split('\n'):
                if '/' in line:
                    packages.add(line.split('/')[-1])
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: 'qlist' command not found. 'get_installed_packages' will fail.")
            print("Please install 'app-portage/portage-utils'")
            return set()

    def get_deps(self) -> dict:
        # <-- CHANGE: Added snapper -->
        return {
            "yq": "sudo emerge app-misc/yq",
            "timeshift": "sudo emerge app-backup/timeshift",
            "snapper": "sudo emerge sys-fs/snapper",
            "portage-utils": "sudo emerge app-portage/portage-utils",
            "eselect-repository": "sudo emerge app-eselect/eselect-repository"
        }

    def get_base_packages(self) -> dict:
        # <-- CHANGE: Added snapper (Gentoo/Btrfs default) -->
        return {
            "description": "Base packages for all Gentoo machines",
            "packages": [
                "app-portage/portage-utils", 
                "app-eselect/eselect-repository", 
                "app-misc/yq",
                "net-misc/networkmanager",
                "app-editors/vim",
                "dev-vcs/git",
                "sys-fs/snapper"
            ],
            "gentoo_overlay": {
                "guru": []
            }
        }

    def install_overlay(self, overlay_map: dict) -> bool:
        if not self.can_add_overlay:
            print("Error: 'eselect repository' is not available. Cannot add overlays.")
            return False

        all_ok = True
        all_packages = []
        needs_sync = False
        
        try:
            result = subprocess.run(["eselect", "repository", "list", "-i"], capture_output=True, text=True, check=True)
            enabled_repos = result.stdout
        except Exception:
            enabled_repos = ""

        for overlay, packages in overlay_map.items():
            if overlay not in enabled_repos:
                print(f"Adding Gentoo overlay: {overlay}")
                if not run_cmd(["sudo", "eselect", "repository", "add", overlay, "git"]):
                    print(f"Warning: Failed to add overlay: {overlay}")
                    all_ok = False
                else:
                    needs_sync = True
            
            all_packages.extend(packages)
        
        if needs_sync:
            print("Running 'emerge --sync' after adding overlays...")
            if not run_cmd(["sudo", "emerge", "--sync"]):
                print("Error: 'emerge --sync' failed.")
                return False
        
        if all_packages:
            if not self.install(all_packages):
                all_ok = False
        return all_ok
