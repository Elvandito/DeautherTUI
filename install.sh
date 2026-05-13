#!/bin/bash
# Installs 'deauther' as a system-wide command so you can run: sudo deauther

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3)"
APP="$SCRIPT_DIR/deauther.py"

cat > /usr/local/bin/deauther << EOF
#!/bin/bash
exec sudo "$PYTHON" "$APP" "\$@"
EOF

chmod +x /usr/local/bin/deauther
echo "[OK] Installed: sudo deauther is now available."
