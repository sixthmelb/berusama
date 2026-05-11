"""
QoS Generators: Simple Queue, Queue Tree, PCQ, Burst Calculator
"""

from generators import BaseGenerator


def _bw(val, unit):
    """Format: 10M, 512k, 1G"""
    return f"{val}{unit}"


class SimpleQueueGenerator(BaseGenerator):
    """Simple Queue + Token Bucket per client"""

    TITLE = "Simple Queue + Token Bucket"

    def collect_params(self):
        c = self.cli
        c.info("Generate Simple Queue untuk bandwidth management per client/IP\n")

        queue_name = c.prompt("Nama queue (prefix)", default="Client")
        clients    = []

        bulk_mode = c.prompt_confirm("Mode bulk? (input banyak client sekaligus)", default=False)

        if bulk_mode:
            c.info("Format: IP,Download,Upload,Nama (pisah baris, kosong selesai)")
            c.info("Contoh: 192.168.1.10,10M,5M,PC-Lobby")
            while True:
                raw = c.prompt("Entry", required=False)
                if not raw:
                    break
                parts = [x.strip() for x in raw.split(",")]
                if len(parts) < 3:
                    c.error("Format salah! Gunakan: IP,Download,Upload[,Nama]")
                    continue
                clients.append({
                    "ip": parts[0],
                    "dl": parts[1],
                    "ul": parts[2],
                    "name": parts[3] if len(parts) > 3 else parts[0],
                })
        else:
            while True:
                c.info(f"\n─── Client #{len(clients)+1} ───")
                ip   = c.prompt_ip("IP Address client", default=f"192.168.1.{len(clients)+10}")
                name = c.prompt("Nama queue", default=f"{queue_name}-{len(clients)+1}")
                dl   = c.prompt("Download limit (contoh: 10M, 512k, 1G)", default="10M")
                ul   = c.prompt("Upload limit", default="5M")
                clients.append({"ip": ip, "dl": dl, "ul": ul, "name": name})
                if not c.prompt_confirm("Tambah client lagi?", default=False):
                    break

        interface  = c.prompt("Interface queue (target)", default="bridge-LAN")
        add_burst  = c.prompt_confirm("Tambahkan Burst limit?", default=False)

        burst_params = {}
        if add_burst:
            c.info("Burst memungkinkan bandwidth melebihi limit untuk waktu singkat")
            burst_params["burst_time"]  = c.prompt("Burst time (detik)", default="8")
            burst_params["burst_ratio"] = c.prompt_int("Burst ratio (% dari limit, misal 150 = 1.5x)", default=150, min_val=101, max_val=500)

        return {
            "clients": clients,
            "interface": interface,
            "add_burst": add_burst,
            "burst_params": burst_params,
        }

    def generate(self, p):
        clients = p["clients"]
        iface   = p["interface"]

        lines = [self._header_comment(self.TITLE, [
            f"Interface : {iface}",
            f"Clients   : {len(clients)} entries",
        ]), ""]

        lines.append("/queue simple")

        for cl in clients:
            dl   = cl["dl"]
            ul   = cl["ul"]
            name = cl["name"]
            ip   = cl["ip"]

            burst_dl = burst_ul = burst_dl_thresh = burst_ul_thresh = burst_time = ""
            if p["add_burst"] and p["burst_params"]:
                ratio = p["burst_params"]["burst_ratio"] / 100
                btime = p["burst_params"]["burst_time"]

                def scale_bw(bw_str):
                    """Scale bandwidth untuk burst"""
                    import re
                    m = re.match(r'^(\d+(?:\.\d+)?)([kKmMgG]?)$', bw_str)
                    if m:
                        val  = float(m.group(1))
                        unit = m.group(2) or "M"
                        burst_val = int(val * ratio)
                        thresh_val = int(val * 0.8)  # 80% limit = burst threshold
                        return f"{burst_val}{unit}", f"{thresh_val}{unit}"
                    return bw_str, bw_str

                bdl, tdl = scale_bw(dl)
                bul, tul = scale_bw(ul)
                burst_part = (
                    f" burst-limit={bdl}/{bul}"
                    f" burst-threshold={tdl}/{tul}"
                    f" burst-time={btime}s/{btime}s"
                )
            else:
                burst_part = ""

            lines.append(
                f'add name="{name}" target={ip}/32 '
                f'max-limit={dl}/{ul}'
                f'{burst_part}'
                f' interface={iface}'
                f' comment="{name}"'
            )

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class SimpleQueueSharedGenerator(BaseGenerator):
    """Simple Queue — Bandwidth Shared Up-To"""

    TITLE = "Simple Queue Bandwidth Shared Up-To"

    def collect_params(self):
        c = self.cli
        c.info("Shared bandwidth — semua client share satu pool bandwidth\n")

        parent_name = c.prompt("Nama parent queue", default="Shared-Pool")
        parent_dl   = c.prompt("Total download pool (misal: 100M)", default="100M")
        parent_ul   = c.prompt("Total upload pool", default="50M")

        per_dl = c.prompt("Max download per client", default="20M")
        per_ul = c.prompt("Max upload per client", default="10M")

        subnet = c.prompt_subnet("Subnet target", default="192.168.1.0/24")
        iface  = c.prompt("Interface", default="bridge-LAN")

        return {
            "parent_name": parent_name,
            "parent_dl": parent_dl,
            "parent_ul": parent_ul,
            "per_dl": per_dl,
            "per_ul": per_ul,
            "subnet": subnet,
            "iface": iface,
        }

    def generate(self, p):
        lines = [self._header_comment(self.TITLE), ""]
        lines += [
            "/queue simple",
            f'add name="{p["parent_name"]}" '
            f'target={p["subnet"]} '
            f'max-limit={p["parent_dl"]}/{p["parent_ul"]} '
            f'interface={p["iface"]} '
            f'comment="Parent pool — shared {p["parent_dl"]}/{p["parent_ul"]}"',
            "",
            "# Untuk per-client (child dari parent di atas):",
            f'# add name="Client-1" target=192.168.1.x/32 '
            f'parent="{p["parent_name"]}" '
            f'max-limit={p["per_dl"]}/{p["per_ul"]} '
            f'limit-at=1M/512k',
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class QueueTreeGenerator(BaseGenerator):
    """Queue Tree — Bandwidth Shared dengan mangle marking"""

    TITLE = "Queue Tree Bandwidth Shared"

    def collect_params(self):
        c = self.cli
        c.info("Queue Tree — lebih fleksibel, perlu mangle packet marking\n")

        wan_iface = c.prompt("Interface WAN (untuk global-in/out)", default="ether1")
        lan_iface = c.prompt("Interface LAN", default="bridge-LAN")
        total_dl  = c.prompt("Total bandwidth download", default="100M")
        total_ul  = c.prompt("Total bandwidth upload", default="50M")

        priorities = c.prompt_confirm("Tambahkan priority queue (VoIP, gaming, browsing)?", default=True)

        return {
            "wan": wan_iface,
            "lan": lan_iface,
            "total_dl": total_dl,
            "total_ul": total_ul,
            "priorities": priorities,
        }

    def generate(self, p):
        wan = p["wan"]
        lan = p["lan"]

        lines = [self._header_comment(self.TITLE, [
            f"WAN: {wan}", f"LAN: {lan}",
            f"Download: {p['total_dl']} | Upload: {p['total_ul']}",
        ]), ""]

        if p["priorities"]:
            lines += [
                "# ── Mangle — Packet Marking ──────────────────────",
                "/ip firewall mangle",
                f'add chain=forward in-interface={lan} protocol=udp dst-port=5060,10000-20000 \\',
                '  action=mark-packet new-packet-mark=voip passthrough=no comment="VoIP/SIP"',
                f'add chain=forward in-interface={lan} dst-port=80,443 protocol=tcp \\',
                '  action=mark-packet new-packet-mark=browsing passthrough=no comment="Browsing"',
                f'add chain=forward in-interface={lan} \\',
                '  action=mark-packet new-packet-mark=other passthrough=no comment="Other traffic"',
                "",
            ]

        lines += [
            "# ── Queue Type (PCQ) ─────────────────────────────",
            "/queue type",
            'add name=pcq-download kind=pcq pcq-classifier=dst-address pcq-rate=0',
            'add name=pcq-upload   kind=pcq pcq-classifier=src-address pcq-rate=0',
            "",
            "# ── Queue Tree ───────────────────────────────────",
            "/queue tree",
            f'add name="Download-Total" parent={wan} max-limit={p["total_dl"]} comment="Total Download"',
            f'add name="Upload-Total"   parent={lan} max-limit={p["total_ul"]} comment="Total Upload"',
            "",
        ]

        if p["priorities"]:
            lines += [
                f'add name="DL-VoIP"     parent=Download-Total priority=1 queue=pcq-download \\',
                '  packet-mark=voip     max-limit=10M comment="Download VoIP"',
                f'add name="DL-Browsing" parent=Download-Total priority=4 queue=pcq-download \\',
                '  packet-mark=browsing max-limit=0   comment="Download Browsing"',
                f'add name="DL-Other"    parent=Download-Total priority=8 queue=pcq-download \\',
                '  packet-mark=other    max-limit=0   comment="Download Other"',
                "",
                f'add name="UL-VoIP"     parent=Upload-Total priority=1 queue=pcq-upload \\',
                '  packet-mark=voip     max-limit=5M  comment="Upload VoIP"',
                f'add name="UL-Browsing" parent=Upload-Total priority=4 queue=pcq-upload \\',
                '  packet-mark=browsing max-limit=0   comment="Upload Browsing"',
                f'add name="UL-Other"    parent=Upload-Total priority=8 queue=pcq-upload \\',
                '  packet-mark=other    max-limit=0   comment="Upload Other"',
            ]
        else:
            lines += [
                f'add name="DL-All" parent=Download-Total queue=pcq-download max-limit=0',
                f'add name="UL-All" parent=Upload-Total   queue=pcq-upload   max-limit=0',
            ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class PCQGenerator(BaseGenerator):
    """PCQ Queue Type Generator"""

    TITLE = "PCQ (Per Connection Queue) Generator"

    def collect_params(self):
        c = self.cli
        c.info("PCQ — fair-use per client secara otomatis\n")

        dl_rate  = c.prompt("PCQ rate download per client (0 = no limit)", default="0")
        ul_rate  = c.prompt("PCQ rate upload per client (0 = no limit)", default="0")
        dl_limit = c.prompt("PCQ total limit download (bytes, 0 = unlimited)", default="0")
        ul_limit = c.prompt("PCQ total limit upload", default="0")
        burst    = c.prompt_confirm("Tambahkan burst config?", default=False)

        burst_params = {}
        if burst:
            burst_params["dl_burst"]  = c.prompt("Burst rate download (misal: 5M)", default="5M")
            burst_params["ul_burst"]  = c.prompt("Burst rate upload", default="2M")
            burst_params["burst_time"]= c.prompt("Burst time (detik)", default="8")
            burst_params["dl_thresh"] = c.prompt("Burst threshold download (misal: 4M)", default="4M")
            burst_params["ul_thresh"] = c.prompt("Burst threshold upload", default="1M")

        return {
            "dl_rate": dl_rate,
            "ul_rate": ul_rate,
            "dl_limit": dl_limit,
            "ul_limit": ul_limit,
            "burst": burst,
            "burst_params": burst_params,
        }

    def generate(self, p):
        bp = p["burst_params"]

        def _pcq(name, classifier, rate, total_limit, burst_rate="", burst_thresh="", burst_time=""):
            b = ""
            if burst_rate:
                b = f" pcq-burst-rate={burst_rate} pcq-burst-threshold={burst_thresh} pcq-burst-time={burst_time}s"
            return (
                f'add name={name} kind=pcq '
                f'pcq-classifier={classifier} '
                f'pcq-rate={rate} '
                f'pcq-total-limit={total_limit}'
                f'{b}'
            )

        lines = [self._header_comment(self.TITLE), "", "/queue type"]

        if p["burst"] and bp:
            lines.append(_pcq("pcq-download", "dst-address", p["dl_rate"], p["dl_limit"],
                               bp["dl_burst"], bp["dl_thresh"], bp["burst_time"]))
            lines.append(_pcq("pcq-upload",   "src-address", p["ul_rate"], p["ul_limit"],
                               bp["ul_burst"], bp["ul_thresh"], bp["burst_time"]))
        else:
            lines.append(_pcq("pcq-download", "dst-address", p["dl_rate"], p["dl_limit"]))
            lines.append(_pcq("pcq-upload",   "src-address", p["ul_rate"], p["ul_limit"]))

        lines += [
            "",
            "# Gunakan pcq-download/pcq-upload di Queue Tree atau Simple Queue:",
            "# /queue tree add name=DL parent=<WAN> queue=pcq-download max-limit=<TOTAL>",
            "# /queue tree add name=UL parent=<LAN> queue=pcq-upload   max-limit=<TOTAL>",
        ]

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────


class BurstCalculator(BaseGenerator):
    """Burst Limit Calculator untuk Simple Queue"""

    TITLE = "Burst Limit Calculator"

    def collect_params(self):
        c = self.cli
        c.info("Hitung burst parameters secara otomatis\n")
        c.info("Referensi: MikroTik token bucket burst algorithm")
        c.info("  burst-limit  = bandwidth sesaat saat burst aktif")
        c.info("  burst-thresh = jika usage < threshold, burst bisa aktif")
        c.info("  burst-time   = window waktu untuk rata-rata\n")

        dl_limit  = c.prompt_int("Download limit (Mbps)", default=10, min_val=1)
        ul_limit  = c.prompt_int("Upload limit (Mbps)", default=5, min_val=1)
        burst_mul = c.prompt_int("Burst multiplier (%, contoh: 150 = 1.5x limit)", default=150, min_val=101)
        burst_time = c.prompt_int("Burst time (detik)", default=8, min_val=4)
        name      = c.prompt("Nama queue (untuk script output)", default="Client-1")
        target_ip = c.prompt("Target IP", default="192.168.1.100")

        return {
            "dl_limit": dl_limit,
            "ul_limit": ul_limit,
            "burst_mul": burst_mul,
            "burst_time": burst_time,
            "name": name,
            "target": target_ip,
        }

    def generate(self, p):
        dl        = p["dl_limit"]
        ul        = p["ul_limit"]
        mul       = p["burst_mul"] / 100
        bt        = p["burst_time"]

        burst_dl  = int(dl * mul)
        burst_ul  = int(ul * mul)
        thresh_dl = int(dl * 0.75)  # 75% dari limit
        thresh_ul = int(ul * 0.75)

        # Rata-rata harus dibawah limit selama burst_time/2 agar burst aktif lagi
        avg_dl    = int(dl * 0.5)
        avg_ul    = int(ul * 0.5)

        lines = [
            self._header_comment(self.TITLE, [
                f"Download limit : {dl}M → Burst: {burst_dl}M (Threshold: {thresh_dl}M)",
                f"Upload limit   : {ul}M → Burst: {burst_ul}M (Threshold: {thresh_ul}M)",
                f"Burst time     : {bt}s",
            ]),
            "",
            "# ── Hasil Kalkulasi ─────────────────────────────────",
            f"# Download : limit={dl}M, burst-limit={burst_dl}M, burst-threshold={thresh_dl}M, burst-time={bt}s",
            f"# Upload   : limit={ul}M, burst-limit={burst_ul}M, burst-threshold={thresh_ul}M, burst-time={bt}s",
            "",
            "# ── Script Simple Queue ──────────────────────────────",
            "/queue simple",
            f'add name="{p["name"]}" \\',
            f'  target={p["target"]}/32 \\',
            f'  max-limit={dl}M/{ul}M \\',
            f'  burst-limit={burst_dl}M/{burst_ul}M \\',
            f'  burst-threshold={thresh_dl}M/{thresh_ul}M \\',
            f'  burst-time={bt}s/{bt}s \\',
            f'  comment="{p["name"]} — burst {burst_dl}M/{burst_ul}M"',
            "",
            "# ── Penjelasan Burst ─────────────────────────────────",
            f"# Jika rata-rata penggunaan client < {thresh_dl}M/{thresh_ul}M selama {bt}s terakhir,",
            f"# maka client boleh burst hingga {burst_dl}M/{burst_ul}M.",
            f"# Begitu rata-rata melewati threshold, burst dihentikan.",
        ]

        return "\n".join(lines)
