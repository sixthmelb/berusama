"""
System Generators: Timezone Indonesia, Full Hardening, Auto Backup Email
"""

from generators import BaseGenerator


TIMEZONE_MAP = {
    "WIB":  ("Asia/Jakarta",    "WIB  — Waktu Indonesia Barat  (UTC+7)  — Sumatra, Jawa, Kalimantan Barat/Tengah"),
    "WITA": ("Asia/Makassar",   "WITA — Waktu Indonesia Tengah (UTC+8)  — Kalimantan Timur, Sulawesi, Bali, NTB, NTT"),
    "WIT":  ("Asia/Jayapura",   "WIT  — Waktu Indonesia Timur  (UTC+9)  — Maluku, Papua"),
}

NTP_SERVERS = {
    "pool_id":    ("0.id.pool.ntp.org",   "NTP Pool Indonesia"),
    "bmkg":       ("ntp.bmkg.go.id",      "BMKG Indonesia"),
    "itb":        ("ntp.itb.ac.id",       "ITB (Bandung)"),
    "unila":      ("ntp.unila.ac.id",     "Unila (Lampung)"),
    "cloudflare": ("time.cloudflare.com", "Cloudflare NTP"),
    "google":     ("time.google.com",     "Google NTP"),
    "custom":     ("",                    "Custom NTP Server"),
}


class TimezoneGenerator(BaseGenerator):
    TITLE = "Timezone Indonesia + NTP Setup"

    def collect_params(self):
        c = self.cli
        c.info("Setup timezone dan NTP server untuk MikroTik\n")

        tz_choices = [(k, v[1]) for k, v in TIMEZONE_MAP.items()]
        tz_key     = c.prompt_choice("Pilih timezone", tz_choices, default=1)
        tz_name    = TIMEZONE_MAP[tz_key][0]

        ntp_choices = [(k, v[1]) for k, v in NTP_SERVERS.items()]
        ntp_key     = c.prompt_choice("NTP Server Primer", ntp_choices, default=1)

        if ntp_key == "custom":
            ntp_primary = c.prompt("NTP primary server")
        else:
            ntp_primary = NTP_SERVERS[ntp_key][0]

        ntp2_key = c.prompt_choice("NTP Server Sekunder", ntp_choices, default=6)
        if ntp2_key == "custom":
            ntp_secondary = c.prompt("NTP secondary server")
        else:
            ntp_secondary = NTP_SERVERS[ntp2_key][0]

        router_name  = c.prompt("Hostname router", default="MikroTik-Router")
        set_identity = c.prompt_confirm("Set router identity sekalian?", default=True)

        return {
            "tz": tz_name,
            "tz_key": tz_key,
            "ntp1": ntp_primary,
            "ntp2": ntp_secondary,
            "router_name": router_name,
            "set_identity": set_identity,
        }

    def generate(self, p):
        lines = [self._header_comment(self.TITLE, [
            f"Timezone : {p['tz']} ({p['tz_key']})",
            f"NTP      : {p['ntp1']} / {p['ntp2']}",
            f"Hostname : {p['router_name']}",
        ]), ""]

        if p["set_identity"]:
            lines += [
                "# ── Router Identity ──────────────────────────────",
                f'/system identity set name="{p["router_name"]}"',
                "",
            ]

        lines += [
            "# ── Timezone ─────────────────────────────────────",
            f'/system clock set time-zone-name={p["tz"]}',
            "",
            "# ── NTP Client ───────────────────────────────────",
            "/system ntp client set enabled=yes \\",
            f'  servers={p["ntp1"]},{p["ntp2"]}',
            "",
            "# ── Verifikasi ───────────────────────────────────",
            "# /system clock print",
            "# /system ntp client print",
            "# /system ntp client monitors print",
            "",
            "# ── Info Timezone Indonesia ──────────────────────",
        ]

        for k, (tz, desc) in TIMEZONE_MAP.items():
            marker = "▶" if k == p["tz_key"] else " "
            lines.append(f"# {marker} {desc}")
            lines.append(f"#   {tz}")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class HardeningGenerator(BaseGenerator):
    TITLE = "Full System Hardening Checklist"

    def collect_params(self):
        c = self.cli
        c.info("Generate full hardening script — production ready\n")
        c.warning("Review script sebelum diapply! Beberapa rule bisa lockout akses.\n")

        mgmt_ip      = c.prompt("IP trusted untuk manajemen (kamu)", default="192.168.1.5")
        new_ssh_port = c.prompt_int("Port SSH baru (default=22, rekomendasi non-standard)", default=2222, min_val=1024, max_val=65535)
        winbox_port  = c.prompt_int("Port Winbox (default=8291)", default=8291, min_val=1024, max_val=65535)
        api_enabled  = c.prompt_confirm("Aktifkan API (port 8728)?", default=False)
        api_ssl      = c.prompt_confirm("Aktifkan API-SSL (port 8729)?", default=False)
        disable_btest = c.prompt_confirm("Nonaktifkan Bandwidth Test server?", default=True)
        disable_proxy = c.prompt_confirm("Nonaktifkan Web Proxy (jika tidak dipakai)?", default=True)
        disable_socks = c.prompt_confirm("Nonaktifkan SOCKS?", default=True)
        disable_upnp  = c.prompt_confirm("Nonaktifkan UPnP?", default=True)
        disable_discovery = c.prompt_confirm("Nonaktifkan neighbor discovery ke WAN?", default=True)
        strong_crypto = c.prompt_confirm("Paksa strong crypto (SSH, SSL)?", default=True)
        admin_rename  = c.prompt_confirm("Rename user 'admin' ke nama lain?", default=True)
        new_admin     = ""
        if admin_rename:
            new_admin = c.prompt("Username admin baru", default="netadmin")

        return {
            "mgmt_ip": mgmt_ip,
            "ssh_port": new_ssh_port,
            "winbox_port": winbox_port,
            "api": api_enabled,
            "api_ssl": api_ssl,
            "btest": disable_btest,
            "proxy": disable_proxy,
            "socks": disable_socks,
            "upnp": disable_upnp,
            "discovery": disable_discovery,
            "strong_crypto": strong_crypto,
            "rename_admin": admin_rename,
            "new_admin": new_admin,
        }

    def generate(self, p):
        mgmt = p["mgmt_ip"]
        lines = [self._header_comment(self.TITLE, [
            f"MGMT IP    : {mgmt}",
            f"SSH Port   : {p['ssh_port']}",
            f"Winbox Port: {p['winbox_port']}",
            "!! REVIEW DULU SEBELUM DIAPPLY !!",
        ]), ""]

        lines += [
            "# ════════════════════════════════════════════════════",
            "# STEP 1 — Disable services yang tidak perlu",
            "# ════════════════════════════════════════════════════",
            "/ip service",
            "set telnet  disabled=yes",
            "set ftp     disabled=yes",
            "set www     disabled=yes",
            "set www-ssl disabled=yes",
            f"set ssh     port={p['ssh_port']} disabled=no address={mgmt}",
            f"set winbox  port={p['winbox_port']} disabled=no address={mgmt}",
            f"set api     disabled={'no' if p['api'] else 'yes'}",
            f"set api-ssl disabled={'no' if p['api_ssl'] else 'yes'}",
            "",
        ]

        if p["btest"]:
            lines += [
                "# Disable Bandwidth Test server",
                "/tool bandwidth-server set enabled=no",
                "",
            ]

        if p["proxy"]:
            lines += [
                "# Disable Web Proxy",
                "/ip proxy set enabled=no",
                "",
            ]

        if p["socks"]:
            lines += [
                "# Disable SOCKS",
                "/ip socks set enabled=no",
                "",
            ]

        if p["upnp"]:
            lines += [
                "# Disable UPnP",
                "/ip upnp set enabled=no",
                "",
            ]

        lines += [
            "# ════════════════════════════════════════════════════",
            "# STEP 2 — Neighbor Discovery",
            "# ════════════════════════════════════════════════════",
        ]
        if p["discovery"]:
            lines += [
                "# Disable CDP/MNDP ke WAN (biarkan ke LAN jika perlu)",
                "/ip neighbor discovery-settings set discover-interface-list=LAN",
                "",
            ]

        if p["strong_crypto"]:
            lines += [
                "# ════════════════════════════════════════════════════",
                "# STEP 3 — Strong Crypto",
                "# ════════════════════════════════════════════════════",
                "/ip ssh",
                "set strong-crypto=yes",
                "set forwarding-enabled=no",
                "",
                "# Disable weak ciphers SSL",
                "/ip ssl set tls-version=TLSv1.2,TLSv1.3",
                "",
            ]

        lines += [
            "# ════════════════════════════════════════════════════",
            "# STEP 4 — User Hardening",
            "# ════════════════════════════════════════════════════",
        ]
        if p["rename_admin"] and p["new_admin"]:
            lines += [
                f'# Rename admin → {p["new_admin"]}',
                f'/user add name={p["new_admin"]} group=full password="<STRONG_PASSWORD>"',
                "# Login dulu sebagai user baru, baru disable admin!",
                "/user disable admin",
                "# /user remove admin   ← opsional, setelah konfirmasi login ok",
                "",
            ]

        lines += [
            "# ════════════════════════════════════════════════════",
            "# STEP 5 — MAC Server (disable akses WAN)",
            "# ════════════════════════════════════════════════════",
            "/tool mac-server set allowed-interface-list=LAN",
            "/tool mac-server mac-winbox set allowed-interface-list=LAN",
            "/tool mac-server ping set enabled=no",
            "",
            "# ════════════════════════════════════════════════════",
            "# STEP 6 — Firewall Input Drop (tambahkan ke filter yang ada)",
            "# ════════════════════════════════════════════════════",
            "/ip firewall filter",
            f'add chain=input src-address={mgmt} action=accept '
            f'comment="Hardening: Allow MGMT IP" place-before=0',
            'add chain=input in-interface-list=WAN action=drop '
            'comment="Hardening: Drop all WAN input" place-before=99',
            "",
            "# ════════════════════════════════════════════════════",
            "# STEP 7 — RouterOS Update Notif (manual check)",
            "# ════════════════════════════════════════════════════",
            "# /system package update check-for-updates",
            "# /system routerboard upgrade   (jika firmware outdated)",
            "",
            "# ════════════════════════════════════════════════════",
            "# STEP 8 — Backup setelah hardening",
            "# ════════════════════════════════════════════════════",
            '/system backup save name="backup-post-hardening"',
            '/export file="config-post-hardening"',
        ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class BackupMailGenerator(BaseGenerator):
    TITLE = "Auto Backup ke Email (Scheduler)"

    def collect_params(self):
        c = self.cli
        c.info("Auto backup konfigurasi MikroTik dan kirim via email\n")

        smtp_server = c.prompt("SMTP Server", default="smtp.gmail.com")
        smtp_port   = c.prompt_int("Port SMTP", default=587)
        smtp_user   = c.prompt("Email username (pengirim)")
        smtp_pass   = c.prompt("Email password / app-password")
        email_from  = c.prompt("From email", default=smtp_user)
        email_to    = c.prompt("Kirim ke email (tujuan)")
        email_subj  = c.prompt("Subject prefix", default="[MikroTik Backup]")

        router_name = c.prompt("Nama router (untuk nama file backup)", default="Router-01")
        backup_type = c.prompt_choice("Tipe backup", [
            ("both",   "Binary + Export (.backup + .rsc)"),
            ("binary", "Binary saja (.backup)"),
            ("export", "Export saja (.rsc — text, bisa dibaca)"),
        ], default=1)

        encryption = c.prompt_confirm("Enkripsi backup (.backup)?", default=False)
        enc_pass   = ""
        if encryption:
            enc_pass = c.prompt("Password enkripsi backup")

        schedule_choices = [
            ("daily",   "Setiap hari"),
            ("weekly",  "Setiap minggu"),
            ("monthly", "Setiap bulan"),
        ]
        schedule    = c.prompt_choice("Jadwal backup", schedule_choices, default=2)
        sched_time  = c.prompt("Jam backup (format HH:MM:SS)", default="02:00:00")

        return {
            "smtp": smtp_server, "port": smtp_port,
            "user": smtp_user, "pass": smtp_pass,
            "from": email_from, "to": email_to,
            "subject": email_subj,
            "router": router_name,
            "type": backup_type,
            "encrypt": encryption, "enc_pass": enc_pass,
            "schedule": schedule, "time": sched_time,
        }

    def generate(self, p):
        r     = p["router"]
        btype = p["type"]

        if p["schedule"] == "daily":
            interval = "1d"
            start_date = "jan/01/1970"
        elif p["schedule"] == "weekly":
            interval = "7d"
            start_date = "jan/01/1970"
        else:
            interval = "30d"
            start_date = "jan/01/1970"

        lines = [self._header_comment(self.TITLE, [
            f"SMTP   : {p['smtp']}:{p['port']}",
            f"To     : {p['to']}",
            f"Jadwal : {p['schedule']} @ {p['time']}",
            f"Tipe   : {btype}",
        ]), ""]

        # Email setup
        lines += [
            "# ── 1. SMTP Setup ────────────────────────────────",
            "/tool e-mail set \\",
            f'  server={p["smtp"]} \\',
            f'  port={p["port"]} \\',
            f'  from="{p["from"]}" \\',
            f'  user="{p["user"]}" \\',
            f'  password="{p["pass"]}" \\',
            f'  start-tls=yes',
            "",
        ]

        # Backup script
        enc_part = f' encryption=aes256 password="{p["enc_pass"]}"' if p["encrypt"] else ""
        lines += [
            "# ── 2. Backup Script ─────────────────────────────",
            "/system script",
            f'add name="auto-backup" policy=read,write,ftp,email,sensitive source={{',
            f'  :local datenow [/system clock get date]',
            f'  :local timenow [/system clock get time]',
            f'  :local fname ("{r}-backup-" . $datenow)',
            f'  :local fnameclean [:tostr $fname]',
        ]

        if btype in ("both", "binary"):
            lines.append(f'  /system backup save name=$fnameclean{enc_part}')

        if btype in ("both", "export"):
            lines.append(f'  /export compact file=$fnameclean')

        # Build attachment list
        if btype == "both":
            attach_expr = f'($fnameclean . ".backup," . $fnameclean . ".rsc")'
        elif btype == "binary":
            attach_expr = f'($fnameclean . ".backup")'
        else:
            attach_expr = f'($fnameclean . ".rsc")'

        lines += [
            f'  :delay 3s',
            f'  /tool e-mail send \\',
            f'    to="{p["to"]}" \\',
            f'    subject=("{p["subject"]} " . $fnameclean) \\',
            f'    body=("Backup otomatis MikroTik {r}\\nTanggal: " . $datenow . " " . $timenow) \\',
            f'    file={attach_expr}',
            f'  :log info ("Auto backup berhasil dikirim: " . $fnameclean)',
            f'  :delay 5s',
        ]

        if btype in ("both", "binary"):
            lines.append(f'  /file remove ($fnameclean . ".backup")')
        if btype in ("both", "export"):
            lines.append(f'  /file remove ($fnameclean . ".rsc")')

        lines += ['}', ""]

        # Scheduler
        lines += [
            "# ── 3. Scheduler ─────────────────────────────────",
            "/system scheduler",
            f'add name="sched-auto-backup" \\',
            f'  interval={interval} \\',
            f'  start-time={p["time"]} \\',
            f'  on-event="/system script run auto-backup" \\',
            f'  policy=read,write,ftp,email,sensitive \\',
            f'  comment="Auto backup — {p["schedule"]} @ {p["time"]}"',
            "",
            "# ── 4. Test Manual ───────────────────────────────",
            "# /system script run auto-backup",
            "# /log print  ← cek hasil log",
        ]

        return "\n".join(lines)
