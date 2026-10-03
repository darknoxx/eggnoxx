"""Tests for the theme layer, especially without a running QApplication.

Regression guard: touching QFontDatabase before a QGuiApplication exists
crashes Qt outright, and ``load_fonts()`` used to do exactly that.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_load_fonts_without_app_returns_empty() -> None:
    """Must not crash - Qt segfaults if QFontDatabase is touched too early."""
    from PySide6.QtGui import QGuiApplication

    from eggnoxx import theme

    if QGuiApplication.instance() is not None:
        pytest.skip("QApplication läuft bereits in diesem Prozess")
    assert theme.load_fonts() == ""


def test_pixel_font_without_app_falls_back() -> None:
    from PySide6.QtGui import QGuiApplication

    from eggnoxx import theme

    if QGuiApplication.instance() is not None:
        pytest.skip("QApplication läuft bereits in diesem Prozess")
    font = theme.pixel(14)
    assert font.pixelSize() == 14


def test_load_fonts_with_app_returns_family() -> None:
    from PySide6.QtWidgets import QApplication

    from eggnoxx import theme

    QApplication.instance() or QApplication(["eggnoxx-theme-test"])
    assert theme.load_fonts() == theme.PIXEL_FAMILY


def test_bundled_font_files_exist() -> None:
    """The wheel ships them; without them the look silently degrades."""
    from eggnoxx import theme

    for name in theme.PIXEL_FONT_FILES:
        assert (theme.FONT_DIR / name).exists(), f"{name} fehlt"


def test_license_file_ships_with_the_font() -> None:
    from eggnoxx import theme

    assert (theme.FONT_DIR / "OFL.txt").exists()


def test_stylesheet_has_no_font_size() -> None:
    """font-size in QSS would override the per-widget pixel sizes."""
    from eggnoxx import theme

    assert "font-size" not in theme.stylesheet()
    assert "font-size" not in theme.stylesheet(dark=False)


def test_both_stylesheet_variants_differ_in_colour() -> None:
    from eggnoxx import theme

    assert theme.stylesheet(dark=True) != theme.stylesheet(dark=False)


def test_dark_variant_is_black_on_white_text() -> None:
    from eggnoxx import theme

    sheet = theme.stylesheet(dark=True)
    assert theme.BLACK.name() in sheet
    assert theme.WHITE.name() in sheet
