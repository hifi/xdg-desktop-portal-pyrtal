import logging
from dbus_fast.service import ServiceInterface, method, dbus_property, signal
from dbus_fast import Variant
from dbus_fast.constants import PropertyAccess

from .session import XdpSession

logger = logging.getLogger(__name__)

class GlobalShortcuts(ServiceInterface):
    interface = "org.freedesktop.impl.portal.GlobalShortcuts"

    def __init__(self, bus):
        super().__init__(self.interface)
        self.bus = bus
        logger.info("Portal created")

    @dbus_property(access=PropertyAccess.READ)
    def version(self) -> 'u':
        return 2

    @signal()
    def Activated(self, session: 'o', shortcut_id: 's', timestamp: 't', options: 'a{sv}') -> 'osta{sv}':
        logger.debug("Activated(session=%s, shortcut_id=%s, timestamp=%s, options=%s)", session, shortcut_id, timestamp, options)
        return [session, shortcut_id, timestamp, options]

    @signal()
    def Deactivated(self, session: 'o', shortcut_id: 's', timestamp: 't', options: 'a{sv}') -> 'osta{sv}':
        logger.debug("Deactivated(session=%s, shortcut_id=%s, timestamp=%s, options=%s)", session, shortcut_id, timestamp, options)
        return [session, shortcut_id, timestamp, options]

    @method()
    def CreateSession(self, handle: 'o', session_handle: 'o', app_id: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.debug("CreateSession(handle=%s, session_handle=%s, app_id=%s, options=%s)", handle, session_handle, app_id, options)
        if app_id in XdpSession.sessions:
            logger.info("Overriding existing session for %s", app_id)
            XdpSession.sessions[app_id].Close()
        session = XdpSession(self.bus, session_handle, app_id)
        XdpSession.sessions[app_id] = session
        self.bus.export(session_handle, session)
        return [0, {}]

    @method()
    def BindShortcuts(self, handle: 'o', session_handle: 'o', shortcuts: 'a(sa{sv})', parent_window: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.debug("BindShortcuts(handle=%s, session_handle=%s, shortcuts=%s, parent_window=%s, options=%s)", handle, session_handle, shortcuts, parent_window, options)
        results = {}
        session = next((s for s in XdpSession.sessions.values() if s.path == session_handle), None)
        if session:
            for s_id, s_options in shortcuts:
                v_desc = s_options.get('description')
                session.shortcuts[s_id] = str(v_desc.value) if v_desc else ""

        if session:
            results['shortcuts'] = Variant('a(sa{sv})', [
                [sid, {
                    'description': Variant('s', desc),
                    'trigger_description': Variant('s', f"pyrtal trigger {session.app_id} {sid}"),
                }]
                for sid, desc in session.shortcuts.items()
            ])

        logger.debug("BindShortcuts results: %s", results)
        return [0, results]

    @method()
    def ListShortcuts(self, handle: 'o', session_handle: 'o') -> 'ua{sv}':
        logger.debug("ListShortcuts(handle=%s, session_handle=%s)", handle, session_handle)
        session = next((s for s in XdpSession.sessions.values() if s.path == session_handle), None)
        results = {}
        if session:
            results['shortcuts'] = Variant('a(sa{sv})', [
                [sid, {
                    'description': Variant('s', desc),
                    'trigger_description': Variant('s', f"pyrtal trigger {session.app_id} {sid}"),
                }]
                for sid, desc in session.shortcuts.items()
            ])
        logger.debug("ListShortcuts results: %s", results)
        return [0, results]

    @method()
    def ConfigureShortcuts(self, session_handle: 'o', parent_window: 's', options: 'a{sv}'):
        logger.debug("ConfigureShortcuts(session_handle=%s, parent_window=%s, options=%s)", session_handle, parent_window, options)
