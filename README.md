# xdg-desktop-portal-pyrtal

A minimal desktop portal for any Wayland compositor.

Can be used standalone to implement all supported portals or selectively pick them.

## Portals

- Global Shortcuts
  - requires the user to setup exec triggers
- Remote Desktop
  - requires [zwp_virtual_keyboard_v1](https://wayland.app/protocols/virtual-keyboard-unstable-v1)
  - only supports keysym replay
  - should work with wide range of Latin characters (defaults to `--layout=eu`)

Known to work on:
  - labwc (any wlroots based should)
  - COSMIC

## Requirements

- Python 3
- `dbus-fast`
- `pywayland` (optional, required for Remote Desktop) 
- `xkbcommon` (optional, required for Remote Desktop)

Install the required dependencies on Debian/Ubuntu:
```bash
sudo apt install python3-dbus-fast python3-pywayland python3-xkbcommon
```

Install the required dependencies on Fedora:

```bash
sudo dnf install python3-dbus-fast python3-pywayland python3-xkbcommon
```

## Usage
```
usage: python3 -m pyrtal [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] {portal,list,activate,deactivate,trigger} ...

pyrtal - A minimal desktop portal for any Wayland compositor

positional arguments:
  {portal,list,activate,deactivate,trigger}
    portal              Run the D-Bus portal service
    list                List all active shortcut sessions and their shortcuts
    activate            Activate a specific shortcut
    deactivate          Deactivate a specific shortcut
    trigger             Trigger a shortcut (Activate followed by Deactivate)

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level (default: INFO)
```

### Add the portal
Assuming you want to use pyrtal for all compositors.

```sh
mkdir -p ~/.local/share/xdg-desktop-portal/portals
cat << 'EOF' > ~/.local/share/xdg-desktop-portal/portals/pyrtal.portal
[portal]
DBusName=org.freedesktop.impl.portal.desktop.Pyrtal
Interfaces=org.freedesktop.impl.portal.GlobalShortcuts;org.freedesktop.impl.portal.RemoteDesktop
EOF

mkdir -p ~/.config/xdg-desktop-portal
cat << 'EOF' > ~/.config/xdg-desktop-portal/portals.conf
[preferred]
default=gtk
org.freedesktop.impl.portal.GlobalShortcuts=pyrtal
org.freedesktop.impl.portal.RemoteDesktop=pyrtal
EOF
```

You may need to start/restart the xdg-desktop-portal service for these to take effect after pyrtal is running.

### Run the portal service
```sh
python3 -m pyrtal portal
```

### List registered shortcuts
```sh
python3 -m pyrtal list
```

### Trigger a shortcut
```sh
python3 -m pyrtal trigger org.keepassxc.KeePassXC autotype
```

## Note on LLMs
Development of this utility has been heavily sped up with LLMs. The code isn't slop, though, but if you have a thing against AI written code then this may not be for you.
