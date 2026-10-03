"""Installs a Linux desktop entry and the icon set for the current user.

Everything goes into ``~/.local/share`` - no root, nothing outside the home
directory, and it is removed again just as easily:

    python -m eggnoxx.desktop install
    python -m eggnoxx.desktop uninstall
    python -m eggnoxx.desktop status
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_ID = "eggnoxx"
APP_NAME = "EggNoxx"
APP_SUMMARY = "Minimalistische Schwarz-Weiß-Eieruhr"
APP_COMMENT = "Eieruhr im Retro-Pixel-Look: Presets, freier Timer und Alarm."

ICON_SIZES = (16, 22, 24, 32, 48, 64, 128, 256)
XDG_DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
APPLICATIONS_DIR = XDG_DATA / "applications"
ICON_ROOT = XDG_DATA / "icons" / "hicolor"
DESKTOP_FILE = APPLICATIONS_DIR / f"{APP_ID}.desktop"


def icon_source_dir() -> Path:
    return Path(__file__).parent / "assets" / "icons"


def launch_command() -> list[str]:
    """The command that starts the app.

    Prefers the console script created by ``pip install``. Otherwise falls back
    to this interpreter with ``-m``, plus an explicit PYTHONPATH: a desktop
    entry runs with an arbitrary working directory, so a source checkout that
    was never installed would otherwise fail to import.
    """
    interpreter = Path(sys.executable)
    for script in (interpreter.parent / APP_ID, Path("/usr/local/bin") / APP_ID):
        if script.exists():
            return [str(script)]
    return [str(interpreter), "-m", APP_ID]


def desktop_contents() -> str:
    exec_line = " ".join(launch_command())
    return f"""[Desktop Entry]
Type=Application
Version=1.5
Name={APP_NAME}
GenericName=Eieruhr
Comment={APP_COMMENT}
Exec={exec_line}
Icon={APP_ID}
Terminal=false
Categories=Utility;
Keywords=Eier;Eieruhr;Timer;Kochen;Boil;Egg;
StartupNotify=true
StartupWMClass={APP_ID}
Path={Path(__file__).resolve().parent.parent}
"""


def install_icons() -> list[Path]:
    """Copy every bundled size into the hicolor theme; returns the targets."""
    source = icon_source_dir()
    written = []
    for size in ICON_SIZES:
        icon = source / f"{size}x{size}.png"
        if not icon.exists():
            continue
        target_dir = ICON_ROOT / f"{size}x{size}" / "apps"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{APP_ID}.png"
        shutil.copyfile(icon, target)
        written.append(target)
    return written


def install() -> int:
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    icons = install_icons()
    DESKTOP_FILE.write_text(desktop_contents(), encoding="utf-8")
    DESKTOP_FILE.chmod(0o755)
    _refresh_caches()

    print(f"Desktop-Eintrag: {DESKTOP_FILE}")
    print(f"Icons installiert: {len(icons)}")
    print(f"Start via:        {DESKTOP_FILE}")
    return 0


def uninstall() -> int:
    removed = False
    if DESKTOP_FILE.exists():
        DESKTOP_FILE.unlink()
        removed = True
    for size in ICON_SIZES:
        icon = ICON_ROOT / f"{size}x{size}" / "apps" / f"{APP_ID}.png"
        if icon.exists():
            icon.unlink()
            removed = True
    _refresh_caches()
    print("Entfernt." if removed else "Nichts zu entfernen.")
    return 0


def status() -> int:
    print(f"Desktop-Eintrag: {DESKTOP_FILE} ({'vorhanden' if DESKTOP_FILE.exists() else 'fehlt'})")
    for size in ICON_SIZES:
        icon = ICON_ROOT / f"{size}x{size}" / "apps" / f"{APP_ID}.png"
        print(f"  Icon {size:>3}px: {'ok' if icon.exists() else 'fehlt'}")
    return 0


def _refresh_caches() -> None:
    """Let the desktop notice the new files without a logout."""
    for command in (
        ["update-desktop-database", str(APPLICATIONS_DIR)],
        ["gtk-update-icon-cache", "-f", "-t", str(XDG_DATA / "icons" / "hicolor")],
    ):
        if shutil.which(command[0]):
            subprocess.run(command, check=False, capture_output=True)


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    action = args[0] if args else "install"
    if action == "install":
        return install()
    if action == "uninstall":
        return uninstall()
    if action == "status":
        return status()
    print(
        f"Unbekanntes Kommando: {action}\n"
        "Verwendung: python -m eggnoxx.desktop [install|uninstall|status]"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
