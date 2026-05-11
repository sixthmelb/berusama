"""
Netwatch Monitoring Generator
"""

from generators import BaseGenerator


class NetwatchGenerator(BaseGenerator):
    TITLE = "Netwatch Monitoring + Telegram / Email / WA Alert"

    def collect_params(self):
        c = self.cli
        c.info("Netwatch — monitoring host dengan alert otomatis\n")

        alert_method = c.prompt_choice("Metode alert", [
            ("telegram", "Telegram Bot"),
            ("email",    "Email (SMTP)"),
            ("both",     "Telegram + Email"),
            ("none",     "Log saja (tanpa alert eksternal)"),
        ], default=1)

        tg_config = {}
        if alert_method in ("telegram", "both"):
            c.info("\n─── Telegram Bot Config ───")
            tg_config["token"]   = c.prompt("Bot Token (dari @BotFather)", default="<YOUR_BOT_TOKEN>")
            tg_config["chat_id"] = c.prompt("Chat ID / Group ID", default="<YOUR_CHAT_ID>")

        email_config = {}
        if alert_method in ("email", "both"):
            c.info("\n─── Email / SMTP Config ───")
            email_config["server"] = c.prompt("SMTP server", default="smtp.gmail.com")
            email_config["port"]   = c.prompt_int("Port SMTP", default=587)
            email_config["user"]   = c.prompt("Email username")
            email_config["pass"]   = c.prompt("Email password/app-password")
            email_config["to"]     = c.prompt("Kirim alert ke email")
            email_config["from"]   = c.prompt("From email", default=email_config["user"])

        # Hosts to monitor
        c.info("\n─── Host yang Dimonitor ───")
        hosts = []
        while True:
            c.info(f"\n─── Host #{len(hosts)+1} ───")
            host_ip   = c.prompt_ip("IP atau hostname yang dimonitor", default="8.8.8.8")
            host_name = c.prompt("Label/nama host", default=f"Host-{len(hosts)+1}")
            interval  = c.prompt("Interval cek (misal: 30s, 1m)", default="30s")
            timeout   = c.prompt("Timeout per cek", default="3s")
            hosts.append({"ip": host_ip, "name": host_name, "interval": interval, "timeout": timeout})

            if not c.prompt_confirm("Tambah host lagi?", default=False):
                break

        router_id = c.prompt("Nama/identitas router (untuk pesan alert)", default="Router-01")

        return {
            "method": alert_method,
            "tg": tg_config,
            "email": email_config,
            "hosts": hosts,
            "router_id": router_id,
        }

    def generate(self, p):
        method  = p["method"]
        hosts   = p["hosts"]
        rid     = p["router_id"]
        tg      = p["tg"]
        em      = p["email"]

        lines = [self._header_comment(self.TITLE, [
            f"Alert method : {method}",
            f"Hosts        : {len(hosts)} entries",
            f"Router ID    : {rid}",
        ]), ""]

        # Email SMTP setup
        if method in ("email", "both") and em:
            lines += [
                "# ── Email / SMTP Setup ───────────────────────────",
                "/tool e-mail set \\",
                f'  server={em["server"]} \\',
                f'  port={em["port"]} \\',
                f'  from="{em["from"]}" \\',
                f'  user="{em["user"]}" \\',
                f'  password="{em["pass"]}" \\',
                f'  start-tls=yes',
                "",
            ]

        # Telegram helper function (script)
        if method in ("telegram", "both") and tg:
            lines += [
                "# ── Telegram Alert Script ────────────────────────",
                "/system script",
                'add name="tg-alert" policy=read,write,test source={',
                '  :local msg $1',
                f'  :local token "{tg["token"]}"',
                f'  :local chatid "{tg["chat_id"]}"',
                '  :local url ("https://api.telegram.org/bot" . $token . "/sendMessage")',
                '  /tool fetch url=$url http-method=post \\',
                '    http-data=("chat_id=" . $chatid . "&text=" . $msg . "&parse_mode=HTML") \\',
                '    output=none keep-result=no',
                '}',
                "",
            ]

        # Netwatch entries
        lines += [
            "# ── Netwatch Monitor ─────────────────────────────",
            "/tool netwatch",
        ]

        for h in hosts:
            name = h["name"]
            ip   = h["ip"]

            up_parts   = []
            down_parts = []

            up_log   = f'/log info "[{rid}] {name} ({ip}) — UP"'
            down_log = f'/log warning "[{rid}] {name} ({ip}) — DOWN!"'

            if method in ("telegram", "both") and tg:
                up_parts.append(
                    f'[/system script run tg-alert input=("🟢 [{rid}] {name} ({ip}) ONLINE")]'
                )
                down_parts.append(
                    f'[/system script run tg-alert input=("🔴 [{rid}] {name} ({ip}) OFFLINE!")]'
                )

            if method in ("email", "both") and em:
                up_parts.append(
                    f'/tool e-mail send to="{em["to"]}" '
                    f'subject="[{rid}] {name} UP" '
                    f'body="{name} ({ip}) is back ONLINE"'
                )
                down_parts.append(
                    f'/tool e-mail send to="{em["to"]}" '
                    f'subject="[{rid}] {name} DOWN!" '
                    f'body="{name} ({ip}) is OFFLINE! Check immediately."'
                )

            up_script   = up_log + "; " + "; ".join(up_parts)   if up_parts   else up_log
            down_script = down_log + "; " + "; ".join(down_parts) if down_parts else down_log

            lines.append(
                f'add host={ip} interval={h["interval"]} timeout={h["timeout"]} \\',
            )
            lines.append(f'  up-script="{up_script}" \\')
            lines.append(f'  down-script="{down_script}" \\')
            lines.append(f'  comment="Monitor: {name}"')
            lines.append("")

        lines += [
            "# ── Verifikasi ───────────────────────────────────",
            "# /tool netwatch print",
            "# /log print",
            "# /system script run tg-alert input=\"Test dari MikroTik\"",
        ]

        return "\n".join(lines)
