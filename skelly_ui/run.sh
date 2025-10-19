#!/usr/bin/env bash
set -euo pipefail
source /usr/lib/bashio/bashio.sh

WITH_BLE=$(bashio::config 'with_ble_ui' || echo true)

if [ "$WITH_BLE" = "true" ] && [ ! -d "/opt/skelly/ble-ui" ]; then
  bashio::log.info "Cloning tinkertims.github.io into /opt/skelly/ble-ui (first run)"
  git clone https://github.com/tinkertims/tinkertims.github.io /opt/skelly/ble-ui || true
fi

pulseaudio --start || true

cd /opt/skelly
source /opt/venv/bin/activate

export SKELLY_BIND_HOST="0.0.0.0"
export SKELLY_PORT="8099"

python app.py
