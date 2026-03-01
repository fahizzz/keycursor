#!/bin/bash
# OnlyMouse Uninstaller - Clean removal
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  🗑️  OnlyMouse Uninstaller${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}ERROR: Please do NOT run this script as root or with sudo!${NC}"
    echo "The script will ask for sudo password when needed."
    exit 1
fi

# Confirmation prompt
echo -e "${CYAN}This will remove OnlyMouse and its configuration.${NC}"
echo -e "${CYAN}Dependencies (python-evdev, ydotool, etc.) will NOT be removed.${NC}"
echo ""
read -p "Are you sure you want to uninstall? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uninstall cancelled.${NC}"
    exit 0
fi

echo ""

# 1. STOP AND DISABLE SERVICE
echo -e "${YELLOW}[1/5] Stopping OnlyMouse service...${NC}"
if systemctl --user is-active onlymouse.service &>/dev/null; then
    systemctl --user stop onlymouse.service
    echo "Service stopped ✓"
else
    echo "Service not running"
fi

if systemctl --user is-enabled onlymouse.service &>/dev/null; then
    systemctl --user disable onlymouse.service
    echo "Service disabled ✓"
else
    echo "Service not enabled"
fi

# 2. REMOVE SERVICE FILE
echo ""
echo -e "${YELLOW}[2/5] Removing service file...${NC}"
if [ -f ~/.config/systemd/user/onlymouse.service ]; then
    rm ~/.config/systemd/user/onlymouse.service
    echo "Service file removed ✓"
else
    echo "Service file not found"
fi

# Reload systemd
systemctl --user daemon-reload
echo "Systemd reloaded ✓"

# 3. REMOVE SCRIPT
echo ""
echo -e "${YELLOW}[3/5] Removing OnlyMouse script...${NC}"
SCRIPT_PATH="$HOME/.local/bin/onlymouse"
if [ -f "$SCRIPT_PATH" ]; then
    rm "$SCRIPT_PATH"
    echo "Script removed ✓"
else
    echo "Script not found"
fi

# 4. REMOVE UDEV RULES (optional)
echo ""
echo -e "${YELLOW}[4/5] Removing udev rules...${NC}"
read -p "Remove udev rules for uinput? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f /etc/udev/rules.d/99-uinput.rules ]; then
        sudo rm /etc/udev/rules.d/99-uinput.rules
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo "Udev rules removed ✓"
    else
        echo "Udev rules not found"
    fi
else
    echo "Udev rules kept"
fi

# 5. REMOVE USER FROM GROUPS (optional)
echo ""
echo -e "${YELLOW}[5/5] User group membership...${NC}"
read -p "Remove user from 'input' and 'uinput' groups? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if groups $USER | grep -q '\binput\b'; then
        sudo gpasswd -d $USER input
        echo "Removed from 'input' group"
    fi
    if groups $USER | grep -q '\buinput\b'; then
        sudo gpasswd -d $USER uinput
        echo "Removed from 'uinput' group"
    fi
    echo -e "${YELLOW}Note: You need to log out and back in for group changes to take effect${NC}"
else
    echo "Group membership kept (recommended if you use other input tools)"
fi

# Optional: Remove uinput module config
echo ""
read -p "Remove uinput module auto-load configuration? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f /etc/modules-load.d/uinput.conf ]; then
        sudo rm /etc/modules-load.d/uinput.conf
        echo "uinput auto-load config removed ✓"
    fi
fi

# Optional: Remove uinput group
echo ""
read -p "Remove 'uinput' group? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if getent group uinput >/dev/null; then
        sudo groupdel uinput
        echo "uinput group removed ✓"
    fi
fi

# Completion message
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ UNINSTALL COMPLETE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}OnlyMouse has been removed from your system.${NC}"
echo ""
echo -e "${YELLOW}What was kept (if not manually removed):${NC}"
echo "  • Python packages (python3-evdev, ydotool, etc.)"
echo "  • ydotool system service"
echo ""
echo -e "${CYAN}To remove dependencies manually:${NC}"

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID

    case $DISTRO in
        arch|manjaro)
            echo "  sudo pacman -R python-evdev ydotool"
            ;;
        ubuntu|debian|pop|mint)
            echo "  sudo apt remove python3-evdev ydotool"
            ;;
        fedora|rhel|centos)
            echo "  sudo dnf remove python3-evdev ydotool"
            ;;
    esac
fi

echo ""
echo -e "${GREEN}Thank you for using OnlyMouse! 👋${NC}"
echo ""
