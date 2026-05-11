"""
Routing Generators: Failover Recursive, Static Routing
"""

from generators import BaseGenerator


class FailoverGenerator(BaseGenerator):
    """Failover Recursive Gateway — dual WAN auto-failover"""

    TITLE = "Failover Recursive Gateway"

    def collect_params(self):
        c = self.cli
        c.info("Failover Recursive — WAN2 otomatis aktif jika WAN1 down\n")

        c.info("─── WAN 1 (Primary) ───")
        wan1_iface = c.prompt("Interface WAN1", default="ether1")
        wan1_gw    = c.prompt_ip("Gateway WAN1", default="192.168.100.1")
        wan1_check = c.prompt_ip("IP check WAN1 (misal IP ISP/DNS)", default="8.8.8.8")
        wan1_comment = c.prompt("Comment WAN1", default="WAN1-Primary")

        c.info("─── WAN 2 (Backup) ───")
        wan2_iface   = c.prompt("Interface WAN2", default="ether2")
        wan2_gw      = c.prompt_ip("Gateway WAN2", default="10.0.0.1")
        wan2_check   = c.prompt_ip("IP check WAN2", default="1.1.1.1")
        wan2_comment = c.prompt("Comment WAN2", default="WAN2-Backup")

        lan_iface = c.prompt("Interface LAN", default="bridge-LAN")
        interval  = c.prompt("Interval cek Netwatch (detik)", default="10")

        add_netwatch = c.prompt_confirm("Tambahkan Netwatch monitoring?", default=True)
        add_masq     = c.prompt_confirm("Tambahkan NAT Masquerade?", default=True)

        return {
            "wan1": {"iface": wan1_iface, "gw": wan1_gw, "check": wan1_check, "comment": wan1_comment},
            "wan2": {"iface": wan2_iface, "gw": wan2_gw, "check": wan2_check, "comment": wan2_comment},
            "lan": lan_iface,
            "interval": interval,
            "add_netwatch": add_netwatch,
            "add_masq": add_masq,
        }

    def generate(self, p):
        w1 = p["wan1"]
        w2 = p["wan2"]

        lines = [self._header_comment(self.TITLE, [
            f"WAN1 (Primary): {w1['iface']} → GW {w1['gw']}",
            f"WAN2 (Backup) : {w2['iface']} → GW {w2['gw']}",
            f"LAN           : {p['lan']}",
        ]), ""]

        # Recursive routes — check via IP target
        lines += [
            "# ── Recursive Check Routes ───────────────────────",
            "/ip route",
            f'add dst-address={w1["check"]}/32 gateway={w1["gw"]} distance=1 comment="{w1["comment"]}-check"',
            f'add dst-address={w2["check"]}/32 gateway={w2["gw"]} distance=2 comment="{w2["comment"]}-check"',
            "",
            "# ── Default Routes (recursive — auto failover) ───",
            f'add dst-address=0.0.0.0/0 gateway={w1["check"]} distance=1 check-gateway=ping comment="{w1["comment"]}"',
            f'add dst-address=0.0.0.0/0 gateway={w2["check"]} distance=2 check-gateway=ping comment="{w2["comment"]}"',
            "",
        ]

        if p["add_masq"]:
            lines += [
                "# ── NAT Masquerade ───────────────────────────────",
                "/ip firewall nat",
                f'add chain=srcnat out-interface={w1["iface"]} action=masquerade comment="Masq {w1["comment"]}"',
                f'add chain=srcnat out-interface={w2["iface"]} action=masquerade comment="Masq {w2["comment"]}"',
                "",
            ]

        if p["add_netwatch"]:
            interval = p["interval"]
            lines += [
                "# ── Netwatch Monitoring ──────────────────────────",
                "/tool netwatch",
                f'add host={w1["check"]} interval={interval}s timeout=1s \\',
                f'  up-script="/ip route enable [find comment=\\"{w1["comment"]}\\"]" \\',
                f'  down-script="/ip route disable [find comment=\\"{w1["comment"]}\\"]" \\',
                f'  comment="Monitor {w1["comment"]}"',
                "",
                f'add host={w2["check"]} interval={interval}s timeout=1s \\',
                f'  up-script="/ip route enable [find comment=\\"{w2["comment"]}\\"]" \\',
                f'  down-script="/ip route disable [find comment=\\"{w2["comment"]}\\"]" \\',
                f'  comment="Monitor {w2["comment"]}"',
                "",
            ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


POPULAR_ROUTES = {
    "youtube":  ["142.250.0.0/15", "172.217.0.0/16", "173.194.0.0/16", "74.125.0.0/16"],
    "tiktok":   ["103.121.18.0/24", "103.121.19.0/24", "161.117.0.0/16", "128.14.0.0/16"],
    "whatsapp": ["157.240.0.0/16", "31.13.64.0/18", "179.60.192.0/22"],
    "facebook": ["157.240.0.0/16", "31.13.64.0/18", "69.171.250.0/24", "204.15.20.0/22"],
    "instagram": ["157.240.0.0/16", "31.13.64.0/18"],
    "netflix":  ["198.38.96.0/19", "198.45.48.0/20", "23.246.0.0/18", "37.77.184.0/21"],
    "google":   ["142.250.0.0/15", "172.217.0.0/16", "8.8.8.0/24", "8.34.208.0/20"],
    "zoom":     ["3.7.35.0/25", "3.21.137.128/25", "52.202.62.192/26", "52.215.168.0/25"],
}


class StaticRouteGenerator(BaseGenerator):
    """Static Routing untuk website/service tertentu melalui WAN tertentu"""

    TITLE = "Static Routing per Website / Service"

    def collect_params(self):
        c = self.cli
        c.info("Route traffic ke website tertentu via WAN spesifik (PBR)\n")

        service_keys = list(POPULAR_ROUTES.keys()) + ["custom"]
        choices = [(k, k.capitalize()) for k in service_keys]
        service = c.prompt_choice("Pilih service/website", choices, default=1)

        custom_ips = []
        if service == "custom":
            c.info("Masukkan IP/subnet (kosongkan untuk selesai):")
            while True:
                ip = c.prompt("IP/Subnet", required=False)
                if not ip:
                    break
                custom_ips.append(ip)
            subnets = custom_ips
            svc_name = c.prompt("Nama service/label", default="custom-service")
        else:
            subnets = POPULAR_ROUTES[service]
            svc_name = service.capitalize()
            c.info(f"IP ranges untuk {svc_name}: {', '.join(subnets[:3])}{'...' if len(subnets) > 3 else ''}")

        gateway = c.prompt_ip("Gateway tujuan (WAN spesifik)", default="192.168.100.1")
        use_mangle = c.prompt_confirm("Gunakan mangle (lebih presisi, routing-mark)?", default=False)
        use_table  = "raw-table" if not use_mangle else "mangle"

        return {
            "subnets": subnets,
            "gateway": gateway,
            "svc_name": svc_name,
            "use_mangle": use_mangle,
        }

    def generate(self, p):
        subnets   = p["subnets"]
        gw        = p["gateway"]
        svc       = p["svc_name"]

        lines = [self._header_comment(self.TITLE, [
            f"Service : {svc}",
            f"Gateway : {gw}",
            f"Subnets : {len(subnets)} entries",
        ]), ""]

        if p["use_mangle"]:
            lines += [
                f"# ── Address List: {svc} ──────────────────────────",
                "/ip firewall address-list",
            ]
            for s in subnets:
                lines.append(f'add list={svc.lower()}-ips address={s} comment="{svc}"')

            lines += [
                "",
                f"# ── Mangle — mark routing untuk {svc} ───────────",
                "/ip firewall mangle",
                f'add chain=prerouting dst-address-list={svc.lower()}-ips \\',
                f'  action=mark-routing new-routing-mark=to-{svc.lower()} \\',
                f'  passthrough=no comment="Route {svc} via {gw}"',
                "",
                f"# ── Route untuk routing-mark to-{svc.lower()} ─────",
                "/ip route",
                f'add dst-address=0.0.0.0/0 gateway={gw} routing-mark=to-{svc.lower()} \\',
                f'  distance=1 comment="{svc} via {gw}"',
            ]
        else:
            lines += [
                f"# ── Static Routes: {svc} ─────────────────────────",
                "/ip route",
            ]
            for s in subnets:
                lines.append(f'add dst-address={s} gateway={gw} comment="{svc}"')

        return "\n".join(lines)
