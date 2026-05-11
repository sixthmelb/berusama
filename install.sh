#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# MikroTik AutoConfig CLI — Quick Install Script
# ─────────────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  ═══════════════════════════════════════════════"
echo "   MikroTik AutoConfig CLI — Install"
echo "  ═══════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  ✗ Python3 tidak ditemukan!"
    echo "    Install: sudo apt install python3   (Debian/Ubuntu)"
    echo "             sudo yum install python3   (CentOS/RHEL)"
    echo "             brew install python3       (macOS)"
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  ✓ Python $PY_VER ditemukan"

# Make executable
chmod +x "$SCRIPT_DIR/main.py"
echo "  ✓ main.py executable"

# Symlink ke /usr/local/bin (opsional, butuh sudo)
if [ "$1" == "--global" ]; then
    sudo ln -sf "$SCRIPT_DIR/main.py" /usr/local/bin/mtik-autoconfig
    echo "  ✓ Symlink dibuat: mtik-autoconfig → /usr/local/bin/"
    echo ""
    echo "  Sekarang bisa run dari mana saja:"
    echo "    mtik-autoconfig"
else
    echo ""
    echo "  Jalankan dengan:"
    echo "    cd $SCRIPT_DIR"
    echo "    python3 main.py"
    echo ""
    echo "  Atau install global (butuh sudo):"
    echo "    bash install.sh --global"
fi

echo ""
echo "  ═══════════════════════════════════════════════"
echo "   Setup selesai! 🎉"
echo "  ═══════════════════════════════════════════════"
echo ""
