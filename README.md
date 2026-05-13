# DeautherTUI

A premium Terminal User Interface (TUI) for WiFi deauthentication attacks, built using the `aircrack-ng` suite and Python's `Textual` framework.

## Features
- **Dashboard UI**: Real-time monitoring of Access Points and Clients.
- **Auto-Discovery**: Automatically find and list targets.
- **Multi-Band Scanning**: Supports 2.4GHz, 5GHz, and all-band scanning.
- **Easy Deployment**: Supports `apt`, `pacman`, `dnf`, `zypper`, `apk`, and Docker.
- **Demo Mode**: Test the UI without hardware.

## Installation

### Prerequisites
- A Linux distribution (Kali, Ubuntu, Arch, etc.)
- A WiFi card that supports **Monitor Mode** and **Packet Injection**.
- Root privileges.
- `aircrack-ng` suite installed.

### Option 1: Quick Setup Script (Recommended)
```bash
sudo ./setup.sh
```

### Option 2: Install as System Command (`sudo deauther`)
```bash
sudo /usr/bin/python3 setup.py install
```

> **Note:** If you see `sudo: /path/to/venv/python3: command not found` after installing,
> it means a stale script with a venv shebang exists at `/usr/local/bin/deauther`.
> Fix it by running:
> ```bash
> sudo bash -c 'echo -e "#!/usr/bin/python3\nimport sys\nsys.path.insert(0, \"/usr/lib/python3.14/site-packages\")\nfrom deauther import main\nmain()" > /usr/local/bin/deauther && chmod +x /usr/local/bin/deauther'
> ```

### Option 3: Docker
```bash
./deauther-docker.sh
```

## Usage
Launch the tool:
```bash
sudo deauther
# or
sudo python3 deauther.py
```

### Keybindings
| Key | Action |
|-----|--------|
| `S` | Start/Stop scanning |
| `D` | Deauth selected target |
| `R` | Refresh interfaces |
| `Q` | Quit |
| `Enter` / Click | Select a target |

## Demo Mode
Test the UI without a WiFi card:
```bash
DEAUTH_DEMO=1 python3 deauther.py
```

## Disclaimer
This tool is for **educational purposes and authorized security testing only**. Unauthorized use on networks you do not own is illegal. Use responsibly.
