"""Launch / reuse Azahar with the ROM. Ctrl+C must not kill the emulator."""

from __future__ import annotations

import subprocess
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

    def window_titles(self) -> list[str]:
        if not self.is_running():
            return []
        for process_name in (APPLESCRIPT_PROCESS, "azahar"):
            raw = _applescript(
                f"""
                tell application "System Events"
                  if not (exists process "{process_name}") then return ""
                  tell process "{process_name}"
                    set out to ""
                    repeat with w in windows
                      try
                        set nm to name of w as text
                        if nm is not "" then set out to out & nm & linefeed
                      end try
                    end repeat
                    return out
                  end tell
                end tell
                """
            )
            titles = [line for line in raw.splitlines() if line.strip()]
            if titles:
                return titles
        return []

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
