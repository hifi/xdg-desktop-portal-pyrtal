import logging
from dbus_fast.service import ServiceInterface, method

logger = logging.getLogger(__name__)


class XdpSession(ServiceInterface):
    interface = "org.freedesktop.impl.portal.Session"
    sessions: dict = {}

    def __init__(self, bus, path: str, app_id: str):
        super().__init__(self.interface)
        self.bus = bus
        self.path = path
        self.app_id = app_id
        self.shortcuts: dict[str, str] = {}
        logger.debug("__init__(path=%s app_id=%s)", self.path, self.app_id)

    @method()
    def Close(self):
        logger.debug("Close(): path=%s, app_id=%s", self.path, self.app_id)
        if XdpSession.sessions.get(self.app_id) is self:
            del XdpSession.sessions[self.app_id]
        try:
            self.bus.unexport(self.path, self.interface)
        except Exception:
            pass
