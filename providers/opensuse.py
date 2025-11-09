# providers/opensuse.py
import subprocess
import hashlib
from .base_provider import BaseProvider

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """openSUSE provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "zypper", "install", "--non-interactive", "--no-recommends"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "zypper", "remove", "--non-interactive"] + packages)

    def update(self) -> bool:
        # 'dup' is standard for Tumbleweed, 'up' for Leap. 'dup' is safer.
        return run_cmd(["sudo", "zypper", "dup", "--non-interactive", "--no-recommends"])

    def search(self, package: str) -> bool:
        return run_cmd(["zypper", "search", package])

    def get_installed_packages(self) -> set:
        try:
            # Same as Fedora, uses rpm
            result = subprocess.run(
                ["rpm", "-qa", "--qf", "%{NAME}\n"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        return {
            "yq": "sudo zypper install yq",
            "timeshift": "sudo zypper install timeshift"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all openSUSE machines",
            "packages": [
                "patterns-base-base",
                "kernel-default",
                "NetworkManager",
                "vim",
                "git",
                "yq"
            ]
        }

    # --- NEW: OBS Helper Function ---
    def install_obs(self, obs_map: dict) -> bool:
        all_ok = True
        all_packages = []
        
        # Get list of existing repo aliases
        try:
            result = subprocess.run(["zypper", "lr", "-a"], capture_output=True, text=True, check=True)
            existing_repos = result.stdout
        except Exception:
            existing_repos = ""

        for repo_url, packages in obs_map.items():
            # Create a unique, stable alias for the repo
            alias = f"wcli-obs-{hashlib.md5(repo_url.encode()).hexdigest()[:8]}"
            
            if alias not in existing_repos:
                print(f"Adding OBS repo: {repo_url}")
                if not run_cmd(["sudo", "zypper", "addrepo", "--refresh", "--name", alias, repo_url, alias]):
                    print(f"Warning: Failed to add OBS repo: {repo_url}")
                    all_ok = False
                else:
                    # Trust keys from new repos
                    run_cmd(["sudo", "zypper", "--gpg-auto-import-keys", "refresh"])
            
            all_packages.extend(packages)
        
        if all_packages:
            # Install packages, allowing vendor change
            if not run_cmd(["sudo", "zypper", "install", "--non-interactive", "--no-recommends", "--allow-vendor-change"] + all_packages):
                all_ok = False
        return all_ok
