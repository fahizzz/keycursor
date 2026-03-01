#!/bin/bash
# KeyCursor Ultimate Installer - Everything in one go
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🚀 KeyCursor Ultimate Installer${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}ERROR: Please do NOT run this script as root or with sudo!${NC}"
    echo "The script will ask for sudo password when needed."
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ] && [ ! -d "keycursor" ]; then
    echo -e "${RED}ERROR: keycursor files not found in current directory!${NC}"
    echo "Please run this installer from the keycursor_project directory"
    exit 1
fi

# Detect package manager and distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo -e "${RED}Cannot detect Linux distribution${NC}"
    exit 1
fi

echo -e "${CYAN}Detected distribution: $DISTRO${NC}"
echo ""

# 1. INSTALL SYSTEM DEPENDENCIES
echo -e "${YELLOW}[1/7] Installing system dependencies...${NC}"
case $DISTRO in
    arch|manjaro)
        echo "Installing packages for Arch Linux..."
        sudo pacman -S --noconfirm python python-pip python-virtualenv ydotool python-gobject gtk3 libhandy python-cairo
        ;;
    ubuntu|debian|pop|mint|linuxmint)
        echo "Installing packages for Debian/Ubuntu..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv ydotool python3-gi gir1.2-gtk-3.0 python3-cairo
        ;;
    fedora|rhel|centos)
        echo "Installing packages for Fedora/RHEL..."
        sudo dnf install -y python3 python3-pip python3-virtualenv ydotool python3-gobject gtk3 python3-cairo
        ;;
    *)
        echo -e "${YELLOW}Unknown distribution. Please install manually:${NC}"
        echo "  - python3, python3-pip, python3-venv"
        echo "  - ydotool"
        echo "  - python3-gobject (or python-gobject)"
        echo "  - gtk3"
        read -p "Press enter when dependencies are installed..."
        ;;
esac
echo -e "${GREEN}System dependencies installed ✓${NC}"

# 2. USER GROUPS & PERMISSIONS
echo ""
echo -e "${YELLOW}[2/7] Setting up user groups and permissions...${NC}"

# Create uinput group if it doesn't exist
if ! getent group uinput >/dev/null; then
    echo "Creating 'uinput' group..."
    sudo groupadd -r uinput
fi

# Add user to input and uinput groups
GROUPS_ADDED=0
if ! groups $USER | grep -q '\binput\b'; then
    sudo usermod -a -G input $USER
    echo "Added user to 'input' group"
    GROUPS_ADDED=1
fi

if ! groups $USER | grep -q '\buinput\b'; then
    sudo usermod -a -G uinput $USER
    echo "Added user to 'uinput' group"
    GROUPS_ADDED=1
fi

if [ $GROUPS_ADDED -eq 0 ]; then
    echo -e "${GREEN}User already in required groups ✓${NC}"
fi

# Create udev rule for uinput
echo "Creating udev rule for uinput access..."
sudo tee /etc/udev/rules.d/99-uinput.rules > /dev/null <<EOF
KERNEL=="uinput", GROUP="uinput", MODE="0660"
EOF

# Create udev rule for input devices
echo "Creating udev rule for input devices..."
sudo tee /etc/udev/rules.d/99-input.rules > /dev/null <<EOF
KERNEL=="event*", GROUP="input", MODE="0660"
EOF

# Load uinput module if not loaded
if ! lsmod | grep -q uinput; then
    echo "Loading uinput kernel module..."
    sudo modprobe uinput
fi

# Make uinput load on boot
if [ ! -f /etc/modules-load.d/uinput.conf ]; then
    echo "Configuring uinput to load on boot..."
    echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf > /dev/null
fi

echo -e "${GREEN}Permissions configured ✓${NC}"

# 3. SETUP YDOTOOL
echo ""
echo -e "${YELLOW}[3/7] Setting up ydotool daemon...${NC}"

# Enable and start ydotool service
if systemctl is-enabled ydotool.service &>/dev/null; then
    echo "ydotool service already enabled ✓"
else
    echo "Enabling ydotool service..."
    sudo systemctl enable ydotool.service
fi

if systemctl is-active ydotool.service &>/dev/null; then
    echo "ydotool service is running ✓"
else
    echo "Starting ydotool service..."
    sudo systemctl start ydotool.service
    sleep 2
fi

if systemctl is-active ydotool.service &>/dev/null; then
    echo -e "${GREEN}ydotool daemon running ✓${NC}"
else
    echo -e "${RED}Warning: ydotool service failed to start${NC}"
    echo "This will be fixed after reboot"
fi

# 4. CREATE VENV AND INSTALL PYTHON DEPENDENCIES
echo ""
echo -e "${YELLOW}[4/7] Creating virtual environment and installing Python packages...${NC}"

INSTALL_DIR="$HOME/.local/share/keycursor"
VENV_DIR="$INSTALL_DIR/venv"

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" --system-site-packages
    echo -e "${GREEN}Virtual environment created ✓${NC}"
else
    echo -e "${GREEN}Virtual environment already exists ✓${NC}"
fi

# Install Python dependencies in venv
echo "Installing Python packages in virtual environment..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install evdev PyGObject

echo -e "${GREEN}Python dependencies installed ✓${NC}"

# 5. INSTALL SCRIPT
echo ""
echo -e "${YELLOW}[5/7] Installing KeyCursor application...${NC}"

# Copy entire application
echo "Copying application files..."
cp -r keycursor "$INSTALL_DIR/"
cp main.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/main.py"

# Create wrapper script in ~/.local/bin
BIN_DIR="$HOME/.local/bin"
WRAPPER_PATH="$BIN_DIR/keycursor"

mkdir -p "$BIN_DIR"

cat > "$WRAPPER_PATH" <<EOF
#!/bin/bash
# KeyCursor wrapper script
export GDK_BACKEND=x11
export YDOTOOL_SOCKET=/run/ydotool.sock
exec "$VENV_DIR/bin/python3" "$INSTALL_DIR/main.py" "\$@"
EOF

chmod +x "$WRAPPER_PATH"

echo -e "${GREEN}Application installed to $INSTALL_DIR ✓${NC}"
echo -e "${GREEN}Wrapper script created at $WRAPPER_PATH ✓${NC}"

# 6. CREATE SYSTEMD USER SERVICE
echo ""
echo -e "${YELLOW}[6/7] Creating KeyCursor user service...${NC}"

# Create systemd user directory
mkdir -p ~/.config/systemd/user/

# Create service file
cat > ~/.config/systemd/user/keycursor.service <<EOF
[Unit]
Description=KeyCursor - Keyboard Mouse Control
After=graphical-session.target
Requires=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=GDK_BACKEND=x11
Environment=YDOTOOL_SOCKET=/run/ydotool.sock
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
EOF

echo -e "${GREEN}Service file created ✓${NC}"

# 7. ENABLE AND APPLY CHANGES
echo ""
echo -e "${YELLOW}[7/7] Enabling service and applying changes...${NC}"

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Reload systemd user daemon
systemctl --user daemon-reload

# Enable the service
systemctl --user enable keycursor.service

echo -e "${GREEN}Service enabled ✓${NC}"

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "${YELLOW}Adding ~/.local/bin to PATH...${NC}"
    
    # Determine shell config file
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    echo -e "${GREEN}Added to $SHELL_RC ✓${NC}"
    echo -e "${YELLOW}You may need to restart your terminal or run: source $SHELL_RC${NC}"
fi

# Show completion message
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}🖱️  HOW TO USE:${NC}"
echo "  • Press ${YELLOW}CapsLock${NC} to toggle mouse mode"
echo "  • ${YELLOW}WASD${NC} to move cursor"
echo "  • ${YELLOW}Enter${NC} = Left click (hold to drag)"
echo "  • ${YELLOW}Backspace${NC} = Right click"
echo "  • ${YELLOW}\\${NC} = Middle click"
echo "  • ${YELLOW}PageUp/PageDown${NC} = Scroll (hold for continuous)"
echo "  • ${YELLOW}Q${NC} = Precision mode (speed 2, green bar)"
echo "  • ${YELLOW}TAB${NC} = Toggle acceleration"
echo "  • ${YELLOW}1-9, 0${NC} = Speed adjustment (2-50)"
echo ""
echo -e "${CYAN}✨ SMART AUTO-EXIT:${NC}"
echo "  • Any non-mouse key exits mode"
echo "  • ALL combos exit (${YELLOW}Ctrl+C${NC}, ${YELLOW}Alt+Tab${NC}, etc.)"
echo "  • EXCEPT: ${YELLOW}Ctrl/Shift/Alt${NC} + Click/RightClick"
echo ""
echo -e "${CYAN}🔧 SERVICE MANAGEMENT:${NC}"
echo "  • Check status:  ${GREEN}systemctl --user status keycursor${NC}"
echo "  • View logs:     ${GREEN}journalctl --user -u keycursor -f${NC}"
echo "  • Stop service:  ${GREEN}systemctl --user stop keycursor${NC}"
echo "  • Restart:       ${GREEN}systemctl --user restart keycursor${NC}"
echo "  • Disable:       ${GREEN}systemctl --user disable keycursor${NC}"
echo ""
echo -e "${CYAN}💻 MANUAL CONTROL:${NC}"
echo "  • Run manually:  ${GREEN}keycursor${NC}"
echo "  • (after adding ~/.local/bin to PATH)"
echo ""
echo -e "${CYAN}📍 INSTALLATION LOCATION:${NC}"
echo "  • Application:   ${BLUE}$INSTALL_DIR${NC}"
echo "  • Virtual env:   ${BLUE}$VENV_DIR${NC}"
echo "  • Wrapper:       ${BLUE}$WRAPPER_PATH${NC}"
echo ""

if [ $GROUPS_ADDED -eq 1 ]; then
    echo -e "${RED}⚠️  IMPORTANT: You MUST LOG OUT and LOG BACK IN${NC}"
    echo -e "${RED}   (or reboot) for group permissions to take effect!${NC}"
    echo ""
    echo -e "After logging back in, the service will start automatically,"
    echo -e "or you can start it manually with:"
    echo -e "  ${GREEN}systemctl --user start keycursor${NC}"
else
    echo -e "${YELLOW}Starting KeyCursor service now...${NC}"
    if systemctl --user start keycursor.service 2>/dev/null; then
        sleep 2
        if systemctl --user is-active keycursor.service &>/dev/null; then
            echo -e "${GREEN}✅ KeyCursor is now running!${NC}"
            echo -e "Press ${YELLOW}CapsLock${NC} to activate mouse mode!"
        else
            echo -e "${YELLOW}Service enabled but not yet running.${NC}"
            echo -e "Please log out and log back in to start it."
        fi
    else
        echo -e "${YELLOW}Service enabled but requires logout to start.${NC}"
        echo -e "Please log out and log back in."
    fi
fi

echo ""
echo -e "${GREEN}🎉 Enjoy your keyboard mouse control!${NC}"
echo ""