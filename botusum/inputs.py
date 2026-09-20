"""macOS keyboard to Azahar: 3DS map, window focus, Accessibility."""

from __future__ import annotations

import ctypes
import ctypes.util
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from botusum.azahar import AzaharSession

HOLD_S = 0.05
SOFT_RESET_HOLD_S = 0.5
PROBE_PAUSE_S = 0.8

# Default Azahar keyboard map (Qt key codes in qt-config.ini match these).
DEFAULT_BUTTON_MAP = {
    "A": "a",
    "B": "s",
    "X": "z",
    "Y": "x",
    "L": "q",
    "R": "w",
    "Start": "m",
    "Select": "n",
    "Up": "t",
    "Down": "g",
    "Left": "f",
    "Right": "h",
}

SOFT_RESET_BUTTONS = ("L", "R", "Start")

# ANSI Mac virtual keys. pynput maps some chars to the wrong vk.
_ANSI_VK = {
    "a": 0x00,
    "s": 0x01,
    "d": 0x02,
    "f": 0x03,
    "h": 0x04,
    "g": 0x05,
    "z": 0x06,
    "x": 0x07,
    "c": 0x08,
    "v": 0x09,
    "b": 0x0B,
    "q": 0x0C,
    "w": 0x0D,
    "e": 0x0E,
    "r": 0x0F,
    "y": 0x10,
    "t": 0x11,
    "1": 0x12,
    "2": 0x13,
    "3": 0x14,
    "4": 0x15,
    "6": 0x16,
    "5": 0x17,
    "9": 0x19,
    "7": 0x1A,
    "8": 0x1C,
    "0": 0x1D,
    "o": 0x1F,
    "u": 0x20,
    "[": 0x21,
    "i": 0x22,
    "p": 0x23,
    "l": 0x25,
    "j": 0x26,
    "k": 0x28,
    "n": 0x2D,
    "m": 0x2E,
}


class InputError(Exception):
    """Keyboard events could not be sent, or Accessibility is missing."""


def accessibility_trusted() -> bool:
    """True if this process may drive other apps (menus, keys, mouse)."""
    lib_name = ctypes.util.find_library("ApplicationServices")
    if not lib_name:
        return False
    lib = ctypes.cdll.LoadLibrary(lib_name)
    try:
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        lib.AXIsProcessTrusted.argtypes = []
        return bool(lib.AXIsProcessTrusted())
    except AttributeError:
        return False


def require_accessibility() -> None:
    if accessibility_trusted():
        return
    raise InputError(
        "Grant Accessibility permission so the bot can send keys to Azahar. "
        "System Settings → Privacy & Security → Accessibility → enable the "
        "app that runs this command (Terminal, iTerm, Python, or Grok)."
    )


def _keyboard():
    try:
        from pynput.keyboard import Controller, Key
    except ImportError as exc:
        raise InputError(
            "pynput is required to send keyboard events. Install it with: "
            "python3 -m venv .venv && .venv/bin/pip install pynput"
        ) from exc
    return Controller(), Key


def _mouse():
    try:
        from pynput.mouse import Button, Controller
    except ImportError as exc:
        raise InputError(
            "pynput is required to send mouse events. Install it with: "
            "python3 -m venv .venv && .venv/bin/pip install pynput"
        ) from exc
    return Controller(), Button


def _pynput_key(name: str):
    _controller, Key = _keyboard()
    from pynput.keyboard import KeyCode

    special = {
        "enter": Key.enter,
        "return": Key.enter,
        "backspace": Key.backspace,
        "shift": Key.shift,
        "ctrl": Key.ctrl,
        "up": Key.up,
        "down": Key.down,
        "left": Key.left,
        "right": Key.right,
        "esc": Key.esc,
        "space": Key.space,
        "tab": Key.tab,
    }
    if name.lower() in special:
        return special[name.lower()]
    lookup = name.lower() if name.isalpha() else name
    if lookup in _ANSI_VK:
        return KeyCode.from_vk(_ANSI_VK[lookup])
    if len(name) == 1:
        return name
    raise InputError(f"Cannot send key {name!r}")


def press_key(name: str) -> None:
    require_accessibility()
    controller, _Key = _keyboard()
    controller.press(_pynput_key(name))


def release_key(name: str) -> None:
    require_accessibility()
    controller, _Key = _keyboard()
    controller.release(_pynput_key(name))


def tap_key(name: str, hold_s: float = HOLD_S) -> None:
    press_key(name)
    time.sleep(hold_s)
    release_key(name)


def left_click_at(x: int, y: int) -> None:
    require_accessibility()
    mouse, Button = _mouse()
    mouse.position = (int(x), int(y))
    time.sleep(0.05)
    mouse.click(Button.left, 1)


class PadDriver:
    """Focus Azahar, then tap or hold mapped 3DS buttons."""

    def __init__(
        self,
        session: AzaharSession,
        mapping: dict[str, str] | None = None,
    ) -> None:
        self.session = session
        self.button_map = dict(DEFAULT_BUTTON_MAP if mapping is None else mapping)

    def tap(self, button: str) -> None:
        self.session.tap_key(self._key(button))

    def hold(self, *buttons: str, hold_s: float = SOFT_RESET_HOLD_S) -> None:
        if not buttons:
            raise InputError("hold needs at least one button")
        self.session.hold_keys([self._key(b) for b in buttons], hold_s=hold_s)

    def soft_reset(self, hold_s: float = SOFT_RESET_HOLD_S) -> None:
        """3DS L+R+Start (default keys Q+W+M)."""
        self.hold(*SOFT_RESET_BUTTONS, hold_s=hold_s)

    def _key(self, button: str) -> str:
        try:
            return self.button_map[button]
        except KeyError as exc:
            raise InputError(f"3DS pad has no button {button!r}") from exc
