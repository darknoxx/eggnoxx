"""End-of-time signalling: terminal bell plus an inverting blink."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QWidget

from eggnoxx.theme import BLACK, BLINK_MS, NEAR_BLACK, NEAR_WHITE, WHITE, stylesheet


class Alarmer(QObject):
    """Beeps once per second and blinks the window until acknowledged.

    The blink swaps the application stylesheet (and the window palette the egg
    reads), so the entire window inverts rather than just the numbers.
    """

    def __init__(self, target: QWidget) -> None:
        super().__init__(target)
        self._target = target
        self._app = QApplication.instance()
        self._beep_timer = QTimer(self)
        self._beep_timer.setInterval(1000)
        self._beep_timer.timeout.connect(self._beep)
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(BLINK_MS)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_on = False

    @property
    def is_active(self) -> bool:
        return self._beep_timer.isActive()

    def start(self) -> None:
        self._beep()
        self._beep_timer.start()
        self._blink_on = True
        self._blink_timer.start()
        self._apply_blink()

    def stop(self) -> None:
        self._beep_timer.stop()
        self._blink_timer.stop()
        self._blink_on = False
        self._apply_blink()

    def _beep(self) -> None:
        """Best-effort console bell; harmless if the system mutes it."""
        QApplication.beep()
        sys.stdout.write("\a")
        sys.stdout.flush()

    def _toggle_blink(self) -> None:
        self._blink_on = not self._blink_on
        self._apply_blink()

    def _apply_blink(self) -> None:
        dark = not self._blink_on
        if self._app is not None:
            self._app.setStyleSheet(stylesheet(dark=dark))

        palette = QPalette()
        if dark:
            palette.setColor(QPalette.ColorRole.Window, BLACK)
            palette.setColor(QPalette.ColorRole.WindowText, WHITE)
            palette.setColor(QPalette.ColorRole.Mid, NEAR_WHITE)
        else:
            palette.setColor(QPalette.ColorRole.Window, WHITE)
            palette.setColor(QPalette.ColorRole.WindowText, BLACK)
            palette.setColor(QPalette.ColorRole.Mid, NEAR_BLACK)
        self._target.setPalette(palette)
        self._target.style().unpolish(self._target)
        self._target.style().polish(self._target)
