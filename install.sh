#!/usr/bin/env bash
# wcli Python version installation script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Install location
INSTALL_DIR="/usr/local/lib/wcli"
BIN_DIR="/usr/local/bin"
SCRIPT_NAME="wcli"
PACKAGE_NAME="providers"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- NEW: Distro-Specific Install Commands ---
DISTRO_ID=""
INSTALL_SNAPPER=""
INSTALL_TIMESHIFT=""

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID=$ID
    [ -z "$DISTRO_ID" ] && [ -n "$ID_LIKE" ] && DISTRO_ID=$ID_LIKE
fi

# Set install commands based on detected distro
case $DISTRO_ID in
    fedora)
        INSTALL_SNAPPER="sudo dnf install -y snapper"
        INSTALL_TIMESHIFT="sudo dnf install -y timeshift"
        ;;
    arch)
        INSTALL_SNAPPER="sudo pacman -S --noconfirm snapper"
        INSTALL_TIMESHIFT="sudo pacman -S --noconfirm timeshift"
        ;;
    debian|ubuntu|pop)
        INSTALL_SNAPPER="sudo apt install -y snapper"
        INSTALL_TIMESHIFT="sudo apt install -y timeshift"
        ;;
    opensuse*) # Catches opensuse-leap, opensuse-tumbleweed, etc.
        INSTALL_SNAPPER="sudo zypper install -n snapper"
        INSTALL_TIMESHIFT="sudo zypper install -n timeshift"
        ;;
    gentoo)
        INSTALL_SNAPPER="sudo emerge sys-fs/snapper"
        INSTALL_TIMESHIFT="sudo emerge app-backup/timeshift"
        ;;
    void)
        INSTALL_SNAPPER="sudo xbps-install -Sy snapper"
        INSTALL_TIMESHIFT="sudo xbps-install -Sy timeshift"
        ;;
    *)
        echo -e "${YELLOW}Warning: Unsupported distro '$DISTRO_ID' for auto-installing snapshot tools.${NC}"
        echo -e "${YELLOW}You will need to install 'snapper' or 'timeshift' manually.${NC}"
        ;;
esac
# --- End of New Section ---


echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  wcli (Python) Installation Script     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}Error: Do not run this script as root${NC}" >&2
  echo "Run as a regular user. The script will use sudo when needed." >&2
  exit 1
fi

# Check if files exist
if [ ! -f "$SCRIPT_DIR/$SCRIPT_NAME" ]; then
  echo -e "${RED}Error: ${SCRIPT_NAME} script not found in $SCRIPT_DIR${NC}" >&2
  exit 1
fi
if [ ! -d "$SCRIPT_DIR/$PACKAGE_NAME" ]; then
  echo -e "${RED}Error: ${PACKAGE_NAME}/ directory not found in $SCRIPT_DIR${NC}" >&2
  echo "Make sure the 'providers' folder is in the same directory as this installer." >&2
  exit 1
fi

# Check for Python 3 and PyYAML
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed. Please install it first.${NC}" >&2
    exit 1
fi
if ! python3 -c "import yaml" &> /dev/null; then
    echo -e "${YELLOW}Warning: PyYAML (python3-yaml) not found.${NC}"
    echo "This is required. Please install it."
    echo "e.g., sudo apt install python3-yaml OR sudo dnf install python3-pyyaml"
    read -p "Continue installation anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${YELLOW}Installation cancelled${NC}"
      exit 0
    fi
fi

# --- NEW: Install Snapshot Tool ---
echo ""
read -p "Do you want to install a snapshot tool (snapper or timeshift)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Which tool would you like to install?"
    echo "  [1] Snapper (Recommended for Btrfs systems like Fedora/openSUSE)"
    echo "  [2] Timeshift (Recommended for ext4 systems like Ubuntu/Mint)"
    read -p "Choice (1 or 2): " tool_choice

    case $tool_choice in
        1)
            if [ -n "$INSTALL_SNAPPER" ]; then
                echo -e "${BLUE}Installing Snapper...${NC}"
                if eval "$INSTALL_SNAPPER"; then
                    echo -e "${GREEN}✓ Snapper installed successfully.${NC}"
                else
                    echo -e "${RED}Error: Snapper installation failed. Please try manually.${NC}"
                fi
            else
                echo -e "${YELLOW}Cannot auto-install Snapper on this distro. Please install it manually.${NC}"
            fi
            ;;
        2)
            if [ -n "$INSTALL_TIMESHIFT" ]; then
                echo -e "${BLUE}Installing Timeshift...${NC}"
                if eval "$INSTALL_TIMESHIFT"; then
                    echo -e "${GREEN}✓ Timeshift installed successfully.${NC}"
                else
                    echo -e "${RED}Error: Timeshift installation failed. Please try manually.${NC}"
                fi
            else
                echo -e "${YELLOW}Cannot auto-install Timeshift on this distro. Please install it manually.${NC}"
            fi
            ;;
        *)
            echo -e "${YELLOW}Invalid choice. Skipping snapshot tool installation.${NC}"
            ;;
    esac
else
    echo -e "${YELLOW}Skipping snapshot tool installation.${NC}"
fi
# --- End of New Section ---


# Install/reinstall
echo ""
echo -e "${BLUE}Installing wcli files to $INSTALL_DIR...${NC}"
sudo mkdir -p "$INSTALL_DIR"
sudo cp "$SCRIPT_DIR/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
sudo cp -r "$SCRIPT_DIR/$PACKAGE_NAME" "$INSTALL_DIR/"

# Set permissions
sudo chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Create symlink
echo -e "${BLUE}Creating symlink in $BIN_DIR...${NC}"
sudo ln -sf "$INSTALL_DIR/$SCRIPT_NAME" "$BIN_DIR/$SCRIPT_NAME"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Run 'wcli help' to see all available commands"
