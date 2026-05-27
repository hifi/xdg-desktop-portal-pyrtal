import asyncio
import argparse
import configparser
import glob
import os
import shutil
import stat
import subprocess
import sys
import logging
from dbus_fast.message import Message
from dbus_fast.aio import MessageBus
from dbus_fast.constants import BusType, MessageType

from .global_shortcuts import GlobalShortcuts
try:
    from .remote_desktop import RemoteDesktop
    _remote_desktop_error = None
except ImportError as e:
    RemoteDesktop = None
    _remote_desktop_error = e
from .pyrtal import Pyrtal

BUS_NAME = "org.freedesktop.impl.portal.desktop.Pyrtal"
OBJECT_PATH = "/org/freedesktop/portal/desktop"

XDG_DATA_HOME = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
LOCAL_BIN = os.path.expanduser('~/.local/bin')

logger = logging.getLogger("pyrtal")


def cmd_install():
    module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. pyrtal.portal
    portals_dir = os.path.join(XDG_DATA_HOME, 'xdg-desktop-portal', 'portals')
    os.makedirs(portals_dir, exist_ok=True)
    portal_file = os.path.join(portals_dir, 'pyrtal.portal')
    portal_config = configparser.ConfigParser()
    portal_config.optionxform = str
    portal_config.read(portal_file)
    if 'portal' not in portal_config:
        portal_config['portal'] = {}
    portal_config['portal']['DBusName'] = 'org.freedesktop.impl.portal.desktop.Pyrtal'
    portal_config['portal']['Interfaces'] = 'org.freedesktop.impl.portal.GlobalShortcuts;org.freedesktop.impl.portal.RemoteDesktop'
    with open(portal_file, 'w') as f:
        portal_config.write(f)
    print(f'Wrote {portal_file}')

    # 2. portals.conf (desktop-specific or generic)
    portals_conf_dir = os.path.join(XDG_CONFIG_HOME, 'xdg-desktop-portal')
    os.makedirs(portals_conf_dir, exist_ok=True)
    desktops = [d for d in os.environ.get('XDG_CURRENT_DESKTOP', '').split(':') if d]
    write_conf = True
    if desktops:
        conf_filename = f'{desktops[0].lower()}-portals.conf'
    else:
        answer = input('No XDG_CURRENT_DESKTOP detected. Create generic portals.conf? [y/N] ')
        if answer.strip().lower() == 'y':
            conf_filename = 'portals.conf'
        else:
            write_conf = False
            print('Skipping portals.conf')
    if write_conf:
        local_conf_file = os.path.join(portals_conf_dir, conf_filename)
        system_conf_file = os.path.join('/usr/share/xdg-desktop-portal', conf_filename)
        conf = configparser.ConfigParser()
        conf.optionxform = str
        conf.read([system_conf_file, local_conf_file])
        if 'preferred' not in conf:
            conf['preferred'] = {}
            conf['preferred']['default'] = 'gtk'
        conf['preferred']['org.freedesktop.impl.portal.GlobalShortcuts'] = 'pyrtal'
        conf['preferred']['org.freedesktop.impl.portal.RemoteDesktop'] = 'pyrtal'
        with open(local_conf_file, 'w') as f:
            conf.write(f)
        print(f'Wrote {local_conf_file}')

    # 3. pyrtal binary
    os.makedirs(LOCAL_BIN, exist_ok=True)
    pyrtal_bin = os.path.join(LOCAL_BIN, 'pyrtal')
    with open(pyrtal_bin, 'w') as f:
        f.write('#!/bin/sh\n')
        f.write(f'PYTHONPATH={module_dir} exec python3 -m pyrtal "$@"\n')
    os.chmod(pyrtal_bin, os.stat(pyrtal_bin).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f'Wrote {pyrtal_bin}')

    # 4. D-Bus session service file (systemd only)
    if shutil.which('systemctl') is None:
        print('systemctl not found, skipping D-Bus service file')
        return
    dbus_services_dir = os.path.join(XDG_DATA_HOME, 'dbus-1', 'services')
    os.makedirs(dbus_services_dir, exist_ok=True)
    service_file = os.path.join(dbus_services_dir, 'org.freedesktop.impl.portal.desktop.Pyrtal.service')
    service_config = configparser.ConfigParser()
    service_config.optionxform = str
    service_config['D-BUS Service'] = {
        'Name': 'org.freedesktop.impl.portal.desktop.Pyrtal',
        'Exec': f'{pyrtal_bin} portal',
    }
    with open(service_file, 'w') as f:
        service_config.write(f)
    print(f'Wrote {service_file}')
    subprocess.run(['systemctl', '--user', 'daemon-reload'])
    subprocess.run(['systemctl', '--user', 'reload', 'dbus'])
    print("Systemd reloaded")
    result = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'xdg-desktop-portal'])
    if result.returncode == 0:
        subprocess.run(['systemctl', '--user', 'restart', 'xdg-desktop-portal'])
        print('Restarted xdg-desktop-portal.service')


def cmd_uninstall():
    # Stop pyrtal and xdg-desktop-portal via systemd if available
    reload_systemd = False
    if shutil.which('systemctl') is not None:
        subprocess.run(['systemctl', '--user', 'stop', 'xdg-desktop-portal'], stderr=subprocess.DEVNULL)

        service_file = os.path.join(XDG_DATA_HOME, 'dbus-1', 'services', 'org.freedesktop.impl.portal.desktop.Pyrtal.service')
        if os.path.exists(service_file):
            os.remove(service_file)
            print(f'Removed {service_file}')
            reload_systemd = True

    # Remove pyrtal.portal
    portal_file = os.path.join(XDG_DATA_HOME, 'xdg-desktop-portal', 'portals', 'pyrtal.portal')
    if os.path.exists(portal_file):
        os.remove(portal_file)
        print(f'Removed {portal_file}')

    # Remove pyrtal binary
    pyrtal_bin = os.path.join(LOCAL_BIN, 'pyrtal')
    if os.path.exists(pyrtal_bin):
        os.remove(pyrtal_bin)
        print(f'Removed {pyrtal_bin}')

    # Clean all *portals.conf files — remove only keys pointing to pyrtal
    portals_conf_dir = os.path.join(XDG_CONFIG_HOME, 'xdg-desktop-portal')
    for local_conf_file in glob.glob(os.path.join(portals_conf_dir, '*portals.conf')):
        conf = configparser.ConfigParser()
        conf.optionxform = str
        conf.read(local_conf_file)
        if 'preferred' not in conf:
            continue
        for key in list(conf['preferred']):
            if conf['preferred'][key] == 'pyrtal':
                conf.remove_option('preferred', key)
        with open(local_conf_file, 'w') as f:
            conf.write(f)
        print(f'Updated {local_conf_file}')

    if reload_systemd:
        subprocess.run(['systemctl', '--user', 'daemon-reload'])
        print("Systemd reloaded")


async def main():
    parser = argparse.ArgumentParser(description="pyrtal - A minimal desktop portal for any Wayland compositor")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
    subparsers = parser.add_subparsers(dest="command")

    portal = subparsers.add_parser("portal", help="Run the D-Bus portal service")
    portal.add_argument("--layout", default="eu", metavar="XKB_LAYOUT", help="XKB keyboard layout for virtual keyboard (default: us)")
    subparsers.add_parser("list", help="List all active shortcut sessions and their shortcuts")

    act = subparsers.add_parser("activate", help="Activate a specific shortcut")
    act.add_argument("app_id", help="Application ID (e.g., org.gnome.TextEditor)")
    act.add_argument("shortcut_id", help="Shortcut ID to activate")

    deact = subparsers.add_parser("deactivate", help="Deactivate a specific shortcut")
    deact.add_argument("app_id", help="Application ID")
    deact.add_argument("shortcut_id", help="Shortcut ID to deactivate")

    trig = subparsers.add_parser("trigger", help="Trigger a shortcut (Activate followed by Deactivate)")
    trig.add_argument("app_id", help="Application ID")
    trig.add_argument("shortcut_id", help="Shortcut ID to trigger")

    subparsers.add_parser("install", help="Install pyrtal for the current desktop session")
    subparsers.add_parser("uninstall", help="Uninstall pyrtal completely")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")

    if args.command == "install":
        cmd_install()
        return
    if args.command == "uninstall":
        cmd_uninstall()
        return

    bus = await MessageBus(bus_type=BusType.SESSION).connect()

    if args.command == "portal":
        logger.info("Starting portals")
        await bus.request_name(BUS_NAME)
        gs = GlobalShortcuts(bus)
        bus.export(OBJECT_PATH, gs)
        if RemoteDesktop is not None:
            bus.export(OBJECT_PATH, RemoteDesktop(bus, args.layout))
        else:
            logger.warning("RemoteDesktop portal disabled (install pywayland and xkbcommon to enable): %s", _remote_desktop_error)
        bus.export(OBJECT_PATH, Pyrtal(gs))
        try:
            await bus.wait_for_disconnect()
        except EOFError:
            pass
    elif args.command == "list":
        reply = await bus.call(Message(
            destination=BUS_NAME, path=OBJECT_PATH,
            interface=Pyrtal.interface, member="ListShortcuts",
        ))
        if reply.message_type != MessageType.ERROR:
            rows = [
                (app_id, sid, desc)
                for app_id, shortcuts in reply.body[0].items()
                for sid, desc in shortcuts.items()
            ]
            if rows:
                w_app = max(len(r[0]) for r in rows + [("App ID", "", "")])
                w_sid = max(len(r[1]) for r in rows + [("", "Shortcut ID", "")])
                print(f"{'App':<{w_app}}  {'Shortcut':<{w_sid}}  Description")
                print(f"{'-' * w_app}  {'-' * w_sid}  -----------")
                for app_id, sid, desc in rows:
                    print(f"{app_id:<{w_app}}  {sid:<{w_sid}}  {desc}")
    elif args.command in ("activate", "deactivate", "trigger"):
        member = {"activate": "ActivateShortcut", "deactivate": "DeactivateShortcut", "trigger": "TriggerShortcut"}[args.command]
        reply = await bus.call(Message(
            destination=BUS_NAME, path=OBJECT_PATH, interface=Pyrtal.interface,
            member=member, signature="ss",
            body=[args.app_id, args.shortcut_id],
        ))
        if reply.message_type == MessageType.ERROR:
            logger.error("Error calling %s: %s", args.command, reply.body[0])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
