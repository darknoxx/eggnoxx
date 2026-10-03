"""The egg, drawn as pixel art.

The shape is rasterised into a small low-resolution image and then scaled up with
nearest-neighbour sampling, which gives real chunky pixels instead of a smooth
vector outline. Progress fills the interior from the bottom.
"""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QSizePolicy, QWidget

SUPERELLIPSE = 2.0  # 2.0 is a true ellipse; higher rounds the ends off
TAPER = 0.5  # how much narrower the top is than the bottom
EGG_ASPECT = 1.48  # egg height / egg width
FILL_FRACTION = 0.74  # share of the widget the egg width may use
TARGET_CELLS = 30  # rough cell count across the widget for the pixel scale


def egg_profile(u: float) -> float:
    """Half-width profile of the egg.

    ``u`` runs from 0 at the bottom to 1 at the top; the result is 0..1 where 1
    is the widest point. A superellipse gives the rounded ends and the taper
    term shifts the widest point below the middle, so the top stays pointier.
    """
    if u <= 0.0 or u >= 1.0:
        return 0.0
    s = 2.0 * u - 1.0
    base = max(0.0, 1.0 - abs(s) ** SUPERELLIPSE) ** (1.0 / SUPERELLIPSE)
    return base * (1.0 - TAPER * (u - 0.5))


_STEPS = 64


def _volume_table() -> list[float]:
    """Normalised area of the egg below each height step, from 0 to 1."""
    widths = [egg_profile(i / _STEPS) for i in range(_STEPS + 1)]
    total = sum(widths) or 1.0
    table, running = [], 0.0
    for width in widths:
        running += width
        table.append(running / total)
    return table


_VOLUME = _volume_table()


def fill_height(progress: float) -> float:
    """Egg height (0..1) whose *area* matches the elapsed share of time.

    ``progress`` is linear in time, but the eye reads the egg as a container, so
    filling it linearly would make it race to the top and then crawl. Mapping
    through the cumulative area keeps the perceived rise even.
    """
    if progress <= 0.0:
        return 0.0
    if progress >= 1.0:
        return 1.0
    lo, hi = 0, _STEPS
    while lo < hi:  # bisection on the monotonic area table
        mid = (lo + hi) // 2
        if _VOLUME[mid] < progress:
            lo = mid + 1
        else:
            hi = mid
    return lo / _STEPS


class EggWidget(QWidget):
    """A pixel-art egg that fills up as it cooks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._progress = 0.0
        self.setMinimumSize(90, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def progress(self) -> float:
        return self._progress

    def set_progress(self, value: float) -> None:
        value = min(1.0, max(0.0, float(value)))
        if abs(value - self._progress) > 0.004:
            self._progress = value
            self.update()

    # -- geometry -------------------------------------------------------
    def _cell_size(self) -> int:
        """Integer pixel size, so scaling never blurs the pixels.

        Based on the width only: deriving it from the height as well made the
        egg shrink to a thin outline whenever the layout gave it a wide, short
        slot (the widget expands to the full window width).
        """
        return max(3, int(self.width() / TARGET_CELLS))

    def _grid(self) -> tuple[int, int]:
        cell = self._cell_size()
        return max(8, self.width() // cell), max(10, self.height() // cell)

    def _egg_box(
        self,
        grid_w: int,
        grid_h: int,
        fill_fraction: float = FILL_FRACTION,
        aspect: float = EGG_ASPECT,
    ) -> tuple[float, float, float, float]:
        """Egg bounding box in cell units: (left, top, width, height)."""
        box_w = min(grid_w * fill_fraction, (grid_h * 0.94) / aspect)
        box_h = box_w * aspect
        return (grid_w - box_w) / 2, (grid_h - box_h) / 2, box_w, box_h

    def _rasterise(
        self,
        grid_w: int,
        grid_h: int,
        shell,
        fill,
        empty,
        inset: float = 1.2,
        fill_fraction: float = FILL_FRACTION,
        aspect: float = EGG_ASPECT,
    ) -> QImage:
        """One pixel per cell: 1px shell, filled interior from the bottom.

        ``inset`` is the shell thickness in cells; it has to stay below 1 for
        small grids such as an icon, or the interior disappears entirely.
        """
        image = QImage(grid_w, grid_h, QImage.Format_ARGB32)
        image.fill(empty)

        left, top, box_w, box_h = self._egg_box(grid_w, grid_h, fill_fraction, aspect)
        half_w = box_w / 2
        level = fill_height(self._progress)

        for row in range(grid_h):
            y = row + 0.5
            u = 1.0 - (y - top) / box_h  # 1 at the top of the egg, 0 at the bottom
            if u <= 0.0 or u >= 1.0:
                continue
            profile = egg_profile(u)
            if profile <= 0.0:
                continue
            half = profile * half_w
            inner = half - inset
            cooked = u <= level

            # Only touch the columns the egg can reach.
            first = max(0, int(left + half_w - half))
            last = min(grid_w - 1, int(left + half_w + half))
            for col in range(first, last + 1):
                distance = abs(col + 0.5 - (left + half_w))
                if distance > half:
                    continue
                if distance > inner:
                    image.setPixelColor(col, row, shell)
                elif cooked:
                    image.setPixelColor(col, row, fill)
                else:
                    image.setPixelColor(col, row, empty)
        return image

    def sprite(
        self,
        grid_w: int,
        grid_h: int,
        shell,
        fill,
        empty,
        inset: float = 1.2,
        fill_fraction: float = FILL_FRACTION,
        aspect: float = EGG_ASPECT,
    ) -> QImage:
        """Rasterise the egg at an explicit size, independent of the widget.

        Exists so the app icon does not have to reach into a private method:
        it needs an exact pixel grid rather than whatever the widget geometry
        happens to be, and a slightly rounder proportion than the in-app egg to
        survive downscaling.
        """
        return self._rasterise(grid_w, grid_h, shell, fill, empty, inset, fill_fraction, aspect)

    # -- painting -------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        del event
        painter = QPainter(self)
        self.paint_into(painter)
        painter.end()

    def paint_into(self, painter: QPainter, x: int = 0, y: int = 0) -> None:
        """Draw the egg at (x, y); used by paintEvent and the debug sheet."""
        palette = self.palette()
        shell = palette.color(QPalette.ColorRole.WindowText)
        empty = palette.color(QPalette.ColorRole.Window)
        fill = shell.lighter(215) if empty.lightness() < 128 else shell.darker(180)

        grid_w, grid_h = self._grid()
        image = self._rasterise(grid_w, grid_h, shell, fill, empty)
        cell = self._cell_size()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(QRect(x, y, self.width(), self.height()), empty)
        target = QRect(x, y, grid_w * cell, grid_h * cell)
        painter.drawImage(target, image, QRect(0, 0, grid_w, grid_h))


def debug_sheet(path: str, steps: tuple[float, ...] | None = None) -> None:
    """Render a contact sheet of the egg at several fill levels (dev helper)."""
    from eggnoxx import theme

    app = QApplication.instance() or QApplication([])
    # Start from the resolved default palette, otherwise unset roles fall back to
    # the light theme and the sheet comes out white-on-white.
    dark_palette = QPalette(app.palette())
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        dark_palette.setColor(group, QPalette.ColorRole.Window, theme.BLACK)
        dark_palette.setColor(group, QPalette.ColorRole.WindowText, theme.WHITE)
    app.setPalette(dark_palette)

    levels = steps if steps is not None else (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    cell_w, cell_h = 150, 220
    sheet = QImage(cell_w * len(levels), cell_h, QImage.Format_RGB32)
    sheet.fill(QColor(0, 0, 0))
    painter = QPainter(sheet)
    for index, level in enumerate(levels):
        egg = EggWidget()
        egg.resize(cell_w, cell_h)
        egg.set_progress(level)
        # Paint straight into the sheet: no window or stylesheet involved, so
        # what shows up here is exactly what paintEvent draws on screen.
        egg.paint_into(painter, index * cell_w, 0)
    painter.end()
    sheet.save(path)
