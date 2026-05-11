"""
Interface Generators: VLAN Bridge, Bonding/LACP
"""

from generators import BaseGenerator


class VLANGenerator(BaseGenerator):
    TITLE = "VLAN Bridge Setup (RouterOS v7 — Bridge VLAN Filtering)"

    def collect_params(self):
        c = self.cli
        c.info("Setup VLAN menggunakan bridge VLAN filtering (RouterOS v7)\n")

        bridge_name = c.prompt("Nama bridge", default="br-main")

        vlans = []
        c.info("\n─── Define VLANs ───")
        while True:
            vlan_id   = c.prompt_int(f"VLAN ID #{len(vlans)+1} (1-4094, 0=selesai)", default=0, min_val=0, max_val=4094)
            if vlan_id == 0:
                break
            vlan_name = c.prompt(f"Nama VLAN {vlan_id}", default=f"vlan{vlan_id}")
            vlan_ip   = c.prompt(f"IP Gateway VLAN {vlan_id} (kosong=skip)", default="", required=False)
            access_ifaces = c.prompt(f"Access (untagged) interfaces VLAN {vlan_id} (pisah koma)", default=f"ether{len(vlans)+2}")
            vlans.append({
                "id": vlan_id,
                "name": vlan_name,
                "ip": vlan_ip,
                "access": [x.strip() for x in access_ifaces.split(",")],
            })

        trunk_iface = c.prompt("Trunk interface (tagged semua VLAN, misal ke switch)", default="ether1")
        add_dhcp    = c.prompt_confirm("Generate DHCP server per VLAN?", default=True)
        add_fw      = c.prompt_confirm("Tambahkan inter-VLAN firewall (deny by default)?", default=True)

        return {
            "bridge": bridge_name,
            "vlans": vlans,
            "trunk": trunk_iface,
            "add_dhcp": add_dhcp,
            "add_fw": add_fw,
        }

    def generate(self, p):
        bridge = p["bridge"]
        vlans  = p["vlans"]
        trunk  = p["trunk"]

        lines = [self._header_comment(self.TITLE, [
            f"Bridge    : {bridge}",
            f"VLANs     : {len(vlans)} entries",
            f"Trunk     : {trunk}",
            "RouterOS  : v7+ (bridge VLAN filtering)",
        ]), ""]

        lines += [
            "# ── 1. Create Bridge ─────────────────────────────",
            f"/interface bridge",
            f"add name={bridge} vlan-filtering=yes comment=\"Main bridge with VLAN filtering\"",
            "",
            "# ── 2. Bridge Ports ──────────────────────────────",
            "/interface bridge port",
        ]

        # Trunk port
        lines.append(f"add bridge={bridge} interface={trunk} comment=\"Trunk — tagged all VLANs\"")

        # Access ports
        for vlan in vlans:
            for iface in vlan["access"]:
                lines.append(
                    f"add bridge={bridge} interface={iface} "
                    f"pvid={vlan['id']} comment=\"VLAN{vlan['id']} — {vlan['name']} access\""
                )

        lines += [
            "",
            "# ── 3. Bridge VLAN Table ─────────────────────────",
            "/interface bridge vlan",
        ]

        for vlan in vlans:
            untagged = ",".join(vlan["access"])
            tagged   = f"{bridge},{trunk}"
            lines.append(
                f"add bridge={bridge} vlan-ids={vlan['id']} "
                f"tagged={tagged} "
                f"untagged={untagged} "
                f"comment=\"VLAN{vlan['id']} — {vlan['name']}\""
            )

        lines += [
            "",
            "# ── 4. VLAN Interfaces (untuk routing) ───────────",
            "/interface vlan",
        ]

        for vlan in vlans:
            lines.append(
                f"add name={vlan['name']} vlan-id={vlan['id']} "
                f"interface={bridge} comment=\"L3 interface VLAN{vlan['id']}\""
            )

        # IP addresses
        lines += ["", "# ── 5. IP Addresses ─────────────────────────────"]
        has_ip = False
        for vlan in vlans:
            if vlan["ip"]:
                has_ip = True
                prefix = vlan["ip"].rsplit(".", 1)[0]
                lines.append(
                    f"/ip address add address={vlan['ip']}/24 "
                    f"interface={vlan['name']} comment=\"Gateway VLAN{vlan['id']}\""
                )

        if not has_ip:
            lines.append("# (tidak ada IP yang dikonfigurasi)")

        # DHCP per VLAN
        if p["add_dhcp"]:
            lines += ["", "# ── 6. DHCP Server per VLAN ─────────────────────"]
            for vlan in vlans:
                if not vlan["ip"]:
                    continue
                prefix = vlan["ip"].rsplit(".", 1)[0]
                pool_name = f"pool-{vlan['name']}"
                lines += [
                    f"/ip pool add name={pool_name} ranges={prefix}.10-{prefix}.254",
                    f"/ip dhcp-server add name=dhcp-{vlan['name']} "
                    f"interface={vlan['name']} address-pool={pool_name} disabled=no",
                    f"/ip dhcp-server network add address={prefix}.0/24 "
                    f"gateway={vlan['ip']} dns-server={vlan['ip']},8.8.8.8",
                    "",
                ]

        # Firewall inter-VLAN
        if p["add_fw"] and len(vlans) > 1:
            lines += [
                "# ── 7. Firewall Inter-VLAN ───────────────────────",
                "/interface list",
                "add name=VLAN-ALL",
                "/interface list member",
            ]
            for vlan in vlans:
                lines.append(f"add interface={vlan['name']} list=VLAN-ALL")

            lines += [
                "",
                "/ip firewall filter",
                "add chain=forward connection-state=established,related action=accept "
                'comment="[VLAN] Accept established"',
                "add chain=forward in-interface-list=VLAN-ALL out-interface-list=VLAN-ALL "
                'action=drop comment="[VLAN] Block inter-VLAN by default"',
                "",
                "# Tambahkan exception inter-VLAN sesuai kebutuhan, contoh:",
                "# /ip firewall filter add chain=forward "
                'in-interface=vlan10 out-interface=vlan20 action=accept comment="VLAN10→VLAN20 allowed"',
            ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class BondingGenerator(BaseGenerator):
    TITLE = "Bonding / Link Aggregation (LACP)"

    def collect_params(self):
        c = self.cli
        c.info("Bonding — gabungkan beberapa interface untuk redundancy/throughput\n")

        bond_name = c.prompt("Nama bonding interface", default="bond0")

        slaves = []
        c.info("Masukkan slave interfaces (min 2, kosong=selesai):")
        while True:
            iface = c.prompt(f"Slave interface #{len(slaves)+1}", default="" if len(slaves) >= 2 else f"ether{len(slaves)+1}", required=len(slaves) < 2)
            if not iface:
                break
            slaves.append(iface)

        mode = c.prompt_choice("Mode bonding", [
            ("802.3ad",           "802.3ad LACP (perlu switch support — throughput + redundancy)"),
            ("active-backup",     "Active-Backup (failover saja — switch biasa support)"),
            ("balance-rr",        "Balance Round Robin (throughput, tanpa switch support)"),
            ("balance-xor",       "Balance XOR (hash-based)"),
            ("broadcast",         "Broadcast (semua interface sekaligus)"),
        ], default=1)

        lacp_rate = "fast"
        hash_policy = "layer-2-and-3"
        if mode == "802.3ad":
            lacp_rate   = c.prompt_choice("LACP rate", [("fast","Fast (1s)"),("slow","Slow (30s)")], default=1)
            hash_policy = c.prompt_choice("Transmit hash policy", [
                ("layer-2",        "Layer 2 (MAC)"),
                ("layer-2-and-3",  "Layer 2+3 (MAC+IP) — recommended"),
                ("layer-3-and-4",  "Layer 3+4 (IP+Port)"),
            ], default=2)

        bond_ip  = c.prompt("IP address bonding (kosong=skip)", default="", required=False)
        mii_int  = c.prompt("MII monitoring interval (ms)", default="100")
        comment  = c.prompt("Comment", default="Bond uplink")

        return {
            "name": bond_name,
            "slaves": slaves,
            "mode": mode,
            "lacp_rate": lacp_rate,
            "hash": hash_policy,
            "ip": bond_ip,
            "mii": mii_int,
            "comment": comment,
        }

    def generate(self, p):
        slaves_str = ",".join(p["slaves"])
        mode = p["mode"]

        extra = ""
        if mode == "802.3ad":
            extra = (
                f" lacp-rate={p['lacp_rate']}"
                f" transmit-hash-policy={p['hash']}"
            )

        lines = [self._header_comment(self.TITLE, [
            f"Interface : {p['name']}",
            f"Slaves    : {slaves_str}",
            f"Mode      : {mode}",
        ]), ""]

        lines += [
            "# ── Bonding Interface ────────────────────────────",
            "/interface bonding",
            f"add name={p['name']} \\",
            f"  slaves={slaves_str} \\",
            f"  mode={mode} \\",
            f"  mii-interval={p['mii']}ms{extra} \\",
            f'  comment="{p["comment"]}"',
            "",
        ]

        if p["ip"]:
            lines += [
                "# ── IP Address ───────────────────────────────────",
                f"/ip address add address={p['ip']} interface={p['name']} comment=\"Bond IP\"",
                "",
            ]

        lines += [
            "# ── Verifikasi ───────────────────────────────────",
            f"# /interface bonding monitor {p['name']}",
            "# → cek active-slave, link per slave",
            "",
            "# !! Konfigurasi switch (jika LACP 802.3ad):",
            "# Port-channel / LAG / EtherChannel harus aktif di switch.",
            "# Konsultasikan dokumentasi switch kamu.",
        ]

        return "\n".join(lines)
