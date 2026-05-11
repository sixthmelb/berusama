"""
Firewall Generators: Hardening, Block Site, Port Knocking
"""

from generators import BaseGenerator

BLOCK_PRESETS = {
    "youtube":  ["youtube.com", "googlevideo.com", "ytimg.com", "yt3.ggpht.com"],
    "tiktok":   ["tiktok.com", "tiktokcdn.com", "musical.ly", "tiktokv.com"],
    "facebook": ["facebook.com", "fbcdn.net", "fb.com", "fb.me"],
    "instagram":["instagram.com", "cdninstagram.com"],
    "twitter":  ["twitter.com", "twimg.com", "t.co", "x.com"],
    "telegram": ["telegram.org", "t.me", "telegra.ph", "cdn.telegram.org"],
    "netflix":  ["netflix.com", "nflxvideo.net", "nflximg.net"],
    "gambling": ["poker", "casino", "bet365", "sbobet", "togel"],
}


class FirewallHardeningGenerator(BaseGenerator):
    """Production Firewall Template — input/forward/output chain"""

    TITLE = "Firewall Hardening (Production Template)"

    def collect_params(self):
        c = self.cli
        c.info("Generate firewall rules production-grade\n")

        lan_list  = c.prompt("Interface LAN (interface-list name)", default="LAN")
        wan_list  = c.prompt("Interface WAN (interface-list name)", default="WAN")
        mgmt_ip   = c.prompt("IP manajemen (trusted, misal laptop admin)", default="192.168.1.5")
        ssh_port  = c.prompt("Port SSH", default="22")
        winbox_port = c.prompt("Port Winbox", default="8291")
        wg_port   = c.prompt("Port WireGuard (kosong jika tidak pakai)", default="51820", required=False)

        add_bruteforce = c.prompt_confirm("Tambah anti brute-force SSH?", default=True)
        add_icmp       = c.prompt_confirm("Tambah ICMP rate limit?", default=True)
        add_bogon      = c.prompt_confirm("Block bogon/martian IP addresses?", default=True)
        add_portscan   = c.prompt_confirm("Tambah port scan detection?", default=False)

        return {
            "lan": lan_list, "wan": wan_list,
            "mgmt_ip": mgmt_ip,
            "ssh_port": ssh_port, "winbox_port": winbox_port,
            "wg_port": wg_port,
            "bruteforce": add_bruteforce,
            "icmp": add_icmp,
            "bogon": add_bogon,
            "portscan": add_portscan,
        }

    def generate(self, p):
        lan = p["lan"]
        wan = p["wan"]
        mgmt = p["mgmt_ip"]

        lines = [self._header_comment(self.TITLE, [
            f"LAN List : {lan}",
            f"WAN List : {wan}",
            f"MGMT IP  : {mgmt}",
        ]), ""]

        # Interface lists
        lines += [
            "# ── Interface Lists ──────────────────────────────",
            "/interface list",
            f"add name={wan}",
            f"add name={lan}",
            "",
            "# !! Sesuaikan member list dengan interface aktual !!",
            "# /interface list member add interface=ether1 list=WAN",
            "# /interface list member add interface=bridge  list=LAN",
            "",
        ]

        if p["bogon"]:
            lines += [
                "# ── Bogon / Martian Address List ─────────────────",
                "/ip firewall address-list",
                'add list=bogon address=0.0.0.0/8        comment="This network"',
                'add list=bogon address=10.0.0.0/8       comment="Private"',
                'add list=bogon address=100.64.0.0/10    comment="Shared"',
                'add list=bogon address=127.0.0.0/8      comment="Loopback"',
                'add list=bogon address=169.254.0.0/16   comment="Link-local"',
                'add list=bogon address=172.16.0.0/12    comment="Private"',
                'add list=bogon address=192.0.0.0/24     comment="IETF Protocol"',
                'add list=bogon address=192.168.0.0/16   comment="Private"',
                'add list=bogon address=198.18.0.0/15    comment="Testing"',
                'add list=bogon address=198.51.100.0/24  comment="Documentation"',
                'add list=bogon address=203.0.113.0/24   comment="Documentation"',
                'add list=bogon address=224.0.0.0/4      comment="Multicast"',
                'add list=bogon address=240.0.0.0/4      comment="Reserved"',
                f'add list=whitelist address={mgmt}       comment="MGMT trusted"',
                "",
            ]

        lines += [
            "# ── INPUT CHAIN ──────────────────────────────────",
            "/ip firewall filter",
            'add chain=input connection-state=established,related action=accept comment="[IN] Accept established/related"',
            'add chain=input connection-state=invalid action=drop comment="[IN] Drop invalid"',
        ]

        if p["bogon"]:
            lines.append(
                f'add chain=input in-interface-list={wan} src-address-list=bogon '
                'action=drop comment="[IN] Drop bogon from WAN"'
            )

        if p["icmp"]:
            lines += [
                'add chain=input protocol=icmp limit=10,5:packet action=accept comment="[IN] ICMP rate-limited"',
                'add chain=input protocol=icmp action=drop comment="[IN] Drop excess ICMP"',
            ]

        lines += [
            f'add chain=input in-interface-list={lan} action=accept comment="[IN] Allow LAN"',
        ]

        if p["wg_port"]:
            lines.append(
                f'add chain=input protocol=udp dst-port={p["wg_port"]} '
                f'action=accept comment="[IN] WireGuard"'
            )

        if p["bruteforce"]:
            lines += [
                f'add chain=input protocol=tcp dst-port={p["ssh_port"]} '
                f'src-address-list=!whitelist connection-state=new '
                f'action=add-src-to-address-list address-list=ssh-brute '
                f'address-list-timeout=10m limit=3,1m:packet '
                f'comment="[IN] SSH brute detect"',
                'add chain=input src-address-list=ssh-brute action=drop comment="[IN] Drop SSH brute"',
            ]

        lines += [
            f'add chain=input src-address={mgmt} dst-port={p["ssh_port"]} protocol=tcp '
            f'action=accept comment="[IN] SSH from MGMT"',
            f'add chain=input src-address={mgmt} dst-port={p["winbox_port"]} protocol=tcp '
            f'action=accept comment="[IN] Winbox from MGMT"',
            'add chain=input action=drop comment="[IN] Drop all other"',
            "",
            "# ── FORWARD CHAIN ────────────────────────────────",
            'add chain=forward connection-state=established,related action=accept comment="[FWD] Accept established"',
            'add chain=forward connection-state=invalid action=drop comment="[FWD] Drop invalid"',
        ]

        if p["bogon"]:
            lines.append(
                f'add chain=forward in-interface-list={wan} src-address-list=bogon '
                'action=drop comment="[FWD] Drop bogon"'
            )

        if p["portscan"]:
            lines += [
                'add chain=forward protocol=tcp tcp-flags=fin,!syn,!rst,!psh,!ack,!urg '
                'action=add-src-to-address-list address-list=port-scanners '
                'address-list-timeout=1w comment="[FWD] Portscan: Null scan"',
                'add chain=forward protocol=tcp tcp-flags=fin,syn '
                'action=add-src-to-address-list address-list=port-scanners '
                'address-list-timeout=1w comment="[FWD] Portscan: FIN+SYN"',
                'add chain=forward src-address-list=port-scanners action=drop comment="[FWD] Drop port scanners"',
            ]

        lines += [
            f'add chain=forward in-interface-list={lan} out-interface-list={wan} '
            f'action=accept comment="[FWD] LAN to WAN"',
            'add chain=forward action=drop comment="[FWD] Drop default"',
            "",
            "# ── OUTPUT CHAIN (opsional) ──────────────────────",
            'add chain=output connection-state=established,related action=accept comment="[OUT] Accept established"',
            'add chain=output connection-state=invalid action=drop comment="[OUT] Drop invalid"',
            'add chain=output action=accept comment="[OUT] Accept all router traffic"',
        ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class BlockSiteGenerator(BaseGenerator):
    """Block Website/Domain Generator via DNS/Layer7/Address-list"""

    TITLE = "Block Website Generator"

    def collect_params(self):
        c = self.cli
        c.info("Block website menggunakan address-list + firewall filter\n")

        method = c.prompt_choice("Metode blocking", [
            ("dns",     "DNS redirect (block via DNS — paling efisien)"),
            ("layer7",  "Layer 7 protocol (deep inspection — lebih berat CPU)"),
            ("addrlist","Address list IP (butuh update IP manual)"),
        ], default=1)

        # Preset atau custom
        choices = [(k, k.capitalize()) for k in list(BLOCK_PRESETS.keys()) + ["custom"]]
        preset  = c.prompt_choice("Pilih preset atau custom", choices, default=len(choices))

        domains = []
        if preset == "custom":
            c.info("Masukkan domain/keyword (kosong untuk selesai):")
            while True:
                d = c.prompt("Domain/keyword", required=False)
                if not d:
                    break
                domains.append(d)
        else:
            domains = BLOCK_PRESETS[preset]
            c.info(f"Domains: {', '.join(domains)}")
            extra = c.prompt("Tambah domain lain? (kosong=skip)", required=False)
            if extra:
                domains.append(extra)

        list_name = c.prompt("Nama address/rule list", default=preset if preset != "custom" else "blocked-sites")
        interface_list = c.prompt("Interface LAN (interface-list)", default="LAN")

        return {
            "method": method,
            "domains": domains,
            "list_name": list_name,
            "lan": interface_list,
        }

    def generate(self, p):
        method  = p["method"]
        domains = p["domains"]
        lname   = p["list_name"]
        lan     = p["lan"]

        lines = [self._header_comment(self.TITLE, [
            f"Method  : {method}",
            f"Domains : {len(domains)} entries",
            f"List    : {lname}",
        ]), ""]

        if method == "dns":
            lines += [
                "# ── DNS Redirect — redirect domain ke 0.0.0.0 ───",
                "/ip dns static",
            ]
            for d in domains:
                lines.append(f'add name="{d}" address=0.0.0.0 comment="Block: {lname}"')
                lines.append(f'add name="*.{d}" address=0.0.0.0 comment="Block wildcard: {lname}"')

            lines += [
                "",
                "# Flush DNS cache setelah menambahkan static DNS:",
                "# /ip dns cache flush",
            ]

        elif method == "layer7":
            regex_parts = "|".join(d.replace(".", r"\.") for d in domains)
            lines += [
                "# ── Layer7 Protocol Match ────────────────────────",
                "/ip firewall layer7-protocol",
                f'add name="{lname}" regexp="({regex_parts})"',
                "",
                "# ── Firewall Filter — Block via L7 ──────────────",
                "/ip firewall filter",
                f'add chain=forward layer7-protocol="{lname}" '
                f'in-interface-list={lan} action=drop '
                f'comment="Block {lname} via L7"',
                "",
                "# !! PERINGATAN: Layer7 sangat membebani CPU !!",
                "# Tidak disarankan untuk traffic > 50Mbps",
            ]

        else:  # addrlist
            lines += [
                "# ── Address List ─────────────────────────────────",
                "# Update IP secara manual atau gunakan script otomatis",
                "/ip firewall address-list",
            ]
            for d in domains:
                lines.append(f'add list={lname} address={d} comment="Block: {d}"')

            lines += [
                "",
                "# ── Firewall Filter ──────────────────────────────",
                "/ip firewall filter",
                f'add chain=forward dst-address-list={lname} '
                f'in-interface-list={lan} action=drop '
                f'comment="Block {lname}"',
            ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class PortKnockGenerator(BaseGenerator):
    """Port Knocking dengan ICMP Packet Size"""

    TITLE = "Port Knocking dengan ICMP + Packet Size"

    def collect_params(self):
        c = self.cli
        c.info("Port Knocking — buka akses SSH/Winbox via sequence ICMP ping\n")
        c.info("Cara kerja: kirim 3 ping berurutan dengan packet size tertentu")
        c.info("untuk auto-whitelist IP kamu ke firewall\n")

        knock1 = c.prompt_int("Packet size knock 1 (bytes, misal: 100)", default=100, min_val=50, max_val=1400)
        knock2 = c.prompt_int("Packet size knock 2", default=200, min_val=50, max_val=1400)
        knock3 = c.prompt_int("Packet size knock 3", default=300, min_val=50, max_val=1400)

        timeout = c.prompt("Timeout whitelist setelah knock (misal: 30m, 1h)", default="30m")
        open_port  = c.prompt("Port yang dibuka setelah knock (misal: 22 atau 8291)", default="22")
        proto      = c.prompt_choice("Protocol", [("tcp","TCP"),("udp","UDP")], default=1)

        return {
            "knocks": [knock1, knock2, knock3],
            "timeout": timeout,
            "open_port": open_port,
            "proto": proto,
        }

    def generate(self, p):
        k = p["knocks"]
        t = p["timeout"]
        port  = p["open_port"]
        proto = p["proto"]

        # Size range: ±10 bytes dari target
        def size_range(s):
            return f"{s-10}-{s+10}"

        lines = [
            self._header_comment(self.TITLE, [
                f"Knock sequence: ICMP {k[0]}B → {k[1]}B → {k[2]}B",
                f"Whitelist timeout: {t}",
                f"Opens port: {proto}/{port}",
            ]),
            "",
            "# ── Port Knocking — ICMP Sequence ───────────────────",
            "/ip firewall filter",
            "",
            "# Stage 1 — detect knock 1",
            f'add chain=input protocol=icmp icmp-options=8:0 '
            f'packet-size={size_range(k[0])} '
            f'action=add-src-to-address-list address-list=knock-stage1 '
            f'address-list-timeout=5s comment="Knock #1 ({k[0]}B)"',
            "",
            "# Stage 2 — detect knock 2 (hanya jika sudah knock 1)",
            f'add chain=input protocol=icmp icmp-options=8:0 '
            f'packet-size={size_range(k[1])} '
            f'src-address-list=knock-stage1 '
            f'action=add-src-to-address-list address-list=knock-stage2 '
            f'address-list-timeout=5s comment="Knock #2 ({k[1]}B)"',
            "",
            "# Stage 3 — detect knock 3 (hanya jika sudah knock 1+2)",
            f'add chain=input protocol=icmp icmp-options=8:0 '
            f'packet-size={size_range(k[2])} '
            f'src-address-list=knock-stage2 '
            f'action=add-src-to-address-list address-list=knocked-whitelist '
            f'address-list-timeout={t} comment="Knock #3 — add to whitelist"',
            "",
            "# ── Allow port setelah berhasil knock ───────────────",
            f'add chain=input protocol={proto} dst-port={port} '
            f'src-address-list=knocked-whitelist '
            f'action=accept comment="Allow port {port} post-knock"',
            "",
            "# ── CARA PENGGUNAAN ─────────────────────────────────",
            f"# Dari client (Linux/Mac):",
            f"# ping -c1 -s{k[0]} <ROUTER_IP>   # Knock 1",
            f"# ping -c1 -s{k[1]} <ROUTER_IP>   # Knock 2",
            f"# ping -c1 -s{k[2]} <ROUTER_IP>   # Knock 3",
            f"# ssh admin@<ROUTER_IP>            # Sekarang bisa connect!",
            "#",
            "# Windows (PowerShell):",
            f'# ping -l {k[0]} <ROUTER_IP>',
            f'# ping -l {k[1]} <ROUTER_IP>',
            f'# ping -l {k[2]} <ROUTER_IP>',
        ]

        return "\n".join(lines)
