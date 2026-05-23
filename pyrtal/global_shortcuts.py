import logging
from dbus_fast.service import ServiceInterface, method, dbus_property, signal
from dbus_fast import Variant
from dbus_fast.constants import PropertyAccess

from .shared import XdpRequest, XdpSession

logger = logging.getLogger(__name__)

class GlobalShortcuts(ServiceInterface):
    interface = "org.freedesktop.impl.portal.GlobalShortcuts"

    def __init__(self, bus):
        super().__init__(self.interface)
        self.bus = bus

    @dbus_property(access=PropertyAccess.READ)
    def version(self) -> 'u':
        return 2

    @signal()
    def Activated(self, session: 'o', shortcut_id: 's', timestamp: 't', options: 'a{sv}') -> 'osta{sv}':
        return [session, shortcut_id, timestamp, options]

    @signal()
    def Deactivated(self, session: 'o', shortcut_id: 's', timestamp: 't', options: 'a{sv}') -> 'osta{sv}':
        return [session, shortcut_id, timestamp, options]

    @method()
    def CreateSession(self, handle: 'o', session_handle: 'o', app_id: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.info("CreateSession: %s", app_id)
        if app_id in XdpSession.sessions:
            logger.info("Overriding existing session for %s", app_id)
            XdpSession.sessions[app_id].Close()
        session = XdpSession(self.bus, session_handle, app_id)
        XdpSession.sessions[app_id] = session
        self.bus.export(session_handle, session)
        XdpRequest.create(self.bus, handle).respond()
        return [0, {}]

    @method()
    def BindShortcuts(self, handle: 'o', session_handle: 'o', shortcuts: 'a(sa{sv})', parent_window: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.info("BindShortcuts for session %s: %s", session_handle, shortcuts)
        session = next((s for s in XdpSession.sessions.values() if s.path == session_handle), None)
        if session:
            for s_id, s_options in shortcuts:
                v_desc = s_options.get('description')
                session.shortcuts[s_id] = str(v_desc.value) if v_desc else ""
            logger.info("Session shortcuts: %s", session.shortcuts)
        results = {}
        if session:
            results['shortcuts'] = Variant('a(sa{sv})', [
                [sid, {'description': Variant('s', desc)}]
                for sid, desc in session.shortcuts.items()
            ])
        XdpRequest.create(self.bus, handle).respond(results=results)
        return [0, {}]

    @method()
    def ListShortcuts(self, handle: 'o', session_handle: 'o') -> 'ua{sv}':
        logger.info("ListShortcuts for session %s", session_handle)
        session = next((s for s in XdpSession.sessions.values() if s.path == session_handle), None)
        results = {}
        if session:
            results['shortcuts'] = Variant('a(sa{sv})', [
                [sid, {'description': Variant('s', desc)}]
                for sid, desc in session.shortcuts.items()
            ])
        XdpRequest.create(self.bus, handle).respond(results=results)
        return [0, {}]

    @method()
    def ConfigureShortcuts(self, handle: 'o', session_handle: 'o', parent_window: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.info("ConfigureShortcuts")
        XdpRequest.create(self.bus, handle).respond()
        return [0, {}]
