"""Tests for the generated icon art and the desktop entry (offscreen Qt)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

# The icon code rasterises with Qt, which needs a platform plugin; offscreen
# keeps the test headless. Must happen before the first Qt import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from eggnoxx import icon  # noqa: E402
from eggnoxx.desktop import (  # noqa: E402
    APP_ID,
    ICON_SIZES,
    desktop_contents,
    launch_command,
)


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(["eggnoxx-test"])


@pytest.mark.parametrize("cells", [16, 24, 32])
def test_icon_has_requested_size(app, cells: int) -> None:
    image = icon.render_icon(cells=cells)
    assert image.width() == cells
    assert image.height() == cells


def test_icon_is_square_and_transparent_at_the_corners(app) -> None:
    image = icon.render_icon(cells=32)
    assert image.hasAlphaChannel()
    assert image.pixelColor(0, 0).alpha() < 255, "Ecken müssen transparent sein"


def test_icon_contains_a_bright_egg(app) -> None:
    """Something light in the middle, or the icon would be a black square."""
    image = icon.render_icon(cells=32)
    bright = sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).value() > 200
    )
    assert bright > 20, "das Ei fehlt im Icon"


def test_icon_is_not_half_filled(app) -> None:
    """A part-filled egg reads as a blob at dock sizes, so it is solid."""
    image = icon.render_icon(cells=32)
    assert icon.FILL_PROGRESS == 1.0
    mid_x = 16
    # The egg reaches close to the top of the plate.
    column = [y for y in range(32) if image.pixelColor(mid_x, y).value() > 200]
    assert column, "kein Ei in der Mitte"
    assert min(column) <= 6, "Ei ist oben abgeschnitten"


def test_every_icon_size_renders(app) -> None:
    for size in ICON_SIZES:
        image = icon.render_icon(cells=icon.GRID_FOR_SIZE[size])
        assert image.width() == icon.GRID_FOR_SIZE[size]


def test_desktop_entry_is_complete() -> None:
    text = desktop_contents()
    for key in ("[Desktop Entry]", "Type=Application", "Name=EggNoxx", "Icon=eggnoxx"):
        assert key in text, f"{key} fehlt in der Desktop-Datei"
    assert "Terminal=false" in text
    assert f"StartupWMClass={APP_ID}" in text


def test_desktop_exec_uses_an_existing_command() -> None:
    """A desktop entry with a dangling Exec silently fails to launch."""
    command = launch_command()
    assert command, "kein Startkommando ermittelt"
    assert Path(command[0]).exists(), f"{command[0]} existiert nicht"


def test_desktop_entry_has_no_unregistered_category() -> None:
    """desktop-file-validate rejects unknown categories."""
    assert "Kitchenware" not in desktop_contents()


def test_desktop_entry_has_no_path_key() -> None:
    """A Path= pointing at the source checkout breaks an installed copy."""
    assert "\nPath=" not in desktop_contents()


def test_exec_is_an_absolute_path() -> None:
    """A relative Exec would only work from one directory."""
    command = launch_command()
    assert command[0].startswith("/"), f"{command[0]} ist nicht absolut"
