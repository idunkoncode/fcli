# providers/base_provider.py
from abc import ABC, abstractmethod
import subprocess
import shutil

# --- Add colors for warnings ---
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def _run_cmd_interactive(cmd: list) -> bool:
    """
    Helper to run an interactive command (like flatpak install)
    that streams output to the user.
    """
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Command cancelled.{NC}")
        return False

class BaseProvider(ABC):
    """
    Abstract base class defining the interface for all distro providers.
    """

    @abstractmethod
    def install(self, packages: list) -> bool:
        """Install a list of packages."""
        pass

    @abstractmethod
    def remove(self, packages: list) -> bool:
        """Remove a list of packages."""
        pass

    @abstractmethod
    def update(self, ignore_list: list) -> bool: # <-- CHANGED
        """Update all system packages, ignoring any in ignore_list."""
        pass

    @abstractmethod
    def search(self, package: str) -> bool:
        """Search for a package."""
        pass

    @abstractmethod
    def get_installed_packages(self) -> set:
        """Return a set of all installed package names."""
        pass

    @abstractmethod
    def get_deps(self) -> dict:
        """Return a dict of dependencies { 'yq': 'install_cmd', ... }."""
        pass

    @abstractmethod
    def get_base_packages(self) -> dict:
        """Return a dict of base packages for the 'init' command."""
        pass

    # --- NEW: Abstract methods for version pinning ---

    @abstractmethod
    def get_package_version(self, package: str) -> str:
        """Return the installed version string of a single package."""
        pass
    
    @abstractmethod
    def get_installed_packages_with_versions(self) -> dict:
        """Return a dict of {pkg_name: version} for all installed packages."""
        pass
    
    @abstractmethod
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.
        Returns: 1 if v1 > v2, 0 if v1 == v2, 2 if v1 < v2
        """
        pass
        
    @abstractmethod
    def show_package_versions(self, package: str):
        """Prints installed, available, and cached versions of a package."""
        pass

    # --- Optional Helper Methods ---
    
    def _unsupported(self, feature_name: str) -> bool:
        """Default function for unsupported features."""
        print(f"{YELLOW}Warning: {feature_name} packages are declared, but this system's provider ({self.__class__.__name__}) does not support them. Skipping.{NC}")
        return False

    # --- NEW: Optional downgrade method ---
    def downgrade(self, package: str, version: str) -> bool:
        print(f"{YELLOW}Warning: Downgrading is not explicitly supported by the {self.__class__.__name__} provider. Skipping {package}.{NC}")
        return False

    def install_aur(self, packages: list) -> bool: return self._unsupported("AUR")
    def install_copr(self, copr_map: dict) -> bool: return self._unsupported("COPR")
    def install_ppa(self, ppa_map: dict) -> bool: return self._unsupported("PPA")
    def install_obs(self, obs_map: dict) -> bool: return self._unsupported("OBS")
    def install_overlay(self, overlay_map: dict) -> bool: return self._unsupported("Gentoo Overlay")
    def install_src(self, packages: list) -> bool: return self._unsupported("Void Src")

    def install_flatpak(self, packages: list) -> bool:
        """
        Installs a list of Flatpaks.
        """
        if not shutil.which("flatpak"):
            print(f"{RED}Error: 'flatpak' command not found. Cannot install Flatpaks.{NC}")
            deps = self.get_deps()
            print(f"Please install it first: {deps.get('flatpak', 'sudo <your-package-manager> install flatpak')}")
            return False
        
        try:
            repo_list = subprocess.run(["flatpak", "remotes", "--columns=name"], capture_output=True, text=True, check=True).stdout
            if "flathub" not in repo_list:
                print(f"{YELLOW}Warning: 'flathub' remote not found. Adding it now...{NC}")
                if not _run_cmd_interactive(["sudo", "flatpak", "remote-add", "--if-not-exists", "flathub", "https://flathub.org/repo/flathub.flatpakrepo"]):
                    print(f"{RED}Error: Failed to add 'flathub' remote. Cannot install packages.{NC}")
                    return False
        except Exception as e:
            print(f"{RED}Error checking flatpak remotes: {e}{NC}")
            return False

        return _run_cmd_interactive(["sudo", "flatpak", "install", "-y", "--non-interactive", "flathub"] + packages)
