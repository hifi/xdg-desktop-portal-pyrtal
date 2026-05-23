import time
import logging
from dbus_fast.service import ServiceInterface, method

from .shared import XdpSession

logger = logging.getLogger(__name__)

class Pyrtal(ServiceInterface):
    interface = "org.freedesktop.impl.portal.desktop.Pyrtal"

    def __init__(self, global_shortcuts):
        super().__init__(self.interface)
        self.global_shortcuts = global_shortcuts

    @method()
    def ActivateShortcut(self, app_id: 's', shortcut_id: 's'):
        session = XdpSession.sessions.get(app_id)
        if not session:
            raise ValueError(f"No active session for app_id: {app_id}")
        self.global_shortcuts.Activated(session.path, shortcut_id, int(time.time() * 1000), {})

    @method()
    def DeactivateShortcut(self, app_id: 's', shortcut_id: 's'):
        session = XdpSession.sessions.get(app_id)
        if not session:
            raise ValueError(f"No active session for app_id: {app_id}")
        self.global_shortcuts.Deactivated(session.path, shortcut_id, int(time.time() * 1000), {})

    @method()
    def TriggerShortcut(self, app_id: 's', shortcut_id: 's'):
        self.ActivateShortcut(app_id, shortcut_id)
        self.DeactivateShortcut(app_id, shortcut_id)

    @method()
    def ListShortcuts(self) -> 'a{sa{ss}}':
        return {app_id: sess.shortcuts for app_id, sess in XdpSession.sessions.items()}
