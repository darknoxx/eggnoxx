"""Retro chrome: a dotted grid background and corner ticks around the content.

Both are drawn with hard 1px primitives so they stay in the same visual language
as the pixel font and the pixel-art egg.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QWidget

from eggnoxx import theme

DOT_SPACING = 6  # background dot grid
TICK_LENGTH = 12  # corner tick arms
TICK_MARGIN = 8
LIGHT_GRID = QColor("#e6e6e6")


class Panel(QWidget):
    """Container that paints the dotted backdrop and the corner brackets."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        background = self.palette().color(self.backgroundRole())
        painter.fillRect(self.rect(), background)

        # The dot grid follows the blink, so take the shade from the background.
        painter.setPen(LIGHT_GRID if background.lightness() > 127 else theme.GRID)
        for y in range(0, self.height(), DOT_SPACING):
            for x in range(0, self.width(), DOT_SPACING):
                painter.drawPoint(x, y)

        self._draw_ticks(painter)
        painter.end()

    def _draw_ticks(self, painter: QPainter) -> None:
        """Four corner brackets, the one flourish that breaks the sterility."""
        pen = painter.pen()
        pen.setColor(self.palette().color(self.foregroundRole()))
        pen.setWidth(1)
        painter.setPen(pen)

        left, top = TICK_MARGIN, TICK_MARGIN
        right, bottom = self.width() - 1 - TICK_MARGIN, self.height() - 1 - TICK_MARGIN
        for x, y, dx, dy in (
            (left, top, 1, 1),
            (right, top, -1, 1),
            (left, bottom, 1, -1),
            (right, bottom, -1, -1),
        ):
            painter.drawLine(QPoint(x, y), QPoint(x + dx * TICK_LENGTH, y))
            painter.drawLine(QPoint(x, y), QPoint(x, y + dy * TICK_LENGTH))

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().resizeEvent(event)
        self.update()


def separator(parent: QWidget | None = None) -> QFrame:
    """1px hairline; coloured by the stylesheet so it inverts with the blink."""
    line = QFrame(parent)
    line.setObjectName("rule")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line
