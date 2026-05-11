"""
Main Menu — routing ke semua generator
"""

import sys
import os
from utils.cli import Colors


class MainMenu:

    def __init__(self, cli):
        self.cli = cli
        self._gen_map = None

    def _get_gen_map(self):
        if self._gen_map is not None:
            return self._gen_map

        # lazy import semua generator
        from generators.load_balance import LoadBalancePCC, LoadBalanceNTH, LoadBalanceECMP
        from generators.routing import FailoverGenerator, StaticRouteGenerator
        from generators.nat import PortForwardGenerator
        from generators.qos import (SimpleQueueGenerator, SimpleQueueSharedGenerator,
                                     QueueTreeGenerator, PCQGenerator, BurstCalculator)
        from generators.firewall import FirewallHardeningGenerator, BlockSiteGenerator, PortKnockGenerator
        from generators.hotspot import HotspotWizard, PPPUserGenerator, HotspotUserGenerator
        from generators.vpn import WireGuardGenerator, VPNRemoteGenerator
        from generators.dns import DoHGenerator
        from generators.monitoring import NetwatchGenerator
        from generators.interface import VLANGenerator, BondingGenerator
        from generators.system import TimezoneGenerator, HardeningGenerator, BackupMailGenerator

        self._gen_map = {
            "pcc":          LoadBalancePCC,
            "nth":          LoadBalanceNTH,
            "ecmp":         LoadBalanceECMP,
            "failover":     FailoverGenerator,
            "static-route": StaticRouteGenerator,
            "port-forward": PortForwardGenerator,
            "queue":        SimpleQueueGenerator,
            "queue-shared": SimpleQueueSharedGenerator,
            "queue-tree":   QueueTreeGenerator,
            "pcq":          PCQGenerator,
            "burst":        BurstCalculator,
            "firewall":     FirewallHardeningGenerator,
            "block-site":   BlockSiteGenerator,
            "port-knock":   PortKnockGenerator,
            "hotspot":      HotspotWizard,
            "ppp-user":     PPPUserGenerator,
            "hotspot-user": HotspotUserGenerator,
            "wireguard":    WireGuardGenerator,
            "vpn-remote":   VPNRemoteGenerator,
            "doh":          DoHGenerator,
            "netwatch":     NetwatchGenerator,
            "vlan":         VLANGenerator,
            "bonding":      BondingGenerator,
            "timezone":     TimezoneGenerator,
            "hardening":    HardeningGenerator,
            "backup-mail":  BackupMailGenerator,
        }
        return self._gen_map

    def run_generator(self, key):
        gen_map = self._get_gen_map()
        key = key.lower().strip()
        if key not in gen_map:
            self.cli.error(f"Generator '{key}' tidak ditemukan.")
            self.cli.info("Gunakan --list untuk melihat semua generator.")
            sys.exit(1)
        gen_class = gen_map[key]
        gen = gen_class(self.cli)
        gen.run()

    def show(self):
        c = self.cli
        MENU_CATEGORIES = [
            ("⚡  LOAD BALANCING & ROUTING", [
                ("1",  "pcc",          "Load Balancing PCC"),
                ("2",  "nth",          "Load Balancing NTH"),
                ("3",  "ecmp",         "Load Balancing ECMP"),
                ("4",  "failover",     "Failover Recursive Gateway"),
                ("5",  "static-route", "Static Routing (YouTube/TikTok/dll)"),
            ]),
            ("📊  QoS & QUEUE", [
                ("6",  "queue",        "Simple Queue + Token Bucket"),
                ("7",  "queue-shared", "Simple Queue Bandwidth Shared"),
                ("8",  "queue-tree",   "Queue Tree Bandwidth Shared"),
                ("9",  "pcq",          "PCQ Generator"),
                ("10", "burst",        "Burst Limit Calculator"),
            ]),
            ("🔒  SECURITY & FIREWALL", [
                ("11", "firewall",     "Firewall Hardening Template"),
                ("12", "block-site",   "Block Website Generator"),
                ("13", "port-knock",   "Port Knocking ICMP"),
                ("14", "hardening",    "Full System Hardening Checklist"),
            ]),
            ("🔀  NAT & PORT FORWARD", [
                ("15", "port-forward", "Port Forwarding dengan NAT"),
            ]),
            ("📶  HOTSPOT & PPP", [
                ("16", "hotspot",      "Hotspot Wizard"),
                ("17", "ppp-user",     "PPP Secrets User Generator"),
                ("18", "hotspot-user", "Hotspot User Generator"),
            ]),
            ("🔐  VPN", [
                ("19", "wireguard",    "WireGuard VPN Setup"),
                ("20", "vpn-remote",   "VPN Remote SSTP/L2TP/PPTP"),
            ]),
            ("🌐  DNS & MONITORING", [
                ("21", "doh",          "DNS over HTTPS (DoH)"),
                ("22", "netwatch",     "Netwatch Monitoring + Alert"),
            ]),
            ("🔌  INTERFACE & SYSTEM", [
                ("23", "vlan",         "VLAN Bridge Setup"),
                ("24", "bonding",      "Bonding / LACP Interface"),
                ("25", "timezone",     "Timezone Indonesia"),
                ("26", "backup-mail",  "Auto Backup ke Email"),
            ]),
        ]

        num_to_key = {}
        for _, items in MENU_CATEGORIES:
            for num, key, _ in items:
                num_to_key[num] = key

        while True:
            # clear screen
            os.system("clear" if os.name != "nt" else "cls")

            # reprint banner setiap loop
            from utils.banner import print_banner
            print_banner(c)

            for cat_label, items in MENU_CATEGORIES:
                print(c.color(f"\n  {cat_label}", Colors.CYAN, Colors.BOLD))
                for num, key, label in items:
                    num_str = c.color(f"{num:>3}", Colors.YELLOW)
                    print(f"   {num_str}.  {label}")

            print(c.color("\n   0.  Keluar", Colors.RED))
            print()

            raw = c.prompt("Pilih menu", required=False)
            if not raw or raw == "0":
                print(c.color("\n  Sampai jumpa! 👋\n", Colors.CYAN))
                sys.exit(0)

            if raw not in num_to_key:
                c.error(f"Pilihan '{raw}' tidak valid.")
                input(c.color("  Tekan Enter untuk lanjut...", Colors.GRAY))
                continue

            key = num_to_key[raw]
            try:
                self.run_generator(key)
            except KeyboardInterrupt:
                print()
                c.warning("Generator dibatalkan.")

            input(c.color("\n  Tekan Enter untuk kembali ke menu...", Colors.GRAY))
