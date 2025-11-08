# sys-config

Declarative package management configuration for Linux.

## Structure

- `config.yaml` - Main configuration file
- `packages/base.yaml` - Base packages for all machines
- `packages/hosts/` - Host-specific package configurations
- `packages/modules/` - Optional package modules
- `scripts/` - Post-install hook scripts
- `state/` - Auto-generated state files (git-ignored)

## Usage

### Add base packages

Edit `packages/base.yaml` to add packages that should be installed on all machines.

### Add host-specific packages

Edit `packages/hosts/<your-hostname>.yaml` to add packages specific to this machine.

### Create and enable modules

1.  Create a new YAML file in `packages/modules/`
2.  Enable it with: `sys-sync module enable <module-name>`
3.  Sync packages: `sys-sync sync`

### Sync packages

```bash
sys-sync sync          # Preview and install missing packages
sys-sync sync --prune  # Also remove packages not in configuration

#### Git Integration 

cd ~/.config/sys-config
git init
git add .
git commit -m "Initial sys-config setup"
