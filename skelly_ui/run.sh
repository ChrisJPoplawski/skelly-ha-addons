#!/usr/bin/env bash
set -euo pipefail

# Keep BLE UI current each start
if [ ! -d "/opt/skelly/ble-ui/.git" ]; then
  git clone --depth 1 https://github.com/tinkertims/tinkertims.github.io /opt/skelly/ble-ui || true
else
  git -C /opt/skelly/ble-ui fetch --depth 1 origin main || true
  git -C /opt/skelly/ble-ui reset --hard origin/main || true
fi

# Audio backend for VLC (ignore if already running)
pulseaudio --start || true

# Bind for HA Ingress
export SKELLY_BIND_HOST="0.0.0.0"
export SKELLY_PORT="8099"

cd /opt/skelly
. /opt/venv/bin/activate
python app.py
