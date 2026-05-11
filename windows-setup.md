# Tutorial Setup MikroTik RouterOS Auto-Configurator CLI di Windows

## Persyaratan Sistem
- **Sistem Operasi**: Windows 10 atau lebih baru (direkomendasikan Windows 11)
- **Python**: Versi 3.7 atau lebih tinggi
- **Tidak ada dependensi eksternal** (tools ini menggunakan pure Python stdlib)

## Langkah 1: Install Python
Jika Python belum terinstall di sistem Anda:

1. Buka browser dan kunjungi [python.org](https://www.python.org/downloads/).
2. Download installer Python terbaru (versi 3.7+).
3. Jalankan installer sebagai Administrator.
4. Pastikan centang opsi **"Add Python to PATH"** selama instalasi.
5. Klik **Install Now** dan ikuti instruksi.

Untuk verifikasi instalasi:
- Buka Command Prompt atau PowerShell.
- Jalankan perintah: `python --version`
- Output harus menampilkan versi Python (contoh: `Python 3.11.5`).

Jika `python` tidak dikenali, coba `py --version` atau restart terminal.

## Langkah 2: Download Tools
1. Download file ZIP dari repository GitHub (atau clone jika Anda punya Git):
   - Via ZIP: Kunjungi [repository GitHub](https://github.com/username/mtik-autoconfig) dan klik **Code > Download ZIP**.
   - Via Git: Jalankan `git clone https://github.com/username/mtik-autoconfig.git` di Command Prompt/PowerShell.

2. Ekstrak file ZIP ke folder pilihan, misalnya `C:\Users\YourName\mtik-autoconfig`.

## Langkah 3: Jalankan Tools
1. Buka Command Prompt atau PowerShell.
2. Navigasi ke folder tools: `cd C:\Users\YourName\mtik-autoconfig`.
3. Jalankan mode interaktif: `python main.py`.
4. Atau jalankan generator langsung: `python main.py --gen pcc` (contoh untuk Load Balance PCC).

## Contoh Penggunaan
- **List semua generator**: `python main.py --list`
- **Generate script tanpa warna** (untuk logging): `python main.py --no-color --gen firewall`
- **Simpan output ke file**: Saat tools meminta, pilih "y" untuk menyimpan sebagai `.rsc`.

## Tips Khusus Windows
- **Path Issues**: Jika `python` tidak ditemukan, pastikan Python ditambahkan ke PATH sistem (lihat Environment Variables di System Properties).
- **Permissions**: Jalankan Command Prompt sebagai Administrator jika ada error akses file.
- **Antivirus**: Beberapa antivirus mungkin memblokir eksekusi Python—tambah exception untuk folder tools.
- **PowerShell vs CMD**: Kedua terminal mendukung, tapi PowerShell lebih modern dan direkomendasikan.
- **Troubleshooting**: Jika ada error "ModuleNotFoundError", pastikan Anda di folder yang benar dan Python versi 3.7+.

## Troubleshooting Umum
- **Error: 'python' is not recognized**: Restart terminal atau reinstall Python dengan opsi PATH.
- **Error: Permission denied**: Jalankan sebagai Administrator.
- **Tools tidak responsif**: Pastikan tidak ada firewall yang memblokir, atau coba mode `--no-color`.

Dengan setup ini, Anda siap menggunakan tools untuk generate konfigurasi MikroTik RouterOS di Windows!