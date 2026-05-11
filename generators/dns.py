"""
DNS Generator: DoH (DNS over HTTPS)
"""

from generators import BaseGenerator

DOH_SERVERS = {
    "cloudflare":  ("https://cloudflare-dns.com/dns-query", "Cloudflare — 1.1.1.1 (cepat & privacy)"),
    "google":      ("https://dns.google/dns-query", "Google — 8.8.8.8 (reliable)"),
    "quad9":       ("https://dns.quad9.net/dns-query", "Quad9 — blocking malware/phishing"),
    "adguard":     ("https://dns.adguard.com/dns-query", "AdGuard — ad blocking"),
    "nextdns":     ("https://dns.nextdns.io/<YOUR_ID>", "NextDNS — custom filtering"),
    "custom":      ("", "Custom DoH URL"),
}


class DoHGenerator(BaseGenerator):
    TITLE = "DNS over HTTPS (DoH) Setup"

    def collect_params(self):
        c = self.cli
        c.info("Setup DNS over HTTPS — enkripsi DNS query via HTTPS\n")
        c.warning("DoH membutuhkan RouterOS v6.47+ untuk fitur DoH\n")

        choices = [(k, v[1]) for k, v in DOH_SERVERS.items()]
        provider = c.prompt_choice("Pilih DoH provider", choices, default=1)

        if provider == "custom":
            doh_url = c.prompt("DoH URL")
        else:
            doh_url = DOH_SERVERS[provider][0]

        verify_cert = c.prompt_confirm("Verifikasi certificate server?", default=True)
        cache_size  = c.prompt_int("DNS cache size (entries)", default=2048, min_val=512)
        allow_remote = c.prompt_confirm("Allow DNS query dari LAN (DNS server)?", default=True)
        max_ttl     = c.prompt("Max TTL cache (detik, 0=unlimited)", default="3600")
        add_fallback = c.prompt_confirm("Tambahkan fallback DNS (jika DoH gagal)?", default=True)

        fallback = []
        if add_fallback:
            fallback.append(c.prompt("Fallback DNS 1", default="1.1.1.1"))
            f2 = c.prompt("Fallback DNS 2 (kosong=skip)", default="8.8.8.8", required=False)
            if f2:
                fallback.append(f2)

        return {
            "provider": provider,
            "url": doh_url,
            "verify": verify_cert,
            "cache": cache_size,
            "allow_remote": allow_remote,
            "max_ttl": max_ttl,
            "fallback": fallback,
        }

    def generate(self, p):
        verify = "yes" if p["verify"] else "no"
        remote = "yes" if p["allow_remote"] else "no"

        lines = [self._header_comment(self.TITLE, [
            f"Provider : {p['provider']}",
            f"URL      : {p['url']}",
        ]), ""]

        # Fetch DoH certificate (harus diambil dulu)
        lines += [
            "# ── LANGKAH 1: Fetch DoH Certificate ─────────────",
            "# Jalankan ini PERTAMA sebelum mengaktifkan DoH:",
        ]
        if p["provider"] == "cloudflare":
            lines.append('/tool fetch url=https://curl.se/ca/cacert.pem mode=https')
            lines.append('/certificate import file-name=cacert.pem passphrase=""')
        lines += [
            "",
            "# ── LANGKAH 2: Konfigurasi DNS ───────────────────",
            "/ip dns set \\",
            f'  use-doh-server="{p["url"]}" \\',
            f'  verify-doh-cert={verify} \\',
            f'  allow-remote-requests={remote} \\',
            f'  cache-size={p["cache"]} \\',
            f'  max-cache-ttl={p["max_ttl"]}',
        ]

        if p["fallback"]:
            servers = ",".join(p["fallback"])
            lines += [
                "",
                "# ── LANGKAH 3: Fallback DNS ──────────────────────",
                f"/ip dns set servers={servers}",
            ]

        lines += [
            "",
            "# ── LANGKAH 4: Test ──────────────────────────────",
            '/ip dns cache flush',
            '# /resolve google.com             → test resolusi',
            '# /ip dns cache print             → lihat cache',
            "",
            "# ── FIREWALL — Block DNS biasa dari LAN (opsional) ──",
            "# Redirect semua DNS ke router (cegah bypass DoH):",
            "/ip firewall nat",
            'add chain=dstnat protocol=udp dst-port=53 !dst-address=<ROUTER_IP> \\',
            '  action=redirect to-ports=53 comment="Redirect DNS to router"',
            'add chain=dstnat protocol=tcp dst-port=53 !dst-address=<ROUTER_IP> \\',
            '  action=redirect to-ports=53 comment="Redirect DNS TCP to router"',
        ]

        return "\n".join(lines)
