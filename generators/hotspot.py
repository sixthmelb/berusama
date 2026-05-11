"""
Hotspot & PPP Generators
"""

import random
import string
from generators import BaseGenerator


def _rand_pass(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


class HotspotWizard(BaseGenerator):
    """Easy Hotspot Setup Wizard"""

    TITLE = "Hotspot Wizard (Easy Setup)"

    def collect_params(self):
        c = self.cli
        c.info("Hotspot Wizard — setup hotspot dari nol\n")

        hs_iface    = c.prompt("Interface hotspot (Wlan/Ether ke client)", default="wlan1")
        hs_ip       = c.prompt_ip("IP hotspot gateway", default="192.168.88.1")
        hs_pool     = c.prompt("IP pool DHCP (misal: 192.168.88.2-192.168.88.254)", default="192.168.88.2-192.168.88.254")
        hs_name     = c.prompt("Nama hotspot server", default="hotspot1")
        dns_name    = c.prompt("DNS name hotspot (misal: hotspot.local)", default="hotspot.local")
        smtp_server = c.prompt("SMTP server (kosong jika tidak ada)", default="", required=False)

        # Profile
        c.info("\n─── Hotspot User Profile ───")
        profile_name = c.prompt("Nama profile", default="default")
        dl_limit     = c.prompt("Rate limit download (misal: 10M, kosong=unlimited)", default="10M", required=False)
        ul_limit     = c.prompt("Rate limit upload", default="5M", required=False)
        session_time = c.prompt("Session timeout (misal: 8h, kosong=unlimited)", default="", required=False)
        idle_timeout = c.prompt("Idle timeout", default="30m", required=False)
        shared_users = c.prompt_int("Shared users (user yang sama bisa login dari berapa device)", default=1, min_val=1)

        # Awal user
        c.info("\n─── User Awal ───")
        username = c.prompt("Username admin hotspot", default="admin")
        password = c.prompt("Password (kosong = generate otomatis)", default="", required=False)
        if not password:
            password = _rand_pass(10)
            c.success(f"Password generated: {password}")

        return {
            "hs_iface": hs_iface,
            "hs_ip": hs_ip,
            "hs_pool": hs_pool,
            "hs_name": hs_name,
            "dns_name": dns_name,
            "smtp_server": smtp_server,
            "profile": {
                "name": profile_name,
                "dl": dl_limit,
                "ul": ul_limit,
                "session": session_time,
                "idle": idle_timeout,
                "shared": shared_users,
            },
            "user": {"username": username, "password": password},
        }

    def generate(self, p):
        pr = p["profile"]
        u  = p["user"]

        rate_limit = ""
        if pr["dl"] or pr["ul"]:
            dl = pr["dl"] or "0"
            ul = pr["ul"] or "0"
            rate_limit = f' rate-limit="{dl}/{ul}"'

        session_part = f' session-timeout={pr["session"]}' if pr["session"] else ""
        idle_part    = f' idle-timeout={pr["idle"]}' if pr["idle"] else ""
        smtp_part    = f' smtp-server={p["smtp_server"]}' if p["smtp_server"] else ""

        lines = [self._header_comment(self.TITLE, [
            f"Interface  : {p['hs_iface']}",
            f"Gateway IP : {p['hs_ip']}",
            f"DNS Name   : {p['dns_name']}",
        ]), ""]

        lines += [
            "# ── 1. IP Address ────────────────────────────────",
            f'/ip address add address={p["hs_ip"]}/24 interface={p["hs_iface"]} comment="Hotspot Gateway"',
            "",
            "# ── 2. IP Pool ───────────────────────────────────",
            f'/ip pool add name=hotspot-pool ranges={p["hs_pool"]}',
            "",
            "# ── 3. DHCP Server ───────────────────────────────",
            f'/ip dhcp-server add name=dhcp-{p["hs_iface"]} interface={p["hs_iface"]} \\',
            f'  address-pool=hotspot-pool lease-time=1h disabled=no',
            "",
            f'/ip dhcp-server network add address={p["hs_ip"].rsplit(".",1)[0]+".0"}/24 \\',
            f'  gateway={p["hs_ip"]} dns-server={p["hs_ip"]},8.8.8.8',
            "",
            "# ── 4. Hotspot User Profile ──────────────────────",
            f'/ip hotspot user profile',
            f'add name="{pr["name"]}"'
            f'{rate_limit}'
            f'{session_part}'
            f'{idle_part}'
            f' shared-users={pr["shared"]}'
            f'{smtp_part}'
            f' comment="Profile: {pr["name"]}"',
            "",
            "# ── 5. Hotspot Server ────────────────────────────",
            f'/ip hotspot add name={p["hs_name"]} \\',
            f'  interface={p["hs_iface"]} \\',
            f'  address-pool=hotspot-pool \\',
            f'  profile=hsprof1 \\',
            f'  disabled=no',
            "",
            "# ── 6. Hotspot Server Profile ────────────────────",
            f'/ip hotspot profile set hsprof1 \\',
            f'  dns-name="{p["dns_name"]}" \\',
            f'  login-by=cookie,http-chap \\',
            f'  html-directory=hotspot \\',
            f'  http-cookie-lifetime=3d',
            "",
            "# ── 7. User ──────────────────────────────────────",
            f'/ip hotspot user add name="{u["username"]}" \\',
            f'  password="{u["password"]}" \\',
            f'  profile="{pr["name"]}" \\',
            f'  comment="Admin user"',
            "",
            "# ── 8. NAT Masquerade ────────────────────────────",
            f'/ip firewall nat add chain=srcnat src-address={p["hs_ip"].rsplit(".",1)[0]+".0"}/24 \\',
            f'  action=masquerade comment="Hotspot Masq"',
            "",
            f"# Login credentials: {u['username']} / {u['password']}",
            f"# Hotspot URL: http://{p['dns_name']} atau http://{p['hs_ip']}",
        ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class PPPUserGenerator(BaseGenerator):
    """PPP Secrets Username/Password Generator — bulk"""

    TITLE = "PPP Secrets Username Password Generator"

    def collect_params(self):
        c = self.cli
        c.info("Generate PPP Secrets untuk PPPoE / PPTP / L2TP\n")

        service = c.prompt_choice("Service type", [
            ("pppoe", "PPPoE (pelanggan fiber/ADSL)"),
            ("pptp",  "PPTP VPN"),
            ("l2tp",  "L2TP VPN"),
            ("any",   "Any (semua service)"),
        ], default=1)

        profile = c.prompt("Profile PPP", default="default")

        mode = c.prompt_choice("Mode input", [
            ("single",   "Single user"),
            ("bulk",     "Bulk (banyak sekaligus)"),
            ("generate", "Auto-generate (username + random password)"),
        ], default=1)

        users = []
        if mode == "single":
            username = c.prompt("Username", default="user1")
            password = c.prompt("Password (kosong=generate)", required=False)
            if not password:
                password = _rand_pass()
            local_ip = c.prompt("Local IP (kosong=auto)", required=False)
            remote_ip = c.prompt("Remote IP client (kosong=dari pool)", required=False)
            users.append({"user": username, "pass": password, "local": local_ip, "remote": remote_ip})

        elif mode == "bulk":
            c.info("Format: username,password[,remote-ip] — satu per baris, kosong untuk selesai")
            while True:
                raw = c.prompt("Entry", required=False)
                if not raw:
                    break
                parts = [x.strip() for x in raw.split(",")]
                users.append({
                    "user": parts[0],
                    "pass": parts[1] if len(parts) > 1 else _rand_pass(),
                    "local": "",
                    "remote": parts[2] if len(parts) > 2 else "",
                })

        else:  # generate
            prefix   = c.prompt("Prefix username", default="user")
            count    = c.prompt_int("Jumlah user", default=10, min_val=1)
            start    = c.prompt_int("Mulai dari nomor", default=1)
            pool_base = c.prompt("Base IP pool (misal: 10.0.0.) — kosong=tidak assign IP", required=False)
            for i in range(count):
                remote = f"{pool_base}{start+i}" if pool_base else ""
                users.append({
                    "user": f"{prefix}{start+i:03d}",
                    "pass": _rand_pass(),
                    "local": "",
                    "remote": remote,
                })

        return {"users": users, "service": service, "profile": profile, "mode": mode}

    def generate(self, p):
        lines = [self._header_comment(self.TITLE, [
            f"Service : {p['service']}",
            f"Profile : {p['profile']}",
            f"Users   : {len(p['users'])} entries",
        ]), "", "/ppp secret"]

        for u in p["users"]:
            local_part  = f" local-address={u['local']}"  if u["local"]  else ""
            remote_part = f" remote-address={u['remote']}" if u["remote"] else ""
            lines.append(
                f'add name="{u["user"]}" password="{u["pass"]}" '
                f'service={p["service"]} profile={p["profile"]}'
                f'{local_part}{remote_part}'
            )

        # Print credentials table
        lines += ["", "# ── Credentials Table ───────────────────────────"]
        lines.append(f"# {'Username':<20} {'Password':<15} {'Remote IP':<16}")
        lines.append(f"# {'─'*20} {'─'*15} {'─'*16}")
        for u in p["users"]:
            lines.append(f"# {u['user']:<20} {u['pass']:<15} {u['remote'] or '-':<16}")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class HotspotUserGenerator(BaseGenerator):
    """Hotspot Username/Password Generator — bulk"""

    TITLE = "Hotspot Username Password Generator"

    def collect_params(self):
        c = self.cli
        c.info("Generate Hotspot users — bisa bulk mode\n")

        profile = c.prompt("Nama profile", default="default")

        mode = c.prompt_choice("Mode input", [
            ("single",   "Single user"),
            ("bulk",     "Bulk manual input"),
            ("generate", "Auto-generate"),
        ], default=3)

        users = []
        if mode == "single":
            username = c.prompt("Username")
            password = c.prompt("Password (kosong=generate)", required=False) or _rand_pass()
            limit_uptime = c.prompt("Limit uptime (misal: 8h, kosong=unlimited)", required=False)
            limit_bytes  = c.prompt("Limit bytes total (misal: 1G, kosong=unlimited)", required=False)
            users.append({"user": username, "pass": password, "uptime": limit_uptime, "bytes": limit_bytes})

        elif mode == "bulk":
            c.info("Format: username,password — kosong untuk selesai")
            while True:
                raw = c.prompt("Entry", required=False)
                if not raw:
                    break
                parts = [x.strip() for x in raw.split(",")]
                users.append({
                    "user": parts[0],
                    "pass": parts[1] if len(parts) > 1 else _rand_pass(),
                    "uptime": "", "bytes": "",
                })

        else:
            prefix = c.prompt("Prefix username", default="guest")
            count  = c.prompt_int("Jumlah user", default=20, min_val=1)
            start  = c.prompt_int("Start nomor", default=1)
            pw_len = c.prompt_int("Panjang password", default=6, min_val=4)
            limit_uptime = c.prompt("Limit uptime per user (kosong=unlimited)", required=False)
            limit_bytes  = c.prompt("Limit bytes per user (misal: 500M, kosong=unlimited)", required=False)
            for i in range(count):
                users.append({
                    "user": f"{prefix}{start+i:03d}",
                    "pass": _rand_pass(pw_len),
                    "uptime": limit_uptime,
                    "bytes": limit_bytes,
                })

        return {"users": users, "profile": profile}

    def generate(self, p):
        lines = [self._header_comment(self.TITLE, [
            f"Profile: {p['profile']}",
            f"Users  : {len(p['users'])} entries",
        ]), "", "/ip hotspot user"]

        for u in p["users"]:
            extra = ""
            if u["uptime"]:
                extra += f' limit-uptime={u["uptime"]}'
            if u["bytes"]:
                extra += f' limit-bytes-total={u["bytes"]}'
            lines.append(
                f'add name="{u["user"]}" password="{u["pass"]}" '
                f'profile={p["profile"]}{extra}'
            )

        lines += ["", "# ── Credentials ─────────────────────────────────"]
        lines.append(f"# {'Username':<20} {'Password':<12}")
        lines.append(f"# {'─'*20} {'─'*12}")
        for u in p["users"]:
            lines.append(f"# {u['user']:<20} {u['pass']:<12}")

        return "\n".join(lines)
