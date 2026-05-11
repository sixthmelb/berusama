#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║        MikroTik RouterOS Auto-Configurator CLI v1.0              ║
║                                                                  ║
║        Python CLI Edition — by @renefosterr                      ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from utils.cli import CLI
from utils.banner import print_banner
from utils.menu import MainMenu


def main():
    parser = argparse.ArgumentParser(
        prog="mtik-autoconfig",
        description="MikroTik RouterOS Script Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py                          # Interactive mode
  python main.py --gen pcc               # Load Balance PCC
  python main.py --gen failover          # Failover Recursive
  python main.py --gen queue             # Simple Queue
  python main.py --gen firewall          # Firewall Hardening
  python main.py --gen hotspot           # Hotspot Wizard
  python main.py --gen port-forward      # Port Forward NAT
  python main.py --gen wireguard         # WireGuard VPN
  python main.py --gen doh               # DNS over HTTPS
  python main.py --gen netwatch          # Netwatch Monitoring
  python main.py --gen block-site        # Block Website
  python main.py --gen vlan              # VLAN Setup
  python main.py --list                  # List semua generator
        """
    )
    parser.add_argument("--gen", metavar="TYPE", help="Langsung jalankan generator tertentu")
    parser.add_argument("--list", action="store_true", help="List semua generator yang tersedia")
    parser.add_argument("--no-color", action="store_true", help="Nonaktifkan warna output")
    parser.add_argument("--version", action="version", version="MikroTik AutoConfig CLI v1.0")

    args = parser.parse_args()

    cli = CLI(no_color=args.no_color)

    if args.list:
        cli.list_generators()
        return

    print_banner(cli)

    if args.gen:
        menu = MainMenu(cli)
        menu.run_generator(args.gen)
    else:
        menu = MainMenu(cli)
        menu.show()


if __name__ == "__main__":
    main()
