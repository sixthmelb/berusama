"""
Load Balancing Generators: PCC, NTH, ECMP
"""

from generators import BaseGenerator


class LoadBalancePCC(BaseGenerator):
    """Load Balancing PCC (Per Connection Classifier) — multi-WAN"""

    TITLE = "Load Balancing PCC (Per Connection Classifier)"

    def collect_params(self):
        c = self.cli
        c.info("Setup Load Balancing PCC untuk multi-WAN\n")

        wan_count = c.prompt_int("Jumlah WAN interface", default=2, min_val=2, max_val=4)

        wans = []
        for i in range(1, wan_count + 1):
            c.info(f"─── WAN {i} ───")
            iface   = c.prompt(f"Nama interface WAN {i}", default=f"ether{i}")
            gw      = c.prompt_ip(f"Gateway WAN {i}", default=f"10.0.{i}.1")
            pub_ip  = c.prompt_ip(f"IP Publik WAN {i}", default=f"10.0.{i}.2")
            comment = c.prompt(f"Comment WAN {i}", default=f"WAN{i}-ISP")
            wans.append({"iface": iface, "gw": gw, "pub_ip": pub_ip, "comment": comment})

        lan_iface = c.prompt("Nama interface LAN / Bridge", default="bridge-LAN")
        pcc_mode  = c.prompt_choice("Mode PCC Classifier", [
            ("both-addresses", "Both Addresses (recommended — lebih merata)"),
            ("src-address",    "Source Address only"),
            ("dst-address",    "Destination Address only"),
            ("both-addresses-and-ports", "Both Addresses + Ports (paling granular)"),
        ], default=1)

        add_masq = c.prompt_confirm("Tambahkan NAT Masquerade per WAN?", default=True)
        add_fw   = c.prompt_confirm("Tambahkan firewall accept LAN→WAN?", default=True)

        return {
            "wans": wans,
            "lan_iface": lan_iface,
            "pcc_mode": pcc_mode,
            "add_masq": add_masq,
            "add_fw": add_fw,
        }

    def generate(self, p):
        wans     = p["wans"]
        n        = len(wans)
        lan      = p["lan_iface"]
        mode     = p["pcc_mode"]

        lines = [self._header_comment(self.TITLE, [
            f"WAN Count : {n}",
            f"LAN       : {lan}",
            f"PCC Mode  : {mode}",
        ]), ""]

        # Interface list
        lines += [
            "# ── Interface List ──────────────────────────────",
            "/interface list",
            "add name=WAN",
            "add name=LAN",
            "",
            "/interface list member",
        ]
        for w in wans:
            lines.append(f'add interface={w["iface"]} list=WAN comment="{w["comment"]}"')
        lines.append(f'add interface={lan} list=LAN')
        lines.append("")

        # IP Address placeholder
        lines += [
            "# ── IP Address (sesuaikan dengan kondisi jaringan) ──",
        ]
        for i, w in enumerate(wans, 1):
            lines.append(f'/ip address add address={w["pub_ip"]}/30 interface={w["iface"]} comment="{w["comment"]}"')
        lines.append("")

        # Mangle rules
        lines += [
            "# ── Mangle — Mark Connections ───────────────────",
            "/ip firewall mangle",
        ]
        # Mark incoming per WAN
        for w in wans:
            lines.append(
                f'add chain=input in-interface={w["iface"]} '
                f'action=mark-connection new-connection-mark={w["comment"]}-conn '
                f'passthrough=yes comment="Mark incoming {w["comment"]}"'
            )
        lines.append("")

        # Return traffic
        for w in wans:
            lines.append(
                f'add chain=output connection-mark={w["comment"]}-conn '
                f'action=mark-routing new-routing-mark=to-{w["comment"]} '
                f'passthrough=no comment="Route return {w["comment"]}"'
            )
        lines.append("")

        # PCC prerouting — distribute connections
        for idx, w in enumerate(wans):
            lines.append(
                f'add chain=prerouting dst-address-type=!local in-interface={lan} '
                f'action=mark-connection new-connection-mark={w["comment"]}-conn '
                f'per-connection-classifier={mode}:{n}/{idx} '
                f'passthrough=yes comment="PCC LB to {w["comment"]}"'
            )
        lines.append("")

        # Routing mark → route
        for w in wans:
            lines.append(
                f'add chain=prerouting connection-mark={w["comment"]}-conn '
                f'action=mark-routing new-routing-mark=to-{w["comment"]} '
                f'in-interface={lan} passthrough=no'
            )
        lines.append("")

        # IP Routes
        lines += [
            "# ── Routes ──────────────────────────────────────",
            "/ip route",
        ]
        for idx, w in enumerate(wans):
            dist = idx + 1
            lines.append(
                f'add dst-address=0.0.0.0/0 gateway={w["gw"]} '
                f'routing-mark=to-{w["comment"]} distance=1 '
                f'check-gateway=ping comment="{w["comment"]}"'
            )
        # Failover default routes
        for idx, w in enumerate(wans):
            lines.append(
                f'add dst-address=0.0.0.0/0 gateway={w["gw"]} '
                f'distance={idx+1} check-gateway=ping comment="{w["comment"]}-default"'
            )
        lines.append("")

        # NAT Masquerade
        if p["add_masq"]:
            lines += [
                "# ── NAT Masquerade ───────────────────────────────",
                "/ip firewall nat",
            ]
            for w in wans:
                lines.append(
                    f'add chain=srcnat out-interface={w["iface"]} '
                    f'action=masquerade comment="Masq {w["comment"]}"'
                )
            lines.append("")

        # Firewall forward
        if p["add_fw"]:
            lines += [
                "# ── Firewall Forward ─────────────────────────────",
                "/ip firewall filter",
                'add chain=forward connection-state=established,related action=accept comment="Accept established"',
                'add chain=forward connection-state=invalid action=drop comment="Drop invalid"',
                f'add chain=forward in-interface={lan} out-interface-list=WAN action=accept comment="LAN to WAN"',
                "",
            ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class LoadBalanceNTH(BaseGenerator):
    """Load Balancing NTH (Next Traffic Handler)"""

    TITLE = "Load Balancing NTH (Next Traffic Handler)"

    def collect_params(self):
        c = self.cli
        c.info("Load Balancing NTH — cocok untuk traffic distribution sederhana\n")

        wan_count = c.prompt_int("Jumlah WAN interface", default=2, min_val=2, max_val=4)
        wans = []
        for i in range(1, wan_count + 1):
            c.info(f"─── WAN {i} ───")
            iface = c.prompt(f"Interface WAN {i}", default=f"ether{i}")
            gw    = c.prompt_ip(f"Gateway WAN {i}", default=f"10.0.{i}.1")
            pub   = c.prompt_ip(f"IP Publik WAN {i}", default=f"10.0.{i}.2")
            wans.append({"iface": iface, "gw": gw, "pub": pub, "name": f"WAN{i}"})

        lan_iface = c.prompt("Interface LAN", default="bridge-LAN")

        return {"wans": wans, "lan": lan_iface}

    def generate(self, p):
        wans = p["wans"]
        lan  = p["lan"]
        n    = len(wans)

        lines = [self._header_comment(self.TITLE, [f"WAN Count: {n}", f"LAN: {lan}"]), ""]

        lines += ["/ip firewall mangle"]

        # NTH — setiap paket ketiga dialihkan ke WAN berikutnya
        for idx, w in enumerate(wans):
            lines.append(
                f'add chain=prerouting dst-address-type=!local in-interface={lan} '
                f'nth={n},{idx+1} action=mark-connection '
                f'new-connection-mark={w["name"]}-conn passthrough=yes '
                f'comment="NTH {idx+1}/{n} to {w["name"]}"'
            )

        lines.append("")
        for w in wans:
            lines.append(
                f'add chain=prerouting connection-mark={w["name"]}-conn '
                f'action=mark-routing new-routing-mark=to-{w["name"]} '
                f'in-interface={lan} passthrough=no'
            )

        lines += ["", "/ip route"]
        for idx, w in enumerate(wans):
            lines.append(
                f'add dst-address=0.0.0.0/0 gateway={w["gw"]} '
                f'routing-mark=to-{w["name"]} distance=1 check-gateway=ping'
            )
        for idx, w in enumerate(wans):
            lines.append(
                f'add dst-address=0.0.0.0/0 gateway={w["gw"]} '
                f'distance={idx+1} check-gateway=ping comment="{w["name"]}-fallback"'
            )

        lines += ["", "/ip firewall nat"]
        for w in wans:
            lines.append(
                f'add chain=srcnat out-interface={w["iface"]} '
                f'action=masquerade comment="Masq {w["name"]}"'
            )

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class LoadBalanceECMP(BaseGenerator):
    """Load Balancing ECMP (Equal Cost Multi Path) — RouterOS v7"""

    TITLE = "Load Balancing ECMP (Equal Cost Multi Path)"

    def collect_params(self):
        c = self.cli
        c.info("ECMP — built-in RouterOS v7, tidak perlu mangle rules\n")
        c.warning("ECMP hanya tersedia di RouterOS v7+\n")

        wan_count = c.prompt_int("Jumlah WAN interface", default=2, min_val=2, max_val=6)
        wans = []
        for i in range(1, wan_count + 1):
            iface = c.prompt(f"Interface WAN {i}", default=f"ether{i}")
            gw    = c.prompt_ip(f"Gateway WAN {i}", default=f"10.0.{i}.1")
            wans.append({"iface": iface, "gw": gw, "name": f"WAN{i}"})

        lan_iface = c.prompt("Interface LAN", default="bridge-LAN")
        add_masq  = c.prompt_confirm("Tambahkan NAT Masquerade?", default=True)

        return {"wans": wans, "lan": lan_iface, "add_masq": add_masq}

    def generate(self, p):
        wans     = p["wans"]
        lan      = p["lan"]

        lines = [self._header_comment(self.TITLE, [
            "Requires RouterOS v7+",
            f"WAN Count: {len(wans)}", f"LAN: {lan}",
        ]), ""]

        gw_str = ",".join(w["gw"] for w in wans)
        lines += [
            "# ── ECMP Route — semua gateway dengan distance sama ──",
            "/ip route",
            f'add dst-address=0.0.0.0/0 gateway={gw_str} distance=1 comment="ECMP Load Balance"',
            "",
        ]

        if p["add_masq"]:
            lines += ["/ip firewall nat"]
            for w in wans:
                lines.append(
                    f'add chain=srcnat out-interface={w["iface"]} '
                    f'action=masquerade comment="Masq {w["name"]}"'
                )
            lines.append("")

        lines += [
            "# ── Interface List ──────────────────────────────",
            "/interface list",
            "add name=WAN",
            "add name=LAN",
            "/interface list member",
        ]
        for w in wans:
            lines.append(f'add interface={w["iface"]} list=WAN')
        lines.append(f"add interface={lan} list=LAN")

        return "\n".join(lines)
