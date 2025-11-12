Here is the updated `README.md` file for your `wcli` project.

It has been fully converted from the old `dcli` to match your new multi-distro Python tool, including the new helper-package syntax and the advanced version-pinning commands.

-----

# wcli

A declarative, multi-distro package management CLI for Linux, inspired by NixOS.

`wcli` provides a declarative YAML-based system to manage packages across multiple machines and distributions, including Fedora, Arch, Debian/Ubuntu, openSUSE, Gentoo, and Void.

## Features

  - **Multi-Distro Support**: Works as a wrapper for `dnf`, `apt`, `pacman`, `zypper`, `emerge`, and `xbps`.
  - **Declarative Package Management**: Define your packages in YAML files and `wcli sync` your system to match.
  - [cite\_start]**Advanced Helper Support**: Natively manages packages from **Flatpak**, **AUR**[cite: 508], **COPR**, **PPA**, **OBS**, **Gentoo Overlays**, and **xbps-src**.
  - [cite\_start]**Version Pinning**: Constrain packages to exact, minimum, or maximum versions [cite: 176, 215-219, 432-472].
  - [cite\_start]**Smart Updates**: `wcli update` automatically respects your pinned packages [cite: 173, 418-422].
  - [cite\_start]**Snapshot Integration**: Auto-detects and uses **Snapper** or **Timeshift** for automatic backups before changes[cite: 177, 501].
  - **Module System**: Organize packages into reusable modules (e.g., `gaming`, `development`).
  - **Host-Specific Configs**: Maintain different package sets for different machines.
  - [cite\_start]**Git Integration**: Built-in `repo` commands to sync your config across machines[cite: 178, 352].

## Installation

### Prerequisites

  - A supported Linux distribution (Fedora, Arch, Debian, openSUSE, etc.)
  - `python3`
  - `python3-yaml` (e.g., `sudo apt install python3-yaml` or `sudo dnf install python3-pyyaml`)
  - `git` (for `repo` commands)
  - **Optional:** `snapper` or `timeshift` for snapshot support.

### Install

The installer will ask for your `sudo` password to copy files.

```bash
# 1. Clone the repository
git clone https://your-repo-url/wcli.git
cd wcli

# 2. Run the installer
bash install.sh
```

The installer will:

1.  Detect your distro and ask to install `snapper` or `timeshift`.
2.  Create `/usr/local/lib/wcli/` and copy the `wcli` script and `providers/` package into it.
3.  Create a symlink from `/usr/local/bin/wcli` so you can run it from anywhere.

### Initialize Configuration

After installation, run the `init` command to create your config files:

```bash
wcli init
```

This creates `~/.config/wcli-config/` with:

  - `config.yaml`: Main configuration (with your hostname auto-detected).
  - `packages/base.yaml`: Base packages for your *specific* distribution.
  - `packages/hosts/{your-hostname}.yaml`: Host-specific packages.
  - `packages/modules/`: Optional package modules.
  - `scripts/`: For post-install hooks.
  - `state/`: Auto-generated state files (git-ignored).

#### Bootstrap (Optional)

[cite\_start]To start with a pre-made configuration, you can bootstrap from the original `dcli` config repo[cite: 338, 473]:

```bash
wcli init --bootstrap
```

This will clone the config, remove its git history, and set it up for you.

## Usage

### Package Management

```bash
[cite_start]wcli update                    # Update system, respecting version pins [cite: 173]
wcli search <package-name>     # Search native repos (and AUR on Arch)
wcli install <package>         # Install one or more packages
wcli remove <package>          # Remove one or more packages
```

### Declarative Management

```bash
[cite_start]wcli sync                       # Install/upgrade/downgrade to match config [cite: 174]
wcli sync --prune               # Also remove packages not in config
wcli sync --dry-run             # Show what would be changed
wcli sync --force               # Skip confirmation prompts
[cite_start]wcli sync --no-backup           # Skip snapshot creation [cite: 241]
```

### Module Management

```bash
wcli module list                # Show all available modules
wcli module enable <name>       # Enable a module in your config.yaml
wcli module disable <name>      # Disable a module
```

### Status

```bash
[cite_start]wcli status                     # Show config and see if you are in sync [cite: 175]
```

## Configuration Structure

`wcli` works by merging YAML files. You define *what* you want, and `wcli` figures out *how* to install it on your current distro.

### Example Module (with Helpers & Pinning)

Create `~/.config/wcli-config/packages/modules/gaming.yaml`:

```yaml
description: Gaming packages and tools

# 1. Official packages (works on all distros)
packages:
  - steam
  - gamemode
  # Version Pinning:
  - { name: wine, version: ">=9.0" } # Minimum version
  - { name: mangohud, version: "0.7.1-1" } # Exact version

# 2. Universal packages
flatpaks:
  - net.lutris.Lutris
  - com.heroicgameslauncher.hgl

# 3. Distro-specific helpers
arch_aur:
  - { name: proton-ge-custom }

debian_ppa:
  "ppa:graphics-drivers/ppa":
    - nvidia-driver-550

fedora_copr:
  "atim/heroic-games-launcher":
    - heroic-games-launcher
```

## Version Pinning

[cite\_start]You can control package versions directly in your YAML files [cite: 176, 215-219, 432-472].

  - **Latest:** `package-name`
  - **Exact:** `{ name: package-name, version: "1.2.3-1" }`
  - **Minimum:** `{ name: package-name, version: ">=1.2.0" }`

`wcli` provides commands to manage these pins in your `config.yaml`:

```bash
# Pin 'firefox' to its currently installed version
wcli pin firefox

# Pin 'python' to a specific version
wcli pin python 3.11.5

# Remove the pin and let 'firefox' update normally
wcli unpin firefox

# See installed, available, and cached versions
wcli versions firefox

# Check if any installed packages violate your pins
wcli outdated

# Create a lockfile of *all* installed packages
wcli lock
```

## Snapshot Management (Snapper & Timeshift)

`wcli` auto-detects `snapper` or `timeshift` and uses the best one available.

```bash
[cite_start]wcli backup --create              # Create a new snapshot [cite: 177]
wcli backup --list                # List all snapshots
wcli backup --restore             # Restore snapshot (interactive for Timeshift)
wcli backup --delete <ID>         # Delete a snapshot by ID/name
wcli backup --check               # Check snapshot integrity (Timeshift only)
```

## Repository Management (Git)

[cite\_start]Use these commands to sync your `~/.config/wcli-config` directory across multiple machines[cite: 178, 352].

### First Computer

```bash
# After running 'wcli init'
wcli repo init
# Now, add your remote manually
git remote add origin <your-git-repo-url>
wcli repo push
```

### Additional Computers

```bash
# After installing wcli
wcli repo clone --url <your-git-repo-url>

# Your config is ready. Run sync.
wcli sync
```

### Daily Workflow

```bash
# Push local changes (e.g., new module)
wcli repo push -m "Add development module"

# Pull changes from another machine
wcli repo pull

# See local changes
wcli repo status
```

## Troubleshooting

  - **`wcli: command not found`**: Your shell hasn't registered the new command. Run `hash -r` or restart your terminal.
  - **`Syntax error: "(" unexpected`**: You ran `sh wcli` instead of `bash install.sh`. Re-run the installer correctly.
  - **`Error: A provider module could not be imported`**: You ran `install.sh` from the wrong folder. It *must* be in the same directory as the `wcli` script and the `providers/` folder. Re-run the installation from the correct directory.
  - **`Error: PyYAML dependency not found`**: You need to install the Python YAML library.
      - `sudo apt install python3-yaml` (Debian/Ubuntu)
      - `sudo dnf install python3-pyyaml` (Fedora)
  - **PPA Fails (GPG Error / `dirmngr` not found)**: Your system is missing the PPA key manager.
      - Fix: `sudo apt install dirmngr` or add `dirmngr` to your `base.yaml` and run `wcli sync`.
  - **PPA Fails (No Release file)**: The PPA (e.g., Lutris) does not support your (probably new) version of Ubuntu. `wcli` correctly reports this error and skips the PPA. You must wait for the PPA to be updated or use a `flatpak:` entry instead.
