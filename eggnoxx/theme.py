"""Design tokens: colours and the bundled pixel font.

Fonts are *not* styled through the stylesheet (``font-size`` in QSS would
override the per-widget pixel sizes), so every widget gets its font from here.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
PIXEL_FONT_FILES = ("Silkscreen-Regular.ttf", "Silkscreen-Bold.ttf")
PIXEL_FAMILY = "Silkscreen"

BLINK_MS = 500

# Core monochrome palette. Everything else derives from these two, so the blink
# can swap them and the whole window follows.
BLACK = QColor("#000000")
WHITE = QColor("#ffffff")

# Supporting shades
DIM = QColor("#6b6b6b")  # captions, hints
GRID = QColor("#141414")  # background dot grid
HAIRLINE = QColor("#2e2e2e")  # separators, button borders
LIGHT_GRID = QColor("#e6e6e6")  # dot grid on the inverted background

_font_loaded = False


def _running_app():
    """The live QGuiApplication, or None. Querying this is crash-safe."""
    from PySide6.QtGui import QGuiApplication

    return QGuiApplication.instance()


def load_fonts() -> str:
    """Register the bundled pixel font; return the usable family name.

    Returns an empty string when there is no usable font, which makes the
    callers fall back to the system font. Calling this without a running
    ``QGuiApplication`` is safe but pointless: Qt needs one to know about font
    databases, and touching ``QFontDatabase`` before that crashes.
    """
    global _font_loaded
    if _running_app() is None:
        return ""

    if not _font_loaded:
        _font_loaded = True
        for name in PIXEL_FONT_FILES:
            path = FONT_DIR / name
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))

    available = set(QFontDatabase.families())
    return PIXEL_FAMILY if PIXEL_FAMILY in available else ""


def pixel(size: int, bold: bool = False) -> QFont:
    """Bundled pixel font at an exact pixel size, with a safe fallback."""
    family = load_fonts()
    if family:
        font = QFont(family)
    else:  # assets missing (e.g. installed without package data)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
    font.setPixelSize(size)
    font.setBold(bold)
    return font


def stylesheet(dark: bool = True) -> str:
    """Flat styling: 1px borders, no colour, no gradients.

    Two variants exist purely so the finished-timer blink can invert the whole
    window. Font sizes are intentionally absent - see module docstring.
    """
    bg, fg = (BLACK, WHITE) if dark else (WHITE, BLACK)
    soft = HAIRLINE if dark else QColor("#d4d4d4")
    muted = DIM if dark else QColor("#4a4a4a")
    return f"""
    QWidget {{
        background: {bg.name()};
        color: {fg.name()};
    }}
    QLabel {{
        background: transparent;
        color: {fg.name()};
    }}
    QPushButton {{
        background: {bg.name()};
        color: {fg.name()};
        border: 1px solid {soft.name()};
        padding: 4px 6px;
    }}
    QPushButton:hover {{
        background: {fg.name()};
        color: {bg.name()};
    }}
    QPushButton:pressed {{
        background: {soft.name()};
        color: {bg.name()};
    }}
    QPushButton:disabled {{
        color: {muted.name()};
        border: 1px solid {muted.name()};
    }}
    QSpinBox {{
        background: {bg.name()};
        color: {fg.name()};
        border: 1px solid {soft.name()};
        padding: 4px;
    }}
    QSpinBox:focus {{
        border: 1px solid {fg.name()};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 12px;
    }}
    QCheckBox {{
        spacing: 7px;
        color: {muted.name()};
    }}
    QCheckBox::indicator {{
        width: 9px;
        height: 9px;
        border: 1px solid {muted.name()};
        background: {bg.name()};
    }}
    QCheckBox::indicator:checked {{
        background: {fg.name()};
    }}
    QFrame#rule {{
        background: {soft.name()};
        border: none;
        max-height: 1px;
        min-height: 1px;
    }}
    """
