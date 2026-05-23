import logging
from dbus_fast import Variant
from dbus_fast.service import ServiceInterface, method, dbus_property
from dbus_fast.constants import PropertyAccess

from .shared import XdpRequest, XdpSession
from .virtual_keyboard import VirtualKeyboard

logger = logging.getLogger(__name__)

DEVICE_KEYBOARD = 1

class RemoteDesktop(ServiceInterface):
    interface = "org.freedesktop.impl.portal.RemoteDesktop"

    def __init__(self, bus, layout: str = "us"):
        super().__init__(self.interface)
        self.bus = bus
        self._layout = layout
        self._vkbd = VirtualKeyboard()
        self._devices = DEVICE_KEYBOARD

    @dbus_property(access=PropertyAccess.READ)
    def version(self) -> 'u':
        return 1

    @dbus_property(access=PropertyAccess.READ)
    def AvailableDeviceTypes(self) -> 'u':
        return DEVICE_KEYBOARD

    @method()
    def CreateSession(self, handle: 'o', session_handle: 'o', app_id: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.info("RemoteDesktop.CreateSession: %s", app_id)
        session = XdpSession(self.bus, session_handle, app_id)
        self.bus.export(session_handle, session)
        XdpRequest.create(self.bus, handle).respond()
        return [0, {}]

    @method()
    def SelectDevices(self, handle: 'o', session_handle: 'o', app_id: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.info("RemoteDesktop.SelectDevices")
        types_variant = options.get('types')
        requested = types_variant.value if types_variant else DEVICE_KEYBOARD
        self._devices = requested & DEVICE_KEYBOARD
        return [0, {'devices': Variant('u', self._devices)}]

    @method()
    def Start(self, handle: 'o', session_handle: 'o', app_id: 's', parent_window: 's', options: 'a{sv}') -> 'ua{sv}':
        logger.info("RemoteDesktop.Start")
        if not self._vkbd.connect(self._layout):
            logger.warning("Virtual keyboard unavailable")
        return [0, {'devices': Variant('u', self._devices)}]

    @method()
    def NotifyPointerMotion(self, session_handle: 'o', options: 'a{sv}', dx: 'd', dy: 'd'):
        pass

    @method()
    def NotifyPointerMotionAbsolute(self, session_handle: 'o', options: 'a{sv}', stream: 'u', x: 'd', y: 'd'):
        pass

    @method()
    def NotifyPointerButton(self, session_handle: 'o', options: 'a{sv}', button: 'i', state: 'u'):
        pass

    @method()
    def NotifyPointerAxis(self, session_handle: 'o', options: 'a{sv}', dx: 'd', dy: 'd'):
        pass

    @method()
    def NotifyPointerAxisDiscrete(self, session_handle: 'o', options: 'a{sv}', axis: 'u', steps: 'i'):
        pass

    @method()
    def NotifyKeyboardKeycode(self, session_handle: 'o', options: 'a{sv}', keycode: 'i', state: 'u'):
        pass

    @method()
    def NotifyKeyboardKeysym(self, session_handle: 'o', options: 'a{sv}', keysym: 'i', state: 'u'):
        self._vkbd.send_keysym(keysym & 0xFFFFFFFF, state)

    @method()
    def NotifyTouchDown(self, session_handle: 'o', options: 'a{sv}', stream: 'u', slot: 'u', x: 'd', y: 'd'):
        pass

    @method()
    def NotifyTouchMotion(self, session_handle: 'o', options: 'a{sv}', stream: 'u', slot: 'u', x: 'd', y: 'd'):
        pass

    @method()
    def NotifyTouchUp(self, session_handle: 'o', options: 'a{sv}', slot: 'u'):
        pass
