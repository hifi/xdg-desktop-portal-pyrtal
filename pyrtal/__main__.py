import asyncio
import argparse
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

logger = logging.getLogger("pyrtal")


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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")

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
