#!/bin/bash

# DeautherTUI Setup Script
# Supports apt (Debian/Ubuntu/Kali) and pacman (Arch/Manjaro)

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}DeautherTUI Setup Starting...${NC}"

if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root. Try: sudo ./setup.sh${NC}"
   exit 1
fi

# Detect package manager
if command -v apt-get &> /dev/null; then
    echo -e "${GREEN}Detected apt-based system.${NC}"
    apt-get update
    apt-get install -y aircrack-ng iw iproute2 python3 python3-pip
elif command -v pacman &> /dev/null; then
    echo -e "${GREEN}Detected pacman-based system.${NC}"
    pacman -Sy --noconfirm aircrack-ng iw iproute2 python python-pip
elif command -v dnf &> /dev/null; then
    echo -e "${GREEN}Detected dnf-based system (Fedora/RHEL).${NC}"
    dnf install -y aircrack-ng iw iproute python3 python3-pip
elif command -v zypper &> /dev/null; then
    echo -e "${GREEN}Detected zypper-based system (openSUSE).${NC}"
    zypper install -y aircrack-ng iw iproute2 python3 python3-pip
elif command -v apk &> /dev/null; then
    echo -e "${GREEN}Detected apk-based system (Alpine).${NC}"
    apk add --no-cache aircrack-ng iw iproute2 python3 py3-pip
elif command -v pkg &> /dev/null; then
    echo -e "${GREEN}Detected pkg-based system (Termux/FreeBSD).${NC}"
    pkg install -y root-repo # required for aircrack-ng in Termux
    pkg install -y aircrack-ng iw iproute2 python
else
    echo -e "${RED}Unsupported package manager. Please install aircrack-ng and python3 manually.${NC}"
    exit 1
fi

# Install Python packages globally
echo -e "${BLUE}Installing Python dependencies globally...${NC}"

python3 -m pip install --break-system-packages --upgrade pip
python3 -m pip install --break-system-packages -r requirements.txt

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${BLUE}To run the tool: sudo python3 deauther.py${NC}"
