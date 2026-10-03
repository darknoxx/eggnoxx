"""Monochrome design tokens: colours, fonts and the global stylesheet."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontDatabase

BLACK = QColor("#000000")
WHITE = QColor("#ffffff")
NEAR_BLACK = QColor("#0b0b0b")
NEAR_WHITE = QColor("#e9e9e9")
GREY = QColor("#8c8c8c")

TICK_MS = 100
BLINK_MS = 500


def mono_font(size: int, weight: QFont.Weight = QFont.Weight.Medium) -> QFont:
    """A monospaced, tabular font so digits never jitter while counting."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    font.setPointSize(size)
    font.setWeight(weight)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setFixedPitch(True)
    return font


def ui_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont()
    font.setPointSize(size)
    font.setWeight(weight)
    return font


def stylesheet(dark: bool = True) -> str:
    """Flat styling: 1px borders, no colour, no gradients.

    Two variants exist purely so the finished-timer blink can invert the whole
    window, not just the palette.
    """
    bg, fg = (BLACK, WHITE) if dark else (WHITE, BLACK)
    soft = NEAR_WHITE if dark else NEAR_BLACK
    muted = GREY if dark else QColor("#4a4a4a")
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
        padding: 10px 18px;
        font-size: 15px;
    }}
    QPushButton:hover {{
        background: {fg.name()};
        color: {bg.name()};
    }}
    QPushButton:pressed {{
        background: {soft.name()};
        color: {bg.name()};
    }}
    QPushButton:checked {{
        background: {fg.name()};
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
        padding: 8px;
        font-size: 16px;
        min-width: 62px;
    }}
    QSpinBox:focus {{
        border: 1px solid {fg.name()};
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid {fg.name()};
        background: {bg.name()};
    }}
    QCheckBox::indicator:checked {{
        background: {fg.name()};
    }}
    QPushButton#alarmButton {{
        font-size: 18px;
        padding: 14px 26px;
    }}
    QLabel#title {{
        font-size: 11px;
        font-weight: bold;
    }}
    QLabel#muted {{
        color: {muted.name()};
    }}
    QFrame#rule {{
        background: {soft.name()};
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}
    """
