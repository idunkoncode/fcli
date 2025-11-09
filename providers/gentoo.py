
# providers/gentoo.py
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
    """Gentoo provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "emerge", "--noreplace"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "emerge", "-C"] + packages)

    def update(self) -> bool:
        return run_cmd(["sudo", "emerge", "-auDN", "@world"])

    def search(self, package: str) -> bool:
        return run_cmd(["emerge", "-s", package])

    def get_installed_packages(self) -> set:
        try:
            # Requires app-portage/portage-utils
            result = subprocess.run(
                ["qlist", "-I"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            # qlist output is 'category/name', we only want 'name'
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
        return {
            "yq": "sudo emerge app-misc/yq",
            "timeshift": "sudo emerge app-backup/timeshift",
            "portage-utils": "sudo emerge app-portage/portage-utils"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Gentoo machines",
            "packages": [
                "app-portage/portage-utils", # For qlist
                "app-misc/yq",
                "net-misc/networkmanager",
                "app-editors/vim",
                "dev-vcs/git"
            ]
        }
