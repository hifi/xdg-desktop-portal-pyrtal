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

## Install

Install the required dependencies on Debian/Ubuntu:

```bash
sudo apt install python3-dbus-fast python3-pywayland python3-xkbcommon
```

Install the required dependencies on Fedora:

```bash
sudo dnf install python3-dbus-fast python3-pywayland python3-xkbcommon
```

To install pyrtal for the current desktop, the following commands will create all necessary service files and overrides on systemd enabled systems:

```sh
git clone https://github.com/hifi/xdg-desktop-portal-pyrtal
cd xdg-desktop-portal-pyrtal
python3 -m pyrtal install
```

You should be able to run `pyrtal` directly given `~/.local/bin` is in your _$PATH_ and it should immediately be activated for the current session.
For global shortcuts to register you need to either logout and login again or restart the relevant programs.

## Usage

Remote desktop should work without additional confirmation for keysym input.

### List registered shortcuts
```sh
pyrtal list
```

### Trigger a shortcut
```sh
pyrtal trigger org.keepassxc.KeePassXC autotype
```

## Uninstall

To completely uninstall pyrtal from the current user, execute the following command and it will do its best to cleanup everything:

```sh
pyrtal uninstall
```

## Note on LLMs
Development of this utility has been heavily sped up with LLMs. The code isn't slop, though, but if you have a thing against AI written code then this may not be for you.
