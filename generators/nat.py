"""
NAT & Port Forward Generator
"""

from generators import BaseGenerator

COMMON_SERVICES = {
    "http":     ("80", "tcp", "HTTP Web Server"),
    "https":    ("443", "tcp", "HTTPS Web Server"),
    "ssh":      ("22", "tcp", "SSH Server"),
    "ftp":      ("21", "tcp", "FTP Server"),
    "rdp":      ("3389", "tcp", "Remote Desktop (RDP)"),
    "smtp":     ("25", "tcp", "SMTP Mail Server"),
    "smtps":    ("587", "tcp", "SMTP Submission"),
    "imap":     ("143", "tcp", "IMAP Mail"),
    "imaps":    ("993", "tcp", "IMAP SSL"),
    "mysql":    ("3306", "tcp", "MySQL Database"),
    "pgsql":    ("5432", "tcp", "PostgreSQL Database"),
    "dns":      ("53", "both", "DNS Server"),
    "vpn-l2tp": ("1701", "udp", "L2TP VPN"),
    "vpn-pptp": ("1723", "tcp", "PPTP VPN"),
    "wg":       ("51820", "udp", "WireGuard VPN"),
    "mikrotik": ("8291", "tcp", "Winbox"),
    "custom":   (None, None, "Custom Port"),
}


class PortForwardGenerator(BaseGenerator):
    """Port Forwarding dengan NAT Destination"""

    TITLE = "Port Forwarding dengan NAT"

    def collect_params(self):
        c = self.cli
        c.info("Generator Port Forwarding — NAT Destination (DNAT)\n")

        wan_iface = c.prompt("Interface WAN (incoming)", default="ether1")
        entries   = []

        while True:
            c.info(f"\n─── Rule #{len(entries)+1} ───")

            choices = [(k, f"{k:10} — {v[2]}") for k, v in COMMON_SERVICES.items()]
            svc = c.prompt_choice("Pilih service", choices, default=17)  # custom

            if svc == "custom":
                ext_port = c.prompt("External port (misal: 8080 atau 8080-8090)", default="8080")
                protocol = c.prompt_choice("Protocol", [
                    ("tcp", "TCP"), ("udp", "UDP"), ("both", "TCP + UDP")
                ], default=1)
                svc_label = c.prompt("Label/comment", default="custom-service")
            else:
                info = COMMON_SERVICES[svc]
                ext_port  = info[0]
                protocol  = info[1]
                svc_label = info[2]
                c.info(f"Port: {ext_port} / Protocol: {protocol}")

            int_ip      = c.prompt_ip("IP server tujuan (LAN)", default="192.168.1.100")
            int_port    = c.prompt("Internal port tujuan", default=ext_port)
            src_limit   = c.prompt("Batasi source IP? (kosong = semua)", required=False)

            entries.append({
                "ext_port": ext_port,
                "protocol": protocol,
                "int_ip": int_ip,
                "int_port": int_port,
                "comment": svc_label,
                "src_limit": src_limit,
            })

            c.success(f"Rule '{svc_label}' ditambahkan.")
            if not c.prompt_confirm("Tambah rule lagi?", default=False):
                break

        add_hairpin = c.prompt_confirm("Tambahkan Hairpin NAT (akses internal via IP publik)?", default=True)
        lan_subnet  = ""
        if add_hairpin:
            lan_subnet = c.prompt_subnet("Subnet LAN", default="192.168.1.0/24")

        return {
            "wan_iface": wan_iface,
            "entries": entries,
            "add_hairpin": add_hairpin,
            "lan_subnet": lan_subnet,
        }

    def generate(self, p):
        wan     = p["wan_iface"]
        entries = p["entries"]

        lines = [self._header_comment(self.TITLE, [
            f"WAN Interface : {wan}",
            f"Rules         : {len(entries)} entries",
        ]), ""]

        lines += [
            "# ── NAT Destination (Port Forward) ──────────────",
            "/ip firewall nat",
        ]

        def _add_rule(proto, ext_port, entry):
            src_part = f' src-address={entry["src_limit"]}' if entry["src_limit"] else ""
            lines.append(
                f'add chain=dstnat protocol={proto} '
                f'in-interface={wan}{src_part} '
                f'dst-port={ext_port} '
                f'action=dst-nat to-addresses={entry["int_ip"]} '
                f'to-ports={entry["int_port"]} '
                f'comment="DNAT: {entry["comment"]}"'
            )

        for entry in entries:
            proto = entry["protocol"]
            ext   = entry["ext_port"]
            if proto == "both":
                _add_rule("tcp", ext, entry)
                _add_rule("udp", ext, entry)
            else:
                _add_rule(proto, ext, entry)

        lines.append("")

        # Hairpin NAT
        if p["add_hairpin"] and p["lan_subnet"]:
            lines += [
                "# ── Hairpin NAT (akses via IP publik dari LAN) ──",
            ]
            for entry in entries:
                proto = entry["protocol"]
                ext   = entry["ext_port"]

                def _hairpin(proto):
                    lines.append(
                        f'add chain=srcnat protocol={proto} '
                        f'src-address={p["lan_subnet"]} '
                        f'dst-address={entry["int_ip"]} '
                        f'dst-port={entry["int_port"]} '
                        f'action=masquerade '
                        f'comment="Hairpin: {entry["comment"]}"'
                    )

                if proto == "both":
                    _hairpin("tcp")
                    _hairpin("udp")
                else:
                    _hairpin(proto)

        lines += [
            "",
            "# ── Firewall Accept — Allow forwarded traffic ────",
            "/ip firewall filter",
        ]
        for entry in entries:
            proto = entry["protocol"]
            ext   = entry["ext_port"]
            def _fwrule(proto):
                lines.append(
                    f'add chain=forward protocol={proto} '
                    f'dst-address={entry["int_ip"]} dst-port={entry["int_port"]} '
                    f'action=accept comment="FW Allow {entry["comment"]}"'
                )
            if proto == "both":
                _fwrule("tcp")
                _fwrule("udp")
            else:
                _fwrule(proto)

        return "\n".join(lines)
