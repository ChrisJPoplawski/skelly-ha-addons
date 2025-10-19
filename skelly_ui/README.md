# Home Assistant Add-on: Skelly UI
Place this folder under `/addons/skelly_ui/` on your Home Assistant host.
Then go to Add-on Store → Refresh → Install the "Skelly UI" add-on → Start → Open Web UI.

- Ingress: enabled (opens within HA)
- BLE UI: clones tinkertims.github.io at first start (can be disabled in options)
- Audio/BT: `host_network: true` and `host_dbus: true` allow access to host services
