import os
import time
import logging

from pywayland.client import Display
from pywayland.protocol.wayland import WlSeat
from xkbcommon import xkb

from .protocols.virtual_keyboard_unstable_v1 import ZwpVirtualKeyboardManagerV1

logger = logging.getLogger(__name__)

WL_KEYBOARD_FORMAT_XKB_V1 = 1
WL_KEYBOARD_KEY_STATE_RELEASED = 0
WL_KEYBOARD_KEY_STATE_PRESSED = 1


class VirtualKeyboard:
    def __init__(self):
        self._display = None
        self._keyboard = None
        self._keysym_map: dict[int, tuple[int, int]] = {}

    def connect(self, layout: str = "us") -> bool:
        try:
            self._display = Display()
            self._display.connect()
        except Exception:
            logger.exception("Failed to connect to Wayland display")
            return False

        manager = None
        seat = None
        registry = self._display.get_registry()

        def handle_global(registry_proxy, name, interface, version):
            nonlocal manager, seat
            if interface == ZwpVirtualKeyboardManagerV1.name:
                manager = registry_proxy.bind(name, ZwpVirtualKeyboardManagerV1, min(version, 1))
            elif interface == WlSeat.name:
                if seat is None:
                    seat = registry_proxy.bind(name, WlSeat, min(version, 7))

        registry.dispatcher["global"] = handle_global

        self._display.roundtrip()

        if manager is None or seat is None:
            logger.error("Missing Wayland globals: manager=%s seat=%s", manager, seat)
            return False

        self._keyboard = manager.create_virtual_keyboard(seat)
        self._display.roundtrip()

        ctx = xkb.Context()
        keymap = ctx.keymap_new_from_names(layout=layout)

        keymap_bytes = keymap.get_as_bytes()
        fd = os.memfd_create("xkb-keymap")
        os.write(fd, keymap_bytes)
        self._keyboard.keymap(WL_KEYBOARD_FORMAT_XKB_V1, fd, len(keymap_bytes))
        self._display.flush()
        os.close(fd)

        shift_mask = 1 << keymap.mod_get_index("Shift")

        altgr_mask = 0
        for name in ("Mod5", "ISO_Level3_Shift", "LevelThree"):
            try:
                altgr_mask = 1 << keymap.mod_get_index(name)
                break
            except Exception:
                pass

        level_mods = {0: 0, 1: shift_mask, 2: altgr_mask, 3: shift_mask | altgr_mask}

        for keycode in keymap:
            num_levels = keymap.num_levels_for_key(keycode, 0)
            for level in range(min(num_levels, 4)):
                mod_mask = level_mods.get(level, 0)
                for sym in keymap.key_get_syms_by_level(keycode, 0, level):
                    if sym and sym not in self._keysym_map:
                        self._keysym_map[sym] = (keycode, mod_mask)

        logger.info("VirtualKeyboard ready, layout=%s, %d keysym mappings", layout, len(self._keysym_map))
        return True

    def send_keysym(self, keysym: int, state: int):
        if self._keyboard is None:
            return

        entry = self._keysym_map.get(keysym)
        if entry is None:
            logger.warning("No keycode mapping for keysym 0x%x", keysym)
            return

        keycode, mod_mask = entry
        evdev_keycode = keycode - 8
        timestamp = int(time.monotonic() * 1000) & 0xFFFFFFFF

        if state == WL_KEYBOARD_KEY_STATE_PRESSED:
            if mod_mask:
                self._keyboard.modifiers(mod_mask, 0, 0, 0)
            self._keyboard.key(timestamp, evdev_keycode, WL_KEYBOARD_KEY_STATE_PRESSED)
        else:
            self._keyboard.key(timestamp, evdev_keycode, WL_KEYBOARD_KEY_STATE_RELEASED)
            if mod_mask:
                self._keyboard.modifiers(0, 0, 0, 0)

        self._display.flush()
