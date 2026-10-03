"""Generates the app icon as pixel art, derived from the same egg as the UI.

Run as a module to (re)write every size into the bundled icon directory:

    python -m eggnoxx.icon
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter

from eggnoxx.egg import EggWidget, fill_height

# Sizes a Linux desktop may ask for; keeping the set complete avoids blurry
# scaling in the dock, the launcher and the window list.
ICON_SIZES = (16, 22, 24, 32, 48, 64, 128, 256)

# The art is authored on a 16x16 logical grid and scaled up with
# nearest-neighbour sampling, so every icon stays genuinely pixel art.
ART_GRID = 16
FILL_PROGRESS = 1.0  # solid silhouette; a part-filled egg reads as a blob
INK = QColor("#ffffff")
FILL = QColor("#c8c8c8")
PAPER = QColor("#000000")

_app = None


def _ensure_app() -> None:
    """Rasterising needs a QGuiApplication; offscreen is fine for a file."""
    global _app
    if _app is None:
        from PySide6.QtWidgets import QApplication

        _app = QApplication.instance() or QApplication(["eggnoxx-icon"])


def render_icon(cells: int = ART_GRID, progress: float = FILL_PROGRESS) -> QImage:
    """Return the icon on a square transparent canvas of ``cells`` pixels.

    The egg is rasterised straight onto a transparent background rather than via
    the widget, because ``paint_into`` fills its background opaquely and that
    would square off the rounded plate corners.
    """
    _ensure_app()
    image = QImage(cells, cells, QImage.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    egg = EggWidget()
    egg.set_progress(progress)

    painter = QPainter(image)
    # Antialiasing only for the plate: with it off, the rounded corners come out
    # filled solid black instead of transparent.
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QColor("#5a5a5a"))
    painter.setBrush(PAPER)
    painter.drawRoundedRect(QRect(0, 0, cells - 1, cells - 1), 2, 2)

    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    # A solid silhouette, not an outlined one: at 16px a 1px shell breaks up into
    # speckle and the egg stops being recognisable. Progress is 1.0 so the shape
    # is complete rather than half-filled.
    transparent = QColor(0, 0, 0, 0)
    sprite = egg.sprite(
        cells,
        cells,
        INK,
        INK,
        transparent,
        inset=0.0,
        fill_fraction=0.7,
        aspect=1.34,
    )
    # Inset the egg inside the plate so it does not touch the border.
    margin = max(1, round(cells * 0.1))
    painter.drawImage(QRect(margin, margin, cells - 2 * margin, cells - 2 * margin), sprite)
    painter.end()
    return image


# Art is drawn on a coarse grid and scaled up with nearest-neighbour sampling,
# so every icon is genuinely pixel art rather than a smooth vector shape.
GRID_FOR_SIZE = {16: 16, 22: 11, 24: 12, 32: 16, 48: 16, 64: 16, 128: 32, 256: 64}


def write_icons(directory: Path, sizes: tuple[int, ...] = ICON_SIZES) -> list[Path]:
    """Write one PNG per size; returns the paths written."""
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for size in sizes:
        cells = GRID_FOR_SIZE.get(size, max(8, size // 4))
        icon = render_icon(cells=cells).scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        path = directory / f"{size}x{size}.png"
        icon.save(str(path))
        written.append(path)
    (directory / "eggnoxx.svg").write_text(_svg(), encoding="utf-8")
    written.append(directory / "eggnoxx.svg")
    return written


def _svg() -> str:
    """A crisp vector version for high-DPI and scalable contexts.

    Drawn from the same width profile as the raster icon, as an outline stroke
    rather than a filled outline: the stroke keeps the shape identical at every
    size without needing an even-odd trick for the hole.
    """
    from eggnoxx.egg import egg_profile

    left, right = 3.5, 12.5
    bottom, top = 13.5, 2.5
    half_span = (right - left) / 2

    right_side, left_side = [], []
    steps = 40
    for step in range(steps + 1):
        u = step / steps
        y = bottom - u * (bottom - top)
        half = egg_profile(u) * half_span
        if half <= 0.0:
            continue
        right_side.append(f"{right - half + 0.5:.2f} {y:.2f}")
        left_side.append(f"{left + half - 0.5:.2f} {y:.2f}")

    outline = " ".join(right_side + left_side[::-1])
    fill_top = bottom - fill_height(FILL_PROGRESS) * (bottom - top)

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" '
        'shape-rendering="crispEdges">'
        '<rect width="16" height="16" rx="2" fill="#000000"/>'
        f'<polyline points="{outline}" fill="none" stroke="#ffffff" '
        'stroke-width="1" stroke-linejoin="round"/>'
        f'<rect x="{left + 0.4:.2f}" y="{fill_top:.2f}" '
        f'width="{right - left - 0.8:.2f}" height="{bottom - fill_top - 0.4:.2f}" '
        'fill="#c8c8c8"/>'
        "</svg>"
    )


def main() -> int:
    target = Path(__file__).parent / "assets" / "icons"
    for path in write_icons(target):
        print(f"  {path.relative_to(target.parent.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
