# DeautherTUI

A premium Terminal User Interface (TUI) for WiFi deauthentication attacks, built using the `aircrack-ng` suite and Python's `Textual` framework.

![TUI Screenshot Placeholder](https://via.placeholder.com/800x400?text=DeautherTUI+Interface)

## Features
- **Dashboard UI**: Real-time monitoring of Access Points and Clients.
- **Auto-Discovery**: Automatically find and list targets.
- **Easy Deployment**: Supports `apt` and `pacman` based systems.
- **Safe Mode**: Demo mode for testing the UI without hardware.

## Installation

### Prerequisites
- A Linux distribution (Kali, Ubuntu, Arch, etc.)
- A WiFi card that supports **Monitor Mode** and **Packet Injection**.
- Root privileges.

### Quick Start
1. Clone the repository (or navigate to the folder).
2. Run the setup script:
   ```bash
   sudo ./setup.sh
   ```
3. Launch the tool:
   ```bash
   sudo venv/bin/python3 deauther.py
   ```

## Usage
- **Arrow Keys**: Navigate the AP table.
- **S**: Start/Stop scanning.
- **Enter/Click**: Select a target.
- **D**: Launch deauthentication attack.
- **Q**: Quit.

## Demo Mode
To test the UI without a WiFi card, use:
```bash
DEAUTH_DEMO=1 python3 deauther.py
```

## Disclaimer
This tool is for educational purposes and authorized security testing only. Unauthorized use on networks you do not own is illegal. Use responsibly.
