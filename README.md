



Wcli

A declarative package management CLI tool for Linux, inspired by NixOS. Supports Fedora, Arch, Debian/Ubuntu, openSUSE, Gentoo, and Void.

Features

*** Declarative Package Management: Define your packages in YAML files and sync your system to match.

*** Module System: Organize packages into reusable modules (gaming, development, etc.).

*** Host-Specific Configurations: Maintain different package sets per machine.

*** Automatic Backups: Integrates with Timeshift for automatic snapshots before changes.
    
*** Conflict Detection: Prevents enabling conflicting modules.

*** Post-Install Hooks: (Future feature) Run scripts after package installation.
    
*** Package Management Shortcuts: Quick wrappers around native package managers (dnf, apt, pacman, etc.).

Installation

Prerequisites

* A supported Linux distribution (Fedora, Arch, Debian, openSUSE, Gentoo, Void)
    
* python3
     
* python3-yaml (or pip install pyyaml)
    
* git (for repository management)
     
* timeshift (optional, for backup functionality)
  
Install
    
    # Clone the repository (or download the files)
    git clone https://.../your-wcli-project.git
    cd wcli-project
    ./install.sh

The installer will:

    Create /usr/local/lib/wcli/ (requires sudo)
    Copy the wcli executable and the providers/ package into it
    Symlink wcli to /usr/local/bin/wcli for system-wide access
    Verify the installation

Initialize Configuration
After installation, initialize your configuration directory:
    
    Bash
    wcli init

Declarative Package Management

Define Base Packages
    
*** Edit ~/.config/wcli-config/packages/base.yaml. The wcli init command will have already pre-filled this with ensible defaults for your OS.

Define Host-Specific Packages
    
***Edit ~/.config/wcli-config/packages/hosts/{hostname}.yaml:

    YAML
    # Packages specific to this machine
    description: Packages specific to my-laptop
    packages:
      - tlp
      - powertop
    exclude: []

Create Modules

Create ~/.config/wcli-config/packages/modules/gaming.yaml:

    YAML
    # Gaming packages and tools
    description: Gaming packages and tools

    packages:
      - steam
      - lutris
      - wine
      - gamemode

    conflicts: []
    post_install_hook: ""

Enable/Disable Modules

    Bash

    wcli module list                # Show all modules and their status
    wcli module enable gaming       # Enable gaming module
    wcli module disable gaming      # Disable gaming module

Sync Packages

    Bash

    wcli sync                       # Preview and install missing packages
    wcli sync --dry-run             # Show what would be installed/removed
    wcli sync --prune               # Also remove packages not in config
    wcli sync --force               # Skip confirmation prompts
    wcli sync --no-backup           # Skip Timeshift backup

Check Status

    Bash

    wcli status                     # Show configuration and sync status

Timeshift Backup Commands

    Bash

    wcli backup --create              # Create snapshot
    wcli backup --list                # List snapshots
    wcli backup --restore             # Restore snapshot (interactive)
    wcli backup --restore --snapshot <snapshot> # Restore specific snapshot
    wcli backup --delete <snapshot>   # Delete snapshot
    wcli backup --check               # Check snapshot integrity

Module System

Modules allow you to organize packages by purpose and enable/disable them as needed.

Module Structure

    YAML

    # Module description
    description: Module description

    # List of packages
    packages:
      - package1
      - package2

    # Conflicting modules
    conflicts:
      - other-module

    # Optional post-install script (relative to config dir)
    post_install_hook: scripts/my-setup.sh

Conflict Detection
If two modules conflict (e.g., different window managers), wcli will:

    1. Detect the conflict when enabling
    2. Prompt to disable the conflicting module
    3. Prevent both from being enabled simultaneously

Repository Management

wcli includes built-in git commands to make managing your configuration across multiple computers easy.

First Computer Setup

After running wcli init, set up version control:

    Bash
    wcli repo init

    This will:
    * Initialize a git repository in ~/.config/wcli-config/
    * Create a .gitignore to ignore your local config.yaml and state/
    * Make an initial commit.
    * You can then add your remote: git remote add origin <your-git-repo-url>

Additional Computer Setup

On your second computer, after installing wcli:
    
    Bash
    wcli repo clone --url <your-git-repo-url>

This will:

    Clone your wcli-config repository to ~/.config/wcli-config
    It's now ready to use. Run wcli sync.

Syncing Changes

Push your changes: (After enabling/disabling modules or editing package files)

    Bash
    # Commit and push with a default message
    wcli repo push

    # Add a custom message
    wcli repo push -m "Added development module"

Pull updates from other machines:

    Bash
    wcli repo pull

Check status:

    Bash
    wcli repo status

Multi-Machine Workflow

Scenario: Add a new module on your desktop, use it on your laptop

On desktop:

    Bash
    # Create and enable a new module
    vim ~/.config/wcli-config/packages/modules/development.yaml
    wcli module enable development
    wcli sync

    # Push changes
    wcli repo push -m "Add development module"

On laptop:

    Bash
    # Pull the changes
    wcli repo pull

    # Enable the module and install
    wcli module enable development
    wcli sync

Repository Structure

Your repository will look like this:

    my-wcli-config/
    ├── .gitignore              # config.yaml is auto-ignored
    ├── packages/
    │   ├── base.yaml          # Shared across all machines
    │   ├── modules/           # Shared modules
    │   │   ├── gaming.yaml
    │   │   ├── development.yaml
    │   │   └── ...
    │   └── hosts/             # Machine-specific configs
    │       ├── desktop.yaml   # Your desktop config
    │       └── laptop.yaml    # Your laptop config  
    ├── scripts/               # Shared scripts
    └── README.md

Each machine maintains its own config.yaml (git-ignored) with the correct hostname and enabled modules.
Advanced Usage

Environment Variables

    SYS_CONFIG_DIR - Override the default config location (~/.config/wcli-config)
    Bash
    SYS_CONFIG_DIR=/custom/path wcli sync

Example Workflows

Setting up a new gaming machine

    Bash
    # Install wcli
    git clone https://.../your-wcli-project.git
    cd wcli-project
    ./install.sh

    # Initialize configuration
    wcli init

    # Enable gaming modules
    wcli module enable gaming

    # Sync system
    wcli sync

Maintaining multiple machines

    Bash
    # On first machine, after 'wcli init'
    cd ~/.config/wcli-config
    wcli repo init
    git remote add origin git@gitlab.com:yourname/wcli-config.git
    wcli repo push

    # On second machine (after installing wcli)
    wcli repo clone --url git@gitlab.com:yourname/wcli-config.git
    wcli sync

Troubleshooting

wcli: command not found

Your shell might have cached the command. Try:
Bash

hash -r  # Refresh shell's command cache

Or restart your terminal.

Sync fails with package conflicts

This can happen if two packages provide the same file. Use your native package manager to resolve the conflict manually, then run wcli sync again.

Missing PyYAML dependency

wcli requires the python3-yaml library.
    
    Bash
    # For Debian/Ubuntu
    sudo apt install python3-yaml

    # For Fedora
    sudo dnf install python3-pyyaml

    # Or with pip
    pip install pyyaml

Architecture

    Base packages: Installed on all machines (packages/base.yaml)
    Host-specific packages: Unique to each machine (packages/hosts/{hostname}.yaml)
    Modules: Optional package sets (packages/modules/*.yaml)
    Additional packages: Ad-hoc packages in config.yaml
    Exclusions: Host-specific package exclusions

Priority order:

    1. Load base packages

    2. Load host-specific packages (and exclusions)

    3. Load enabled module packages

    4. Load additional packages from config.yaml

    5. Apply exclusions


Uninstalling is simple. The `install.sh` script copied the files to `/usr/local/lib/wcli` and created a symbolic link in `/usr/local/bin/`.

You just need to remove those two things.

### 1\. Remove the Program Files

Run these two commands to remove the `wcli` executable and its `providers` package:

    bash
    # 1. Remove the symbolic link from your PATH
    sudo rm /usr/local/bin/wcli

    # 2. Remove the actual program directory
    sudo rm -rf /usr/local/lib/wcli
    ```

The program is now uninstalled.

### 2\. (Optional) Remove Your Config Files

The program also created a configuration directory in your home folder when you ran `wcli init`. This is kept separate so you don't lose your configs when you update.

If you want to remove your personal configuration as well, run this command (**this will delete all your YAML files**):

    bash
    rm -rf ~/.config/wcli-config
    ```
License

MIT License - feel free to use and modify as needed.
