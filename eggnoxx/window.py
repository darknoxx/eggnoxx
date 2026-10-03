"""Main window: countdown display, presets, free timer and the alarm."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from eggnoxx import theme
from eggnoxx.alarm import Alarmer
from eggnoxx.core import (
    BOILING_WATER_HINT,
    COLD_WATER_HINT,
    PRESETS,
    TICK_INTERVAL_MS,
    Countdown,
    Preset,
    State,
    clamp_duration,
)
from eggnoxx.egg import EggWidget
from eggnoxx.panel import Panel, separator

HINTS = "LEERTASTE START/PAUSE   R RESET   1-3 PRESETS   ESC BEENDEN"
BUTTON_HEIGHT = 40
EGG_COLUMN_WIDTH = 190
EGG_COLUMN_HEIGHT = 250


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EggNoxx")
        self.setMinimumSize(460, 660)

        self.timer = Countdown(PRESETS[0].seconds)
        self._active_preset: Preset | None = PRESETS[0]
        self.egg = EggWidget()
        self.alarmer = Alarmer(self)

        self.time_label = self._build_time_label()
        self.status_label = self._build_status_label()
        self.preset_hint = self._build_preset_hint()
        self.preset_buttons = self._build_presets()
        self.minutes_box, self.seconds_box = self._build_free_input()
        self.start_button = self._build_button("START", self._toggle)
        self.reset_button = self._build_button("RESET", self._reset)
        self.set_button = self._build_button("SETZEN", self._apply_free_input)
        self.alarm_button = self._build_button("ZEIT IST UM", self._acknowledge)

        self._build_ui()
        self._build_shortcuts()

        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(TICK_INTERVAL_MS)
        self.tick_timer.timeout.connect(self._on_tick)

        self._refresh()

    # -- construction ---------------------------------------------------
    @staticmethod
    def _build_button(text: str, slot=None) -> QPushButton:
        button = QPushButton(text)
        # Space belongs to the window shortcut, never to a focused button.
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setFixedHeight(BUTTON_HEIGHT)
        button.setFont(theme.pixel(14, bold=True))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if slot is not None:
            button.clicked.connect(slot)
        return button

    def _build_time_label(self) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(theme.pixel(72, bold=True))
        label.setMinimumHeight(84)
        return label

    def _build_status_label(self) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(theme.pixel(12))
        return label

    def _build_preset_hint(self) -> QLabel:
        """Describes the selected preset and when the countdown starts.

        The classic German cooking times count from lowering the egg into
        boiling water. Saying so matters: started from cold water the same
        numbers are roughly three minutes short.
        """
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(theme.pixel(10))
        label.setStyleSheet(f"color: {theme.DIM.name()};")
        label.setWordWrap(True)
        return label

    def _build_presets(self) -> list[QPushButton]:
        buttons = []
        for index, preset in enumerate(PRESETS, start=1):
            button = self._build_button(f"{preset.label.upper()} {preset.display}", None)
            button.setToolTip(
                f"{preset.label}: {preset.note}\n"
                f"{BOILING_WATER_HINT}\n{COLD_WATER_HINT}\nKurzbefehl {index}"
            )
            button.clicked.connect(lambda _=False, p=preset: self._select_preset(p))
            buttons.append(button)
        return buttons

    def _build_free_input(self) -> tuple[QSpinBox, QSpinBox]:
        boxes = []
        for maximum in (99, 59):
            box = QSpinBox()
            box.setRange(0, maximum)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setFont(theme.pixel(15))
            box.setFixedHeight(BUTTON_HEIGHT)
            box.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            box.valueChanged.connect(self._on_free_input)
            boxes.append(box)
        return boxes[0], boxes[1]

    # -- layout ---------------------------------------------------------
    def _build_ui(self) -> None:
        panel = Panel()
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(12)
        layout.addWidget(self._build_header())
        layout.addWidget(separator(panel))
        layout.addSpacing(4)

        layout.addStretch(1)
        layout.addWidget(self.time_label)
        layout.addSpacing(2)
        layout.addWidget(self.status_label)
        layout.addSpacing(10)
        layout.addWidget(self._build_egg_row())
        layout.addSpacing(4)
        layout.addWidget(self.preset_hint)
        layout.addStretch(1)
        layout.addSpacing(6)

        layout.addWidget(separator(panel))
        layout.addWidget(self._build_presets_row())
        layout.addWidget(self._build_free_row())
        layout.addWidget(self._build_actions_row())
        layout.addWidget(self.alarm_button)

        hints = QLabel(HINTS)
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hints.setFont(theme.pixel(9))
        hints.setStyleSheet(f"color: {theme.DIM.name()};")
        layout.addSpacing(2)
        layout.addWidget(hints)

        self.setCentralWidget(panel)

    def _build_header(self) -> QWidget:
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)

        title = QLabel("EGGNOXX")
        title.setFont(theme.pixel(16, bold=True))
        pin = QCheckBox("IMMER OBEN")
        pin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pin.setFont(theme.pixel(10))
        pin.setCursor(Qt.CursorShape.PointingHandCursor)
        pin.toggled.connect(self._set_always_on_top)
        self.pin_box = pin

        row.addWidget(title)
        row.addStretch(1)
        row.addWidget(pin)
        return header

    def _build_presets_row(self) -> QWidget:
        row = QWidget()
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        for column, button in enumerate(self.preset_buttons):
            grid.addWidget(button, 0, column)
            grid.setColumnStretch(column, 1)
        return row

    def _build_egg_row(self) -> QWidget:
        """The egg on a fixed-size column so it stays tall and narrow.

        Left to expand freely the widget spans the whole window width, which
        collapses the pixel cells and turns the egg into a thin outline.
        """
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)
        row.addWidget(self.egg)
        row.addStretch(1)
        self.egg.setFixedSize(EGG_COLUMN_WIDTH, EGG_COLUMN_HEIGHT)
        return holder

    def _build_free_row(self) -> QWidget:
        """Caption, spinner, caption, spinner and SETZEN share one equal grid
        so the columns line up with the three preset buttons above."""
        row = QWidget()
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        caption_min = QLabel("MINUTEN")
        caption_sec = QLabel("SEKUNDEN")
        for caption in (caption_min, caption_sec):
            caption.setFont(theme.pixel(10))
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption.setStyleSheet(f"color: {theme.DIM.name()};")

        grid.addWidget(caption_min, 0, 0)
        grid.addWidget(self.minutes_box, 1, 0)
        grid.addWidget(caption_sec, 0, 1)
        grid.addWidget(self.seconds_box, 1, 1)
        # Row 1 only: spanning both rows made the button taller than the
        # spinners, and Qt centres it in the spanned area, so it sat higher.
        grid.addWidget(self.set_button, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        return row

    def _build_actions_row(self) -> QWidget:
        row = QWidget()
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.addWidget(self.start_button, 0, 0)
        grid.addWidget(self.reset_button, 0, 1)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        return row

    def _build_shortcuts(self) -> None:
        def bind(sequence: str, slot) -> None:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(slot)

        bind("Space", self._toggle)
        bind("R", self._reset)
        bind("Esc", self.close)
        bind("Alt+T", self._toggle_pin_shortcut)
        for index, preset in enumerate(PRESETS, start=1):
            bind(str(index), lambda p=preset: self._select_preset(p))

    # -- commands -------------------------------------------------------
    def _toggle(self) -> None:
        if self.timer.state is State.DONE:
            self._acknowledge()
        self.timer.toggle()
        if self.timer.is_running:
            self.tick_timer.start()
        else:
            self.tick_timer.stop()
        self._refresh()

    def _reset(self) -> None:
        self.tick_timer.stop()
        self.alarmer.stop()
        self.timer.reset()
        self._refresh()

    def _acknowledge(self) -> None:
        self.alarmer.stop()
        self.timer.acknowledge()
        self._refresh()

    def _select_preset(self, preset) -> None:
        self.tick_timer.stop()
        self.alarmer.stop()
        self.timer.set_duration(preset.seconds)
        self.minutes_box.blockSignals(True)
        self.seconds_box.blockSignals(True)
        self.minutes_box.setValue(preset.seconds // 60)
        self.seconds_box.setValue(preset.seconds % 60)
        self.minutes_box.blockSignals(False)
        self.seconds_box.blockSignals(False)
        self._active_preset = preset
        self._refresh()

    def _on_free_input(self) -> None:
        """Live-update while typing, but never interrupt a run."""
        if self.timer.state in (State.IDLE, State.DONE):
            self._apply_free_input()

    def _apply_free_input(self) -> None:
        if self.timer.state in (State.RUNNING, State.PAUSED):
            return
        self.alarmer.stop()
        self.timer.set_duration(clamp_duration(self.minutes_box.value(), self.seconds_box.value()))
        # A hand-typed time is no preset, so drop the preset description.
        self._active_preset = None
        self._refresh()

    def _hint_text(self) -> str:
        """Two short lines under the egg: the result and how to count."""
        result = self._active_preset.note if self._active_preset else "Freie Zeit"
        return f"{result}\n{BOILING_WATER_HINT}\n{COLD_WATER_HINT}"

    def _set_always_on_top(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()

    def _toggle_pin_shortcut(self) -> None:
        self.pin_box.toggle()

    # -- ticking --------------------------------------------------------
    def _on_tick(self) -> None:
        if self.timer.is_done:
            self.tick_timer.stop()
            self.timer.tick()
            self.alarmer.start()
        self._refresh()

    def _refresh(self) -> None:
        self.time_label.setText(self.timer.display)
        self.egg.set_progress(self.timer.progress)
        self.start_button.setText("PAUSE" if self.timer.is_running else "START")
        self.alarm_button.setVisible(self.timer.state is State.DONE)
        self.status_label.setText(
            {
                State.IDLE: "BEREIT",
                State.RUNNING: "LAEUFT",
                State.PAUSED: "PAUSIERT",
                State.DONE: "FERTIG",
            }[self.timer.state]
        )
        self.preset_hint.setText(self._hint_text())
        busy = self.timer.is_running or self.timer.state is State.PAUSED
        for button in (*self.preset_buttons, self.set_button):
            button.setEnabled(not busy)
        for box in (self.minutes_box, self.seconds_box):
            box.setEnabled(not busy)

    # -- window events --------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt naming
        self.tick_timer.stop()
        self.alarmer.stop()
        if self.timer.is_running:
            answer = QMessageBox.question(
                self,
                "Noch am Laufen",
                "Die Uhr läuft noch. Wirklich beenden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer is not QMessageBox.StandardButton.Yes:
                self.tick_timer.start()
                event.ignore()
                return
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("EggNoxx")
    app.setApplicationDisplayName("EggNoxx")
    theme.load_fonts()
    app.setStyleSheet(theme.stylesheet())

    window = MainWindow()
    window.show()
    return app.exec()
