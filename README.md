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

- wlroots (labwc, Sway etc.)
- COSMIC
- Hyprland

## Requirements

- Python 3
- `dbus-fast`
- `pywayland` (optional, required for Remote Desktop)
- `xkbcommon` (optional, required for Remote Desktop)

## Install

### Install dependencies

Install the required dependencies on Debian/Ubuntu and derivatives:

```bash
sudo apt install python3-dbus-fast python3-pywayland python3-xkbcommon
```

Install the required dependencies on Fedora and derivatives:

```bash
sudo dnf install python3-dbus-fast python3-pywayland python3-xkbcommon
```

Install the required dependencies on Arch Linux and derivatives:

```bash
sudo pacman -S python-dbus-fast python-pywayland python-xkbcommon
```

### Install pyrtal

Depending on the use case, three different installation options are outlined below.

To install a specific commit, tag or branch, append `@<commit-hash>`, `@<tag>` or `<branch-name>` to the Git URL in the pip requirement, after `.git`.
For example, replace `<tag-commit-or-branch>` with the desired tag name, commit hash or branch name:

```sh
python3 -m pip install --user 'xdg-desktop-portal-pyrtal[remote-desktop] @ git+https://github.com/hifi/xdg-desktop-portal-pyrtal.git@<tag-commit-or-branch>'
```

#### Install as user

Install pyrtal directly from Git with pip:

```sh
python3 -m pip install --user 'xdg-desktop-portal-pyrtal[remote-desktop] @ git+https://github.com/hifi/xdg-desktop-portal-pyrtal.git'
```

Some distributions mark their system Python as externally managed and block pip installs, including `--user` installs.
Use a virtual environment in that case.

#### Install in a virtual environment

If your distribution's Python installation does not allow pip installs, you can use a Python virtual environment.

The `remote-desktop` extra builds the `xkbcommon` Python package against the system `libxkbcommon` library.
On Debian-based distributions, install its development package before installing pyrtal:

```sh
sudo apt install libxkbcommon-dev
```

Then create a Python virtual environment and install pyrtal:

```bash
python3 -m venv venv
source venv/bin/activate
pip install 'xdg-desktop-portal-pyrtal[remote-desktop] @ git+https://github.com/hifi/xdg-desktop-portal-pyrtal.git'
```

#### Install pyrtal at system level

On systems where Python permits pip to manage system packages, use:

```sh
sudo python3 -m pip install 'xdg-desktop-portal-pyrtal[remote-desktop] @ git+https://github.com/hifi/xdg-desktop-portal-pyrtal.git'
```

### Activate pyrtal for a user

The pip installation provides the `pyrtal` command.

As desktop user, run:

```sh
pyrtal install
```

This creates the desktop portal configuration and, on systemd-enabled systems, its D-Bus service file.
When systemd is available, the installer reloads D-Bus and restarts `xdg-desktop-portal` if it is already running.
Otherwise, restart the portal or log out and back in for the configuration to take effect.

For global shortcuts to register you need to either logout and login again or restart the relevant programs.

## Usage

Remote desktop should work without additional confirmation for keysym input.

### List registered shortcuts

```sh
pyrtal list
```

### Trigger a shortcut

Example to trigger the shortcut for KeePassXC:

```sh
pyrtal trigger org.keepassxc.KeePassXC autotype
```

## Uninstall

### Uninstall the user configuration

To remove pyrtal's desktop configuration for the current user, run:

```sh
pyrtal uninstall
```

This does not uninstall the Python package.

### Uninstall pyrtal

To remove a user-level pip installation, run `python3 -m pip uninstall xdg-desktop-portal-pyrtal`;
for a system-level installation, run `sudo python3 -m pip uninstall xdg-desktop-portal-pyrtal`.

If installed in a virtual environment, delete the whole venv folder.

## Note on LLMs

Development of this utility has been heavily sped up with LLMs.
The code isn't slop, though, but if you have a thing against AI written code then this may not be for you.
