"""Default and resolved filesystem paths for the hunt."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ULTRA_MOON_ROM_NAME = "Pokemon Ultra Luna.3ds"
ULTRA_MOON_TITLE_ID = "00040000001B5100"

DEFAULT_AZAHAR_APP = Path("/Applications/Azahar.app")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_azahar_user_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / "Azahar"


def resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


def resolve_azahar_app(path: Path) -> Path:
    """Accept either the .app bundle or the inner MacOS binary."""
    path = resolve_path(path)
    if path.name == "azahar" and path.parent.name == "MacOS":
        return path.parent.parent.parent
    return path


def azahar_executable(app: Path) -> Path:
    app = resolve_azahar_app(app)
    if app.suffix == ".app":
        return app / "Contents" / "MacOS" / "azahar"
    return app


def ultra_moon_save(user_dir: Path) -> Path:
    return (
        user_dir
        / "sdmc"
        / "Nintendo 3DS"
        / "00000000000000000000000000000000"
        / "00000000000000000000000000000000"
        / "title"
        / "00040000"
        / "001b5100"
        / "data"
        / "00000001"
        / "main"
    )


@dataclass(frozen=True)
class HuntPaths:
    repo_root: Path
    ultra_moon_rom: Path
    azahar_app: Path
    azahar_user_dir: Path

    @classmethod
    def defaults(
        cls,
        *,
        ultra_moon_rom: Path | None = None,
        azahar_app: Path | None = None,
        azahar_user_dir: Path | None = None,
    ) -> HuntPaths:
        root = repo_root()
        resources = root / "resources"
        user_dir = resolve_path(azahar_user_dir or default_azahar_user_dir())
        app = resolve_azahar_app(azahar_app or DEFAULT_AZAHAR_APP)
        return cls(
            repo_root=root,
            ultra_moon_rom=resolve_path(ultra_moon_rom or resources / ULTRA_MOON_ROM_NAME),
            azahar_app=app,
            azahar_user_dir=user_dir,
        )

    @property
    def resources_dir(self) -> Path:
        return (self.repo_root / "resources").resolve()

    @property
    def logs_dir(self) -> Path:
        return (self.repo_root / "logs").resolve()

    @property
    def azahar_binary(self) -> Path:
        return azahar_executable(self.azahar_app)

    @property
    def ultra_moon_main(self) -> Path:
        return ultra_moon_save(self.azahar_user_dir)

    def missing(self) -> list[tuple[str, Path]]:
        required = (
            ("Ultra Moon ROM", self.ultra_moon_rom, "file"),
            ("Azahar app", self.azahar_app, "dir"),
        )
        missing: list[tuple[str, Path]] = []
        for label, path, kind in required:
            ok = path.is_file() if kind == "file" else path.is_dir()
            if not ok:
                missing.append((label, path))
        return missing
