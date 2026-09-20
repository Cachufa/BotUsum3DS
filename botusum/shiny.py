"""When-shiny path: in-game save flush, incremental main copy, log, notify stub."""

from __future__ import annotations

import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from botusum.huntlog import HuntLog, total_hunt_seconds, utc_now
from botusum.notify import notify_shiny

SHINY_ARCHIVE_STEM = "main-poipole-shiny"
FORCE_SHINY_SV = 0
SAVE_FLUSH_TIMEOUT_S = 20.0
SAVE_FLUSH_POLL_S = 0.1
SAVE_FLUSH_STABLE_S = 0.4

_SHINY_ARCHIVE_RE = re.compile(rf"^{re.escape(SHINY_ARCHIVE_STEM)}-(\d+)$")


class ShinyError(Exception):
    """Live save missing, copy failed, or Azahar `main` did not flush."""


def file_fingerprint(path: Path) -> tuple[int, int] | None:
    """`(mtime_ns, size)` or None if the file is missing."""
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def wait_for_main_flush(
    path: Path,
    before: tuple[int, int] | None,
    *,
    timeout_s: float = SAVE_FLUSH_TIMEOUT_S,
    poll_s: float = SAVE_FLUSH_POLL_S,
    stable_s: float = SAVE_FLUSH_STABLE_S,
) -> tuple[int, int]:
    """Wait until `path` differs from `before`, then stays still."""
    deadline = time.monotonic() + timeout_s
    changed: tuple[int, int] | None = None
    while time.monotonic() < deadline:
        current = file_fingerprint(path)
        if current is not None and current != before:
            changed = current
            break
        time.sleep(poll_s)
    if changed is None:
        raise ShinyError(f"Azahar main did not flush after in-game save: {path}")
    last = changed
    stable_until = time.monotonic() + stable_s
    while time.monotonic() < stable_until:
        if time.monotonic() >= deadline:
            raise ShinyError(f"Azahar main kept changing after save: {path}")
        time.sleep(poll_s)
        current = file_fingerprint(path)
        if current is None:
            continue
        if current != last:
            last = current
            stable_until = time.monotonic() + stable_s
    final = file_fingerprint(path)
    if final is None:
        raise ShinyError(f"Azahar main missing after save: {path}")
    return final


def next_shiny_archive(resources_dir: Path) -> Path:
    """`resources/main-poipole-shiny-N` with N = 1 + max existing."""
    max_n = 0
    if resources_dir.is_dir():
        for entry in resources_dir.iterdir():
            match = _SHINY_ARCHIVE_RE.fullmatch(entry.name)
            if match:
                max_n = max(max_n, int(match.group(1)))
    return resources_dir / f"{SHINY_ARCHIVE_STEM}-{max_n + 1}"


def copy_main_archive(live_main: Path, dest: Path) -> Path:
    if not live_main.is_file():
        raise ShinyError(f"Live Ultra Moon save not found: {live_main}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(live_main, dest)
    return dest


def archive_log_path(dest: Path, repo_root: Path) -> Path:
    """Repo-relative path for `save=` in the SHINY summary line."""
    try:
        return dest.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return dest


def handle_shiny(
    hunt_log: HuntLog,
    *,
    attempt: int,
    duration_s: float,
    sv: int,
    live_main: Path,
    resources_dir: Path,
    repo_root: Path,
    when: datetime | None = None,
) -> int:
    """Copy `main` to the next archive, log attempt + summary, return 0.

    Does not soft-reset. Callers must save in-game (or skip that for
    `--force-shiny`) before this runs. Never overwrites Azahar's live `main`.
    """
    dest = copy_main_archive(live_main, next_shiny_archive(resources_dir))
    logged = archive_log_path(dest, repo_root)
    stamp = when if when is not None else utc_now()
    hunt_log.write_attempt(
        attempt=attempt,
        duration_s=duration_s,
        sv=sv,
        result="shiny",
        when=stamp,
    )
    started = hunt_log.hunt_started() or stamp
    total_s = total_hunt_seconds(started, stamp)
    hunt_log.write_shiny_summary(
        attempts=attempt,
        total_s=total_s,
        sv=sv,
        save=logged,
        when=stamp,
    )
    notify_shiny(
        attempt=attempt,
        sv=sv,
        total_s=total_s,
        save_path=dest,
    )
    return 0
