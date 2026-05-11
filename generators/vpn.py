"""
VPN Generators: WireGuard, VPN Remote SSTP/L2TP/PPTP
"""

import secrets
import base64
from generators import BaseGenerator


def _gen_wg_key_placeholder(label):
    """Generate placeholder WireGuard key (actual key harus dari /interface/wireguard)"""
    return f"<{label.upper()}_KEY_FROM_ROUTER>"


class WireGuardGenerator(BaseGenerator):
    """WireGuard VPN Setup — RouterOS v7+"""

    TITLE = "WireGuard VPN Setup (RouterOS v7+)"

    def collect_params(self):
        c = self.cli
        c.info("WireGuard VPN — hanya tersedia di RouterOS v7.1+\n")

        mode = c.prompt_choice("Mode deployment", [
            ("server", "Server (router sebagai WireGuard server)"),
            ("client", "Client (router konek ke WireGuard server)"),
            ("site2site", "Site-to-Site (dua router terhubung langsung)"),
        ], default=1)

        wg_iface   = c.prompt("Nama WireGuard interface", default="wg0")
        listen_port = c.prompt_int("Listen port", default=51820, min_val=1024, max_val=65535)
        wg_ip      = c.prompt_subnet("IP WireGuard interface (misal: 10.10.0.1/24)", default="10.10.0.1/24")

        peers = []
        if mode == "server":
            c.info("\n─── Setup Peers (Client) ───")
            peer_count = c.prompt_int("Jumlah peer/client", default=1, min_val=1)
            for i in range(1, peer_count + 1):
                c.info(f"\n─── Peer #{i} ───")
                peer_name   = c.prompt(f"Nama peer {i}", default=f"client{i}")
                peer_ip     = c.prompt_ip(f"IP peer {i} (di tunnel)", default=f"10.10.0.{i+1}")
                allowed_ips = c.prompt(f"Allowed IPs peer {i}", default=f"{peer_ip}/32")
                peers.append({"name": peer_name, "ip": peer_ip, "allowed": allowed_ips})

        elif mode == "client":
            c.info("\n─── Konfigurasi Server ───")
            srv_endpoint  = c.prompt_ip("IP publik server WireGuard", default="203.0.113.1")
            srv_port      = c.prompt_int("Port server", default=51820)
            srv_pubkey    = c.prompt("Public key server (dari server)")
            allowed_ips   = c.prompt("Allowed IPs (0.0.0.0/0 = full tunnel)", default="0.0.0.0/0")
            keepalive     = c.prompt_int("Persistent keepalive (detik, 0=off)", default=25)
            peers.append({
                "name": "server", "endpoint": srv_endpoint,
                "port": srv_port, "pubkey": srv_pubkey,
                "allowed": allowed_ips, "keepalive": keepalive,
            })

        else:  # site2site
            c.info("\n─── Konfigurasi Site Remote ───")
            remote_ip    = c.prompt_ip("IP publik site remote", default="203.0.113.2")
            remote_port  = c.prompt_int("Port site remote", default=51820)
            remote_pubkey = c.prompt("Public key site remote (dari router remote)")
            remote_subnet = c.prompt_subnet("Subnet LAN remote (untuk routing)", default="192.168.2.0/24")
            local_subnet  = c.prompt_subnet("Subnet LAN lokal", default="192.168.1.0/24")
            peers.append({
                "name": "site-remote", "endpoint": remote_ip,
                "port": remote_port, "pubkey": remote_pubkey,
                "allowed": f"{remote_subnet},10.10.0.0/24",
                "keepalive": 25,
                "remote_subnet": remote_subnet,
                "local_subnet": local_subnet,
            })

        firewall_ok = c.prompt_confirm("Tambahkan firewall rules WireGuard?", default=True)
        add_dns     = c.prompt("DNS untuk VPN client (kosong=skip)", default="1.1.1.1", required=False)

        return {
            "mode": mode,
            "wg_iface": wg_iface,
            "listen_port": listen_port,
            "wg_ip": wg_ip,
            "peers": peers,
            "firewall": firewall_ok,
            "dns": add_dns,
        }

    def generate(self, p):
        mode  = p["mode"]
        iface = p["wg_iface"]
        port  = p["listen_port"]
        wg_ip = p["wg_ip"]
        peers = p["peers"]

        lines = [self._header_comment(self.TITLE, [
            f"Mode      : {mode}",
            f"Interface : {iface}",
            f"Listen    : UDP/{port}",
            f"WG IP     : {wg_ip}",
            "RouterOS  : v7.1+",
        ]), ""]

        lines += [
            "# ── 1. WireGuard Interface ───────────────────────",
            f'/interface wireguard add name={iface} listen-port={port} \\',
            f'  comment="WireGuard VPN — {mode}"',
            "",
            f"# !! Setelah interface dibuat, ambil public key:",
            f"# /interface wireguard print",
            "",
            "# ── 2. IP Address ────────────────────────────────",
            f'/ip address add address={wg_ip} interface={iface} comment="WireGuard IP"',
            "",
        ]

        lines += [f"# ── 3. Peers ─────────────────────────────────────"]
        for peer in peers:
            pname = peer["name"]
            if mode == "server":
                lines += [
                    f'/interface wireguard peers add \\',
                    f'  interface={iface} \\',
                    f'  public-key="{_gen_wg_key_placeholder(pname)}" \\',
                    f'  allowed-address={peer["allowed"]} \\',
                    f'  comment="{pname}"',
                    "",
                ]
            else:
                ka = peer.get("keepalive", 0)
                ka_str = f"\\\n  persistent-keepalive={ka}s " if ka else ""
                ep_str = f'  endpoint-address={peer["endpoint"]} endpoint-port={peer.get("port", port)} \\\n'
                pubkey = peer.get("pubkey", _gen_wg_key_placeholder(pname))
                lines += [
                    f'/interface wireguard peers add \\',
                    f'  interface={iface} \\',
                    f'  public-key="{pubkey}" \\',
                    ep_str.rstrip() + " \\",
                    f'  allowed-address={peer["allowed"]} \\',
                    f'  persistent-keepalive={ka}s \\' if ka else "",
                    f'  comment="{pname}"',
                    "",
                ]

        # Site2site routing
        if mode == "site2site" and peers:
            peer = peers[0]
            remote_subnet = peer.get("remote_subnet", "")
            wg_gw = wg_ip.split("/")[0].rsplit(".", 1)[0] + ".2"
            if remote_subnet:
                lines += [
                    "# ── 4. Static Route ke LAN Remote ───────────────",
                    f'/ip route add dst-address={remote_subnet} \\',
                    f'  gateway={iface} comment="Route to remote LAN via WireGuard"',
                    "",
                ]

        # Firewall
        if p["firewall"]:
            lines += [
                "# ── 5. Firewall Rules ────────────────────────────",
                "/ip firewall filter",
                f'add chain=input protocol=udp dst-port={port} \\',
                f'  action=accept comment="Allow WireGuard UDP/{port}"',
                f'add chain=input in-interface={iface} \\',
                f'  action=accept comment="Allow WireGuard tunnel traffic"',
                f'add chain=forward in-interface={iface} \\',
                f'  action=accept comment="Forward WireGuard to LAN"',
                "",
            ]

        lines += [
            "# ── PANDUAN ──────────────────────────────────────",
            "# 1. Generate keys di router:",
            f"#    /interface wireguard print  → lihat public-key",
            "# 2. Kirim public-key ke admin peer, minta public-key balik",
            "# 3. Set public-key peer di atas",
            "# 4. Test: /ping <wg_peer_ip> interface=" + iface,
        ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class VPNRemoteGenerator(BaseGenerator):
    """VPN Remote Setup: SSTP, L2TP, PPTP"""

    TITLE = "VPN Remote SSTP / L2TP / PPTP"

    def collect_params(self):
        c = self.cli
        c.info("Setup VPN server untuk remote access\n")

        vpn_type = c.prompt_choice("Jenis VPN", [
            ("l2tp",  "L2TP/IPSec (recommended — aman, kompatibel luas)"),
            ("sstp",  "SSTP (butuh certificate, sangat aman)"),
            ("pptp",  "PPTP (legacy — tidak aman, hindari jika bisa)"),
        ], default=1)

        ip_pool_name = c.prompt("Nama IP pool VPN", default="vpn-pool")
        ip_pool_range = c.prompt("Range IP pool VPN", default="10.20.0.2-10.20.0.50")
        local_ip      = c.prompt_ip("IP lokal router di VPN", default="10.20.0.1")
        dns_server    = c.prompt("DNS untuk client VPN", default="8.8.8.8,1.1.1.1")

        ipsec_secret = ""
        if vpn_type == "l2tp":
            c.info("\n─── IPSec Pre-Shared Key ───")
            ipsec_secret = c.prompt("IPSec pre-shared key (PSK)", default="MyVpnSecret123!")

        profile_name = c.prompt("Nama PPP profile", default="vpn-profile")

        # Users
        c.info("\n─── VPN Users ───")
        users = []
        while True:
            uname = c.prompt("Username (kosong=selesai)", required=False)
            if not uname:
                break
            passwd = c.prompt(f"Password untuk {uname}")
            users.append({"user": uname, "pass": passwd})

        add_fw = c.prompt_confirm("Tambahkan firewall rules?", default=True)

        return {
            "vpn_type": vpn_type,
            "pool_name": ip_pool_name,
            "pool_range": ip_pool_range,
            "local_ip": local_ip,
            "dns": dns_server,
            "ipsec_secret": ipsec_secret,
            "profile": profile_name,
            "users": users,
            "add_fw": add_fw,
        }

    def generate(self, p):
        vtype  = p["vpn_type"]
        local  = p["local_ip"]

        lines = [self._header_comment(self.TITLE, [
            f"VPN Type : {vtype.upper()}",
            f"IP Pool  : {p['pool_range']}",
            f"Local IP : {local}",
        ]), ""]

        lines += [
            "# ── 1. IP Pool ───────────────────────────────────",
            f'/ip pool add name={p["pool_name"]} ranges={p["pool_range"]}',
            "",
            "# ── 2. PPP Profile ───────────────────────────────",
            f'/ppp profile add name={p["profile"]} \\',
            f'  local-address={local} \\',
            f'  remote-address={p["pool_name"]} \\',
            f'  dns-server={p["dns"]} \\',
            f'  use-encryption=yes \\',
            f'  change-tcp-mss=yes \\',
            f'  comment="VPN Profile — {vtype.upper()}"',
            "",
        ]

        if vtype == "l2tp":
            lines += [
                "# ── 3. L2TP Server ───────────────────────────────",
                f'/interface l2tp-server server set \\',
                f'  enabled=yes \\',
                f'  default-profile={p["profile"]} \\',
                f'  use-ipsec=yes \\',
                f'  ipsec-secret="{p["ipsec_secret"]}" \\',
                f'  authentication=mschap2',
                "",
            ]
            if p["add_fw"]:
                lines += [
                    "# ── 4. Firewall Rules L2TP/IPSec ─────────────────",
                    "/ip firewall filter",
                    'add chain=input protocol=udp dst-port=1701 action=accept comment="L2TP"',
                    'add chain=input protocol=udp dst-port=500  action=accept comment="IKE"',
                    'add chain=input protocol=udp dst-port=4500 action=accept comment="IPSec NAT-T"',
                    'add chain=input protocol=ipsec-esp         action=accept comment="IPSec ESP"',
                    "",
                ]

        elif vtype == "sstp":
            lines += [
                "# ── 3. SSTP Server ───────────────────────────────",
                f'/interface sstp-server server set \\',
                f'  enabled=yes \\',
                f'  default-profile={p["profile"]} \\',
                f'  authentication=mschap2 \\',
                f'  certificate=<CERTIFICATE_NAME>',
                "",
                "# !! Generate/import certificate terlebih dahulu:",
                "# /certificate add name=vpn-cert ... (atau import dari .p12)",
                "",
            ]
            if p["add_fw"]:
                lines += [
                    "/ip firewall filter",
                    'add chain=input protocol=tcp dst-port=443 action=accept comment="SSTP"',
                    "",
                ]

        else:  # pptp
            lines += [
                "# ── 3. PPTP Server (TIDAK DISARANKAN) ────────────",
                "# PPTP memiliki kelemahan keamanan serius!",
                "# Gunakan L2TP atau WireGuard sebagai alternatif.",
                f'/interface pptp-server server set \\',
                f'  enabled=yes \\',
                f'  default-profile={p["profile"]} \\',
                f'  authentication=mschap2',
                "",
            ]
            if p["add_fw"]:
                lines += [
                    "/ip firewall filter",
                    'add chain=input protocol=tcp dst-port=1723    action=accept comment="PPTP"',
                    'add chain=input protocol=gre                  action=accept comment="GRE"',
                    "",
                ]

        # Users
        if p["users"]:
            lines += [
                "# ── PPP Users ────────────────────────────────────",
                "/ppp secret",
            ]
            for u in p["users"]:
                lines.append(
                    f'add name="{u["user"]}" password="{u["pass"]}" '
                    f'service={vtype} profile={p["profile"]}'
                )

        return "\n".join(lines)
