# 📡 DeautherTUI
> **Advanced WiFi Security Auditor & Deauthentication Suite**

`DeautherTUI` is a premium, terminal-based security tool designed for wireless network auditing. Built with the powerful **Textual** framework and the **aircrack-ng** suite, it provides a sleek, modern interface for monitoring and testing WiFi vulnerabilities.

---

## ⚡ Key Features

| Feature | Description |
| :--- | :--- |
| 🖥️ **Premium UI** | A high-performance, responsive TUI with real-time updates. |
| 🔍 **Deep Scan** | Automated discovery of Access Points and connected Clients. |
| 📡 **Multi-Band** | Full support for **2.4GHz** and **5GHz**(where hardware allows). |
| 🛠️ **Auto-Config** | Handles monitor mode switching and process cleanup automatically. |
| 🐳 **Containerized** | Ready-to-use Docker environment for consistent execution. |
| 🧪 **Demo Mode** | Simulation mode for UI testing without wireless hardware. |

---

## 🚀 Getting Started

### 📋 Prerequisites
* **Operating System**: Linux (Kali, Arch, Debian, etc.)
* **Hardware**: WiFi adapter supporting **Monitor Mode** & **Packet Injection**.
* **Permissions**: Root/Sudo access is required for raw socket manipulation.

### 📥 Installation

Choose your preferred installation method:

#### 🔹 Method 1: System Install (Recommended)
This installs `deauther` as a global command.
```bash
git clone https://github.com/Elvandito/DeautherTUI.git
cd DeautherTUI
sudo /usr/bin/python3 setup.py install
```

#### 🔹 Method 2: Quick Setup
```bash
sudo ./setup.sh
```

#### 🔹 Method 3: Docker
```bash
./deauther-docker.sh
```

---

## 🎮 How to Use

Simply run the command from anywhere in your terminal:
```bash
sudo deauther
```

### ⌨️ Keybindings
| Key | Action |
| :---: | :--- |
| `S` | Toggle Scanning (Start/Stop) |
| `D` | Launch Deauthentication Attack |
| `R` | Refresh Network Interfaces |
| `Q` | Exit Application |
| `Enter` | Select Target from Table |

---

## 🛠️ Troubleshooting

> [!IMPORTANT]
> **Stale Venv Issue**: If you see `sudo: command not found` referencing a `venv` path, run the following fix:
> ```bash
> sudo bash -c 'echo -e "#!/usr/bin/python3\nimport sys\nsys.path.insert(0, \"/usr/lib/python3.14/site-packages\")\nfrom deauther import main\nmain()" > /usr/local/bin/deauther && chmod +x /usr/local/bin/deauther'
> ```

---

## 🧪 Demo Mode
Want to see the UI in action without hardware? Use the demo flag:
```bash
DEAUTH_DEMO=1 deauther
```

---

## ⚖️ Disclaimer
**For Educational Purposes Only.**
Unauthorized access or disruption of wireless networks is illegal. This tool is designed for security professionals and researchers to test their own infrastructure. Use responsibly and legally.

---
<p align="center">Made with ❤️ by <b>Elvandito</b></p>
