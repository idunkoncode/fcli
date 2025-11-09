# providers/arch.py
import subprocess
import shutil
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
NC = '\033[0m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """Arch Linux provider implementation."""

    def __init__(self):
        self.helper_cmd = None
        if shutil.which("paru"):
            self.helper_cmd = "paru"
        elif shutil.which("yay"):
            self.helper_cmd = "yay"
        else:
            print(f"{YELLOW}Warning: No AUR helper (paru, yay) found. 'arch_aur' packages will be skipped.{NC}")

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "pacman", "-S", "--noconfirm", "--needed"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "pacman", "-Rs", "--noconfirm"] + packages)

    def update(self) -> bool:
        if self.helper_cmd:
            print(f"Note: 'update' uses '{self.helper_cmd}'.")
            return run_cmd([self.helper_cmd, "-Syu", "--noconfirm"])
        else:
            print("Note: No AUR helper found. Only running pacman.")
            return run_cmd(["sudo", "pacman", "-Syu", "--noconfirm"])

    def search(self, package: str) -> bool:
        if self.helper_cmd:
            print(f"Note: 'search' uses '{self.helper_cmd}'.")
            return run_cmd([self.helper_cmd, "-Ss", package])
        else:
            print("Note: No AUR helper found. Only running pacman.")
            return run_cmd(["pacman", "-Ss", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["pacman", "-Qq"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        # <-- CHANGE: Added snapper -->
        return {
            "yq": "sudo pacman -S go-yq",
            "timeshift": "sudo pacman -S timeshift",
            "snapper": "sudo pacman -S snapper",
            "paru": "(Install 'paru' or 'yay' from the AUR)"
        }

    def get_base_packages(self) -> dict:
        # <-- CHANGE: Added timeshift (common Arch default) -->
        return {
            "description": "Base packages for all Arch machines",
            "packages": [
                "base",
                "linux",
                "linux-firmware",
                "networkmanager",
                "vim",
                "git",
                "go-yq",
                "timeshift"
            ],
            "arch_aur": [
                "paru" 
            ]
        }

    def install_aur(self, packages: list) -> bool:
        if not self.helper_cmd:
            print(f"{RED}Error: No AUR helper found. Cannot install packages.{NC}")
            return False
        
        print(f"{BLUE}Using '{self.helper_cmd}' to install AUR packages...{NC}")
        return run_cmd([self.helper_cmd, "-S", "--noconfirm", "--needed"] + packages)
