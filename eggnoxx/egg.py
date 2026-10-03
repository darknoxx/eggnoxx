"""The egg: a minimalist outline that fills up while it cooks.

Colours are taken from the widget palette, so the alarm blink (which inverts
the palette) also inverts the egg automatically.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPalette
from PySide6.QtWidgets import QSizePolicy, QWidget

EGG_RATIO = 1.32  # height / width


class EggWidget(QWidget):
    """Draws an egg shape filled from the bottom according to ``progress``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._progress = 0.0
        self.setMinimumSize(110, 130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def progress(self) -> float:
        return self._progress

    def set_progress(self, value: float) -> None:
        value = min(1.0, max(0.0, float(value)))
        if abs(value - self._progress) > 0.001:
            self._progress = value
            self.update()

    def _egg_rect(self) -> QRectF:
        """Largest egg-shaped rect that fits, keeping it centred."""
        width = min(self.width() * 0.62, (self.height() * 0.92) / EGG_RATIO)
        height = width * EGG_RATIO
        return QRectF(
            (self.width() - width) / 2,
            (self.height() - height) / 2,
            width,
            height,
        )

    def _egg_path(self, rect: QRectF) -> QPainterPath:
        """Symmetric two-cubic egg outline: wide and round at the bottom."""
        left, top, width, height = rect.x(), rect.y(), rect.width(), rect.height()
        bottom = top + height
        mid = left + width / 2

        path = QPainterPath(QPointF(mid, bottom))
        path.cubicTo(mid - width * 0.30, bottom, left, top + height * 0.44, mid, top)
        path.cubicTo(left + width, top + height * 0.44, mid + width * 0.30, bottom, mid, bottom)
        path.closeSubpath()
        return path

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        del event
        fore = self.palette().color(QPalette.ColorRole.WindowText)
        back = self.palette().color(QPalette.ColorRole.Window)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillRect(self.rect(), back)

        egg = self._egg_path(self._egg_rect())

        # Cooked portion: solid, clipped to the inside of the shell.
        if self._progress > 0:
            painter.save()
            painter.setClipPath(egg)
            filled = QRectF(
                egg.boundingRect().left(),
                egg.boundingRect().bottom() - egg.boundingRect().height() * self._progress,
                egg.boundingRect().width(),
                egg.boundingRect().height() * self._progress,
            )
            painter.fillRect(filled, fore)
            painter.restore()

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(fore)
        painter.drawPath(egg)
        painter.end()
