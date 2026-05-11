"""
CLI utilities: warna, input handler, output formatter
"""

import os
import sys
import re
import ipaddress


class Colors:
    """ANSI Color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Background
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"


class CLI:
    """Central CLI handler"""

    def __init__(self, no_color=False):
        self.no_color = no_color or not self._supports_color()
        self.c = Colors() if not self.no_color else type('NoColor', (), {
            k: '' for k in dir(Colors) if not k.startswith('_')
        })()

        self.GENERATORS = {
            "pcc":         ("Load Balancing PCC (Per Connection Classifier)", "load_balance"),
            "nth":         ("Load Balancing NTH (Next Traffic Handler)", "load_balance"),
            "ecmp":        ("Load Balancing ECMP (Equal Cost Multi Path)", "load_balance"),
            "failover":    ("Failover Recursive Gateway", "routing"),
            "static-route":("Static Routing (YouTube, TikTok, WA, FB, dll)", "routing"),
            "port-forward":("Port Forwarding dengan NAT", "nat"),
            "queue":       ("Simple Queue + Token Bucket", "qos"),
            "queue-shared":("Simple Queue Bandwidth Shared Up-To", "qos"),
            "queue-tree":  ("Queue Tree Bandwidth Shared Up-To", "qos"),
            "pcq":         ("PCQ untuk Queue Tree dan Simple Queue", "qos"),
            "burst":       ("Burst Limit Calculator", "qos"),
            "firewall":    ("Firewall Hardening (Production Template)", "security"),
            "block-site":  ("Block Website Generator", "security"),
            "port-knock":  ("Port Knocking dengan ICMP", "security"),
            "hotspot":     ("Hotspot Wizard (Easy Setup)", "hotspot"),
            "ppp-user":    ("PPP Secrets Username Password Generator", "hotspot"),
            "hotspot-user":("Hotspot Username Password Generator", "hotspot"),
            "wireguard":   ("WireGuard VPN Setup", "vpn"),
            "vpn-remote":  ("VPN Remote SSTP/L2TP/PPTP", "vpn"),
            "doh":         ("DNS over HTTPS (DoH) Setup", "dns"),
            "netwatch":    ("Netwatch Monitoring + Telegram/Email", "monitoring"),
            "vlan":        ("VLAN Bridge Setup", "interface"),
            "bonding":     ("Bonding/LACP Interface", "interface"),
            "timezone":    ("Timezone Indonesia Setup", "system"),
            "hardening":   ("Full Hardening Checklist", "security"),
            "backup-mail": ("Auto Backup ke Email", "system"),
        }

    def _supports_color(self):
        """Check apakah terminal support ANSI color"""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    def color(self, text, *codes):
        """Apply color codes ke text"""
        if self.no_color:
            return text
        code_str = "".join(codes)
        return f"{code_str}{text}{Colors.RESET}"

    def header(self, text):
        """Print section header"""
        width = 60
        line = "═" * width
        print(f"\n{self.color(line, Colors.CYAN, Colors.BOLD)}")
        print(self.color(f"  {text}", Colors.CYAN, Colors.BOLD))
        print(f"{self.color(line, Colors.CYAN, Colors.BOLD)}\n")

    def success(self, text):
        print(self.color(f"  ✓ {text}", Colors.GREEN))

    def error(self, text):
        print(self.color(f"  ✗ ERROR: {text}", Colors.RED), file=sys.stderr)

    def warning(self, text):
        print(self.color(f"  ⚠ {text}", Colors.YELLOW))

    def info(self, text):
        print(self.color(f"  ℹ {text}", Colors.CYAN))

    def prompt(self, text, default=None, required=True):
        """Interactive input prompt"""
        default_str = f" [{self.color(str(default), Colors.YELLOW)}]" if default is not None else ""
        prompt_str = self.color(f"  → {text}{default_str}: ", Colors.GREEN)

        while True:
            try:
                value = input(prompt_str).strip()
            except (KeyboardInterrupt, EOFError):
                print()
                print(self.color("\n  Dibatalkan.", Colors.YELLOW))
                sys.exit(0)

            if not value and default is not None:
                return default
            if not value and required:
                self.error("Input tidak boleh kosong!")
                continue
            if not value and not required:
                return ""
            return value

    def prompt_int(self, text, default=None, min_val=None, max_val=None):
        """Prompt untuk integer dengan validasi"""
        while True:
            raw = self.prompt(text, default=default)
            try:
                val = int(raw)
                if min_val is not None and val < min_val:
                    self.error(f"Minimal nilai: {min_val}")
                    continue
                if max_val is not None and val > max_val:
                    self.error(f"Maksimal nilai: {max_val}")
                    continue
                return val
            except ValueError:
                self.error("Harus berupa angka!")

    def prompt_choice(self, text, choices, default=None):
        """Prompt pilihan dari list"""
        print(f"\n  {self.color(text, Colors.BOLD)}")
        for i, (key, label) in enumerate(choices, 1):
            marker = self.color("●", Colors.GREEN) if str(i) == str(default) else self.color("○", Colors.GRAY)
            print(f"    {marker} {self.color(str(i), Colors.YELLOW)}. {label}")

        while True:
            raw = self.prompt("Pilih nomor", default=default)
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(choices):
                    return choices[idx][0]
                self.error(f"Pilih antara 1-{len(choices)}")
            except ValueError:
                self.error("Masukkan nomor!")

    def prompt_confirm(self, text, default=True):
        """Yes/No confirmation"""
        hint = "[Y/n]" if default else "[y/N]"
        raw = self.prompt(f"{text} {hint}", default="y" if default else "n", required=False)
        return raw.lower() in ("y", "yes", "")

    def prompt_ip(self, text, default=None):
        """Prompt IP address dengan validasi"""
        while True:
            raw = self.prompt(text, default=default)
            try:
                ipaddress.ip_address(raw)
                return raw
            except ValueError:
                self.error(f"IP address tidak valid: {raw}")

    def prompt_subnet(self, text, default=None):
        """Prompt subnet (IP/prefix) dengan validasi"""
        while True:
            raw = self.prompt(text, default=default)
            try:
                ipaddress.ip_network(raw, strict=False)
                return raw
            except ValueError:
                self.error(f"Subnet tidak valid: {raw} (contoh: 192.168.1.0/24)")

    def print_script(self, title, script):
        """Print generated RouterOS script dengan formatting"""
        print(f"\n{self.color('═' * 60, Colors.GREEN, Colors.BOLD)}")
        print(self.color(f"  📋 SCRIPT GENERATED: {title}", Colors.GREEN, Colors.BOLD))
        print(f"{self.color('═' * 60, Colors.GREEN, Colors.BOLD)}\n")
        print(self.color(script, Colors.WHITE))
        print(f"\n{self.color('═' * 60, Colors.GREEN, Colors.BOLD)}")

    def save_script(self, title, script):
        """Tanya user apakah mau save ke file"""
        if self.prompt_confirm("\nSimpan script ke file?", default=False):
            safe_name = re.sub(r'[^\w\-]', '_', title.lower()).strip('_')
            default_filename = f"mtik_{safe_name}.rsc"
            filename = self.prompt("Nama file", default=default_filename)
            try:
                with open(filename, 'w') as f:
                    f.write(f"# Generated by MikroTik AutoConfig CLI\n")
                    f.write(f"# {title}\n")
                    f.write(f"# ─────────────────────────────────────────\n\n")
                    f.write(script)
                self.success(f"Script disimpan ke: {self.color(filename, Colors.YELLOW)}")
            except Exception as e:
                self.error(f"Gagal menyimpan: {e}")

    def list_generators(self):
        """Print semua generator yang tersedia"""
        categories = {}
        for key, (label, cat) in self.GENERATORS.items():
            categories.setdefault(cat, []).append((key, label))

        cat_names = {
            "load_balance": "⚡ Load Balancing",
            "routing":      "🛣️  Routing",
            "nat":          "🔀 NAT & Port Forward",
            "qos":          "📊 QoS & Queue",
            "security":     "🔒 Security & Firewall",
            "hotspot":      "📶 Hotspot & PPP",
            "vpn":          "🔐 VPN",
            "dns":          "🌐 DNS",
            "monitoring":   "📡 Monitoring",
            "interface":    "🔌 Interface",
            "system":       "⚙️  System",
        }

        self.header("Daftar Generator Tersedia")
        for cat_key, cat_label in cat_names.items():
            if cat_key not in categories:
                continue
            print(self.color(f"\n  {cat_label}", Colors.CYAN, Colors.BOLD))
            for key, label in categories[cat_key]:
                print(f"    {self.color(key, Colors.YELLOW):<22} {label}")
        print()
