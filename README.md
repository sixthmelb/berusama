# MikroTik RouterOS Auto-Configurator CLI

```
  ███╗   ███╗██╗██╗  ██╗██████╗  ██████╗ ████████╗██╗██╗  ██╗
  ████╗ ████║██║██║ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝██║██║ ██╔╝
  ██╔████╔██║██║█████╔╝ ██████╔╝██║   ██║   ██║   ██║█████╔╝
  ██║╚██╔╝██║██║██╔═██╗ ██╔══██╗██║   ██║   ██║   ██║██╔═██╗
  ██║ ╚═╝ ██║██║██║  ██╗██║  ██║╚██████╔╝   ██║   ██║██║  ██╗
  ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═╝
```

**Python CLI tool untuk generate script konfigurasi MikroTik RouterOS secara interaktif.**  
versi CLI dengan Python.

---

## ✨ Fitur

| Kategori | Generator |
|---|---|
| ⚡ Load Balancing | PCC, NTH, ECMP |
| 🛣️ Routing | Failover Recursive, Static Route per website |
| 🔀 NAT | Port Forwarding + Hairpin NAT |
| 📊 QoS | Simple Queue, Queue Tree, PCQ, Burst Calculator |
| 🔒 Security | Firewall Hardening, Block Site, Port Knocking |
| 📶 Hotspot | Hotspot Wizard, PPP User Generator, Hotspot User |
| 🔐 VPN | WireGuard, L2TP/SSTP/PPTP |
| 🌐 DNS | DNS over HTTPS (DoH) |
| 📡 Monitoring | Netwatch + Telegram/Email Alert |
| 🔌 Interface | VLAN Bridge, Bonding/LACP |
| ⚙️ System | Timezone Indonesia, Full Hardening, Auto Backup Email |

**Total: 26 generator, 19 kategori.**

---

## 🚀 Cara Pakai

### Requirement
- Python 3.7+
- Tidak butuh library eksternal (pure stdlib)

### Run Interactive Mode
```bash
python main.py
```

### Run Generator Langsung (non-interactive jump)
```bash
python main.py --gen pcc           # Load Balance PCC
python main.py --gen failover      # Failover Recursive
python main.py --gen queue         # Simple Queue
python main.py --gen firewall      # Firewall Hardening
python main.py --gen hotspot       # Hotspot Wizard
python main.py --gen wireguard     # WireGuard VPN
python main.py --gen netwatch      # Netwatch + Alert
python main.py --gen vlan          # VLAN Setup
python main.py --gen hardening     # Full Hardening
python main.py --gen backup-mail   # Auto Backup Email
```

### List Semua Generator
```bash
python main.py --list
```

### Tanpa Warna (untuk logging/pipe)
```bash
python main.py --no-color
```

---

## 📂 Struktur Project

```
mtik-autoconfig/
├── main.py                     ← Entry point CLI
├── README.md
├── requirements.txt            ← (kosong — pure stdlib)
│
├── utils/
│   ├── cli.py                  ← Color, input, output handler
│   ├── banner.py               ← ASCII art banner
│   └── menu.py                 ← Main menu router
│
└── generators/
    ├── __init__.py             ← BaseGenerator class
    ├── load_balance.py         ← PCC, NTH, ECMP
    ├── routing.py              ← Failover, Static Route
    ├── nat.py                  ← Port Forward
    ├── qos.py                  ← Simple Queue, Queue Tree, PCQ, Burst
    ├── firewall.py             ← Hardening, Block Site, Port Knock
    ├── hotspot.py              ← Hotspot Wizard, PPP/Hotspot User
    ├── vpn.py                  ← WireGuard, VPN Remote
    ├── dns.py                  ← DNS over HTTPS
    ├── monitoring.py           ← Netwatch + Telegram/Email
    ├── interface.py            ← VLAN, Bonding
    └── system.py               ← Timezone, Hardening, Backup Mail
```

---

## 💡 Tips Penggunaan

### Cara Apply Script ke Router

**Via Terminal / SSH:**
```bash
# Copy script ke file .rsc, lalu import di RouterOS:
/import file-name=script.rsc
```

**Via Winbox:**
- New Terminal → paste script langsung

**Via FTP / SCP:**
```bash
scp mtik_*.rsc admin@192.168.1.1:/
# Lalu di router: /import file-name=mtik_*.rsc
```

### Simpan Output ke File
Saat script selesai di-generate, tool akan tanya apakah mau disimpan ke file `.rsc`.  
File disimpan di direktori yang sama dengan working directory.

---

## 🔧 Generator Quick Reference

| Command | Generator |
|---|---|
| `pcc` | Load Balancing PCC (multi-WAN) |
| `nth` | Load Balancing NTH |
| `ecmp` | Load Balancing ECMP (v7+) |
| `failover` | Failover Recursive Gateway |
| `static-route` | Static Route per website/service |
| `port-forward` | Port Forwarding NAT |
| `queue` | Simple Queue + Burst |
| `queue-shared` | Simple Queue Shared Bandwidth |
| `queue-tree` | Queue Tree + PCQ |
| `pcq` | PCQ Type Generator |
| `burst` | Burst Limit Calculator |
| `firewall` | Firewall Hardening Template |
| `block-site` | Block Website (DNS/L7/AddrList) |
| `port-knock` | Port Knocking ICMP |
| `hotspot` | Hotspot Wizard |
| `ppp-user` | PPP Secrets Generator |
| `hotspot-user` | Hotspot User Generator |
| `wireguard` | WireGuard VPN (v7+) |
| `vpn-remote` | L2TP/SSTP/PPTP VPN Server |
| `doh` | DNS over HTTPS |
| `netwatch` | Netwatch + Telegram/Email |
| `vlan` | VLAN Bridge Filtering |
| `bonding` | Bonding/LACP Interface |
| `timezone` | Timezone Indonesia + NTP |
| `hardening` | Full System Hardening |
| `backup-mail` | Auto Backup via Email |

---

## ⚠️ Disclaimer

Script yang di-generate perlu disesuaikan dengan kondisi jaringan aktual kamu.  
**Selalu test di lab/vm sebelum apply ke production.**

---

## 📜 License

MIT License — bebas digunakan dan dimodifikasi.

---


