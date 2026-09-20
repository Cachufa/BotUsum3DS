"""Launch / reuse Azahar with the ROM. Ctrl+C must not kill the emulator."""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

from botusum.paths import HuntPaths
from botusum.rpc import RpcClient, RpcError

PROCESS_NAMES = ("azahar", "Azahar")
APPLESCRIPT_PROCESS = "Azahar"
PROCESS_TIMEOUT_S = 20.0
WINDOW_TIMEOUT_S = 30.0


class AzaharError(Exception):
    """Azahar is missing, did not start, or RPC is disabled."""


def azahar_pids() -> list[int]:
    pids: set[int] = set()
    for name in PROCESS_NAMES:
        result = subprocess.run(
            ["pgrep", "-x", name],
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 1):
            raise AzaharError(f"pgrep failed: {result.stderr.strip()}")
        for line in result.stdout.split():
            if line.strip():
                pids.add(int(line))
    return sorted(pids)


def set_ini_key(path: Path, section: str, key: str, value: str) -> None:
    """Change one key in an Azahar qt-config.ini without rewriting unrelated keys."""
    if not path.is_file():
        raise AzaharError(f"Azahar config is missing: {path}")
    text = path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    in_section = False
    found_section = False
    replaced = False
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_section and not replaced:
                out.append(f"{key}={value}")
                replaced = True
            in_section = stripped == f"[{section}]"
            found_section = found_section or in_section
        elif in_section and stripped.split("=", 1)[0].strip() == key:
            out.append(f"{key}={value}")
            replaced = True
            continue
        out.append(line)
    if in_section and not replaced:
        out.append(f"{key}={value}")
        replaced = True
    if not found_section:
        if out and out[-1] != "":
            out.append("")
        out.append(f"[{section}]")
        out.append(f"{key}={value}")
        replaced = True
    if not replaced:
        raise AzaharError(f"Could not set [{section}] {key} in {path}")
    path.write_text(newline.join(out) + newline, encoding="utf-8")


def _applescript(source: str) -> str:
    result = subprocess.run(
        ["osascript"],
        input=source,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "osascript failed").strip()
        if "no se permite" in err.lower() or "not allowed" in err.lower():
            raise AzaharError(
                "Grant Accessibility permission to Terminal (or Python) "
                "so the bot can see the Azahar window."
            )
        raise AzaharError(err)
    return result.stdout.strip()


class AzaharSession:
    def __init__(self, paths: HuntPaths) -> None:
        self.paths = paths

    def is_running(self) -> bool:
        return bool(azahar_pids())

    def enable_rpc_in_config(self) -> None:
        """Persist Enable RPC Server. Azahar ignores the value while \\default=true."""
        config = self.paths.qt_config
        set_ini_key(config, "Debugging", "enable_rpc_server", "true")
        set_ini_key(config, "Debugging", r"enable_rpc_server\default", "false")

    def launch(self) -> bool:
        """Start Azahar with the ROM, or activate an already-running instance.

        Uses `open -a Azahar.app --args <rom>` so the inner Mach-O is not
        launched directly. Returns True if Azahar was already running.
        """
        reused = self.is_running()
        if not reused:
            self.enable_rpc_in_config()
        cmd = [
            "open",
            "-a",
            str(self.paths.azahar_app),
            "--args",
            str(self.paths.ultra_moon_rom),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "open failed").strip()
            raise AzaharError(f"Could not launch Azahar: {err}")
        return reused

    def wait_for_process(self, timeout_s: float = PROCESS_TIMEOUT_S) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self.is_running():
                return
            time.sleep(0.2)
        raise AzaharError("Timed out waiting for the Azahar process")

    def _ax_process_name(self) -> str | None:
        if not self.is_running():
            return None
        for process_name in (APPLESCRIPT_PROCESS, "azahar"):
            raw = _applescript(
                f"""
                tell application "System Events"
                  if exists process "{process_name}" then return "{process_name}"
                end tell
                return ""
                """
            )
            if raw:
                return raw
        return None

    def window_titles(self) -> list[str]:
        return [frame[0] for frame in self.window_frames()]

    def window_frames(self) -> list[tuple[str, int, int, int, int]]:
        """(title, x, y, width, height) for named Azahar windows."""
        process_name = self._ax_process_name()
        if process_name is None:
            return []
        raw = _applescript(
            f"""
            tell application "System Events"
              if not (exists process "{process_name}") then return ""
              tell process "{process_name}"
                set out to ""
                repeat with w in windows
                  try
                    set nm to name of w as text
                    if nm is not "" then
                      set pos to position of w
                      set sz to size of w
                      set out to out & nm & tab & (item 1 of pos as text)
                      set out to out & tab & (item 2 of pos as text)
                      set out to out & tab & (item 1 of sz as text)
                      set out to out & tab & (item 2 of sz as text) & linefeed
                    end if
                  end try
                end repeat
                return out
              end tell
            end tell
            """
        )
        frames: list[tuple[str, int, int, int, int]] = []
        for line in raw.splitlines():
            parts = line.split("\t")
            if len(parts) != 5:
                continue
            title, xs, ys, ws, hs = parts
            try:
                frames.append(
                    (
                        title,
                        int(float(xs)),
                        int(float(ys)),
                        int(float(ws)),
                        int(float(hs)),
                    )
                )
            except ValueError:
                continue
        return frames

    def _game_frame(self) -> tuple[str, int, int, int, int]:
        frames = self.window_frames()
        if not frames:
            raise AzaharError("Azahar window not found")
        return max(frames, key=lambda frame: frame[3] * frame[4])

    def focus_window(self) -> str:
        title, x, y, w, h = self._game_frame()
        self._raise_and_click(title, x, y, w, h)
        return title

    def tap_key(self, key: str, hold_s: float | None = None) -> None:
        """Focus Azahar and tap one key while osascript keeps it frontmost."""
        from botusum.inputs import HOLD_S, left_click_at, tap_key as hid_tap

        title, x, y, w, h = self._game_frame()
        process_name = self._ax_process_name()
        if process_name is None:
            raise AzaharError("Azahar window not found")
        escaped = title.replace("\\", "\\\\").replace('"', '\\"')
        cx = x + max(w // 2, 8)
        cy = y + max(28 + (h - 28) // 2, 40)
        hold = HOLD_S if hold_s is None else max(float(hold_s), 0.0)
        as_delay = 1.6
        hid_error: list[BaseException] = []

        def send_hid() -> None:
            try:
                time.sleep(0.5)
                left_click_at(cx, cy)
                time.sleep(0.22)
                hid_tap(key, hold_s=hold)
            except BaseException as exc:
                hid_error.append(exc)

        worker = threading.Thread(target=send_hid, daemon=True)
        worker.start()
        _applescript(
            f"""
            tell application "System Events"
              tell process "{process_name}"
                set frontmost to true
                delay 0.1
                repeat with w in windows
                  try
                    if (name of w as text) is "{escaped}" then
                      perform action "AXRaise" of w
                      set index of w to 1
                      exit repeat
                    end if
                  end try
                end repeat
                delay 0.2
              end tell
              delay {as_delay:.3f}
            end tell
            """
        )
        worker.join(timeout=as_delay + 2.0)
        self._raise_hid_error(hid_error)

    def mash_key(
        self,
        key: str,
        duration_s: float,
        *,
        hold_s: float | None = None,
        gap_s: float = 0.05,
    ) -> int:
        """Focus once, then tap `key` repeatedly for `duration_s` seconds.

        Per-tap `tap_key` re-runs the focus applescript (~1.6s) and is too
        slow for dialogue mash. Returns how many taps were sent.
        """
        from botusum.inputs import HOLD_S, left_click_at, tap_key as hid_tap

        duration = max(float(duration_s), 0.0)
        if duration <= 0:
            return 0
        title, x, y, w, h = self._game_frame()
        process_name = self._ax_process_name()
        if process_name is None:
            raise AzaharError("Azahar window not found")
        escaped = title.replace("\\", "\\\\").replace('"', '\\"')
        cx = x + max(w // 2, 8)
        cy = y + max(28 + (h - 28) // 2, 40)
        hold = HOLD_S if hold_s is None else max(float(hold_s), 0.0)
        gap = max(float(gap_s), 0.0)
        hid_lead = 0.72
        as_delay = max(1.6, hid_lead + duration + 0.4)
        hid_error: list[BaseException] = []
        taps_done = [0]

        def send_hid() -> None:
            try:
                time.sleep(0.5)
                left_click_at(cx, cy)
                time.sleep(0.22)
                deadline = time.monotonic() + duration
                while time.monotonic() < deadline:
                    hid_tap(key, hold_s=hold)
                    taps_done[0] += 1
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(gap, remaining))
            except BaseException as exc:
                hid_error.append(exc)

        worker = threading.Thread(target=send_hid, daemon=True)
        worker.start()
        _applescript(
            f"""
            tell application "System Events"
              tell process "{process_name}"
                set frontmost to true
                delay 0.1
                repeat with w in windows
                  try
                    if (name of w as text) is "{escaped}" then
                      perform action "AXRaise" of w
                      set index of w to 1
                      exit repeat
                    end if
                  end try
                end repeat
                delay 0.2
              end tell
              delay {as_delay:.3f}
            end tell
            """
        )
        worker.join(timeout=as_delay + 2.0)
        self._raise_hid_error(hid_error)
        return taps_done[0]

    def hold_keys(self, keys: list[str], hold_s: float = 0.5) -> None:
        """Hold several mapped keys at once (e.g. L+R+Start)."""
        from botusum.inputs import left_click_at, press_key, release_key

        title, x, y, w, h = self._game_frame()
        process_name = self._ax_process_name()
        if process_name is None:
            raise AzaharError("Azahar window not found")
        escaped = title.replace("\\", "\\\\").replace('"', '\\"')
        cx = x + max(w // 2, 8)
        cy = y + max(28 + (h - 28) // 2, 40)
        hold = max(float(hold_s), 0.01)
        key_list = list(keys)
        hid_lead = 0.72
        as_delay = max(1.6, hid_lead + hold + 0.4)
        hid_error: list[BaseException] = []

        def send_hid() -> None:
            try:
                time.sleep(0.5)
                left_click_at(cx, cy)
                time.sleep(0.22)
                for key in key_list:
                    press_key(key)
                time.sleep(hold)
                for key in reversed(key_list):
                    release_key(key)
            except BaseException as exc:
                hid_error.append(exc)

        worker = threading.Thread(target=send_hid, daemon=True)
        worker.start()
        _applescript(
            f"""
            tell application "System Events"
              tell process "{process_name}"
                set frontmost to true
                delay 0.1
                repeat with w in windows
                  try
                    if (name of w as text) is "{escaped}" then
                      perform action "AXRaise" of w
                      set index of w to 1
                      exit repeat
                    end if
                  end try
                end repeat
                delay 0.2
              end tell
              delay {as_delay:.3f}
            end tell
            """
        )
        worker.join(timeout=as_delay + 2.0)
        self._raise_hid_error(hid_error)

    def _raise_hid_error(self, hid_error: list[BaseException]) -> None:
        if not hid_error:
            return
        exc = hid_error[0]
        raise AzaharError(str(exc)) from exc

    def _raise_and_click(self, title: str, x: int, y: int, w: int, h: int) -> None:
        process_name = self._ax_process_name()
        if process_name is None:
            raise AzaharError("Azahar window not found")
        escaped = title.replace("\\", "\\\\").replace('"', '\\"')
        cx = x + max(w // 2, 8)
        cy = y + max(h // 2, 12)
        _applescript(
            f"""
            tell application "System Events"
              tell process "{process_name}"
                set frontmost to true
                delay 0.08
                repeat with w in windows
                  try
                    if (name of w as text) is "{escaped}" then
                      perform action "AXRaise" of w
                      exit repeat
                    end if
                  end try
                end repeat
                delay 0.08
                click at {{{cx}, {cy}}}
              end tell
            end tell
            """
        )
        time.sleep(0.12)

    def wait_for_window(self, timeout_s: float = WINDOW_TIMEOUT_S) -> list[str]:
        deadline = time.time() + timeout_s
        last_error: BaseException | None = None
        while time.time() < deadline:
            if not self.is_running():
                raise AzaharError("Azahar exited while waiting for its window")
            try:
                titles = self.window_titles()
            except AzaharError as exc:
                last_error = exc
                time.sleep(0.3)
                continue
            if titles:
                return titles
            time.sleep(0.3)
        if last_error is not None:
            raise AzaharError(str(last_error)) from last_error
        raise AzaharError("Timed out waiting for an Azahar window")

    def connect_rpc(self) -> tuple[RpcClient, dict[int, tuple[int, str]]]:
        client = RpcClient()
        try:
            processes = client.wait_until_ready()
        except RpcError as exc:
            raise AzaharError(str(exc)) from exc
        return client, processes

    def ensure_ready(self) -> tuple[bool, list[str], RpcClient, dict[int, tuple[int, str]]]:
        """Launch or reuse Azahar, wait for a window, then wait for RPC."""
        reused = self.launch()
        self.wait_for_process()
        titles = self.wait_for_window()
        client, processes = self.connect_rpc()
        return reused, titles, client, processes
