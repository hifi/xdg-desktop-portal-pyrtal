import logging
from dbus_fast.service import ServiceInterface, method, signal

logger = logging.getLogger(__name__)

BUS_NAME = "org.freedesktop.impl.portal.desktop.Pyrtal"
OBJECT_PATH = "/org/freedesktop/portal/desktop"


class XdpRequest(ServiceInterface):
    interface = "org.freedesktop.portal.Request"

    def __init__(self, bus, handle: str):
        super().__init__(self.interface)
        self.bus = bus
        self.path = handle

    @staticmethod
    def create(bus, handle: str) -> "XdpRequest":
        req = XdpRequest(bus, handle)
        bus.export(handle, req)
        return req

    @method()
    def Close(self):
        try:
            self.bus.unexport(self.path, self.interface)
        except Exception:
            pass

    @signal()
    def Response(self, status: 'u', results: 'a{sv}') -> 'ua{sv}':
        return [status, results]

    def respond(self, status: int = 0, results: dict | None = None):
        self.Response(status, results or {})
        self.Close()


class XdpSession(ServiceInterface):
    interface = "org.freedesktop.impl.portal.Session"
    sessions: dict = {}

    def __init__(self, bus, path: str, app_id: str):
        super().__init__(self.interface)
        self.bus = bus
        self.path = path
        self.app_id = app_id
        self.shortcuts: dict[str, str] = {}

    @method()
    def Close(self):
        logger.info("Session.Close: %s (App: %s)", self.path, self.app_id)
        if XdpSession.sessions.get(self.app_id) is self:
            del XdpSession.sessions[self.app_id]
        try:
            self.bus.unexport(self.path, self.interface)
        except Exception:
            pass
