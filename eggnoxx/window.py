"""Main window: countdown display, presets, free timer and the alarm."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from eggnoxx import theme
from eggnoxx.alarm import Alarmer
from eggnoxx.core import PRESETS, TICK_INTERVAL_MS, Countdown, State, clamp_duration
from eggnoxx.egg import EggWidget

HINTS = "Leertaste Start/Pause · R Reset · 1-3 Presets · Esc Beenden"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EggNoxx")
        self.setMinimumSize(430, 620)

        self.timer = Countdown(PRESETS[0].seconds)
        self.egg = EggWidget()
        self.alarmer = Alarmer(self)

        self.time_label = self._build_time_label()
        self.status_label = self._build_status_label()
        self.preset_buttons = self._build_presets()
        self.minutes_box, self.seconds_box = self._build_free_input()
        self.start_button = self._build_start_button()
        self.reset_button = self._build_reset_button()
        self.alarm_button = self._build_alarm_button()

        self._build_ui()
        self._build_shortcuts()

        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(TICK_INTERVAL_MS)
        self.tick_timer.timeout.connect(self._on_tick)

        self._refresh()

    # -- construction ---------------------------------------------------
    @staticmethod
    def _flat_button(text: str) -> QPushButton:
        button = QPushButton(text)
        # Space belongs to the window shortcut, never to a focused button.
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def _build_time_label(self) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(theme.mono_font(76, QFont.Weight.Medium))
        return label

    def _build_status_label(self) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("muted")
        label.setFont(theme.ui_font(12))
        return label

    def _build_presets(self) -> list[QPushButton]:
        buttons = []
        for index, preset in enumerate(PRESETS, start=1):
            button = self._flat_button(f"{preset.label}  {preset.display}")
            button.setToolTip(f"Kurzbefehl: {index}")
            button.clicked.connect(lambda _=False, p=preset: self._select_preset(p))
            buttons.append(button)
        return buttons

    def _build_free_input(self) -> tuple[QSpinBox, QSpinBox]:
        boxes = []
        for maximum in (99, 59):
            box = QSpinBox()
            box.setRange(0, maximum)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setFont(theme.mono_font(15))
            box.valueChanged.connect(self._on_free_input)
            boxes.append(box)
        return boxes[0], boxes[1]

    def _build_start_button(self) -> QPushButton:
        button = self._flat_button("Start")
        button.clicked.connect(self._toggle)
        return button

    def _build_reset_button(self) -> QPushButton:
        button = self._flat_button("Reset")
        button.clicked.connect(self._reset)
        return button

    def _build_alarm_button(self) -> QPushButton:
        button = self._flat_button("Zeit ist um")
        button.setObjectName("alarmButton")
        button.clicked.connect(self._acknowledge)
        button.hide()
        return button

    def _rule(self) -> QFrame:
        line = QFrame()
        line.setObjectName("rule")
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(26, 20, 26, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("E G G N O X X")
        title.setObjectName("title")
        pin = QCheckBox("Immer oben")
        pin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pin.toggled.connect(self._set_always_on_top)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(pin)
        layout.addLayout(header)
        layout.addWidget(self._rule())

        layout.addStretch(1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        self.egg.setMaximumHeight(240)
        layout.addWidget(self.egg, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

        layout.addWidget(self._rule())

        presets_row = QHBoxLayout()
        for button in self.preset_buttons:
            presets_row.addWidget(button)
        layout.addLayout(presets_row)

        free_row = QHBoxLayout()
        free_row.addStretch(1)
        for text, box in (("Min", self.minutes_box), ("Sek", self.seconds_box)):
            caption = QLabel(text)
            caption.setObjectName("muted")
            caption.setFont(theme.ui_font(12))
            free_row.addWidget(caption)
            free_row.addWidget(box)
        apply_button = self._flat_button("Setzen")
        apply_button.clicked.connect(self._apply_free_input)
        free_row.addWidget(apply_button)
        free_row.addStretch(1)
        layout.addLayout(free_row)

        actions = QHBoxLayout()
        actions.addWidget(self.start_button, 3)
        actions.addWidget(self.reset_button, 1)
        layout.addLayout(actions)
        layout.addWidget(self.alarm_button)

        hints = QLabel(HINTS)
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hints.setObjectName("muted")
        hints.setFont(theme.ui_font(10))
        layout.addWidget(hints)

        self.setCentralWidget(central)

    def _build_shortcuts(self) -> None:
        def bind(sequence: str, slot) -> None:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(slot)

        bind("Space", self._toggle)
        bind("R", self._reset)
        bind("Esc", self.close)
        bind("Alt+T", lambda: self._toggle_pin_shortcut())
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
        self._refresh()

    def _on_free_input(self) -> None:
        """Live-update the timer while typing, but never interrupt a run."""
        if self.timer.state in (State.IDLE, State.DONE):
            seconds = clamp_duration(self.minutes_box.value(), self.seconds_box.value())
            self._select_duration(seconds)
            self._refresh()

    def _apply_free_input(self) -> None:
        self._select_duration(clamp_duration(self.minutes_box.value(), self.seconds_box.value()))
        self._refresh()

    def _select_duration(self, seconds: int) -> None:
        self.alarmer.stop()
        self.timer.set_duration(seconds)

    def _set_always_on_top(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()

    def _toggle_pin_shortcut(self) -> None:
        box = self.findChild(QCheckBox)
        if box is not None:
            box.toggle()

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
        self.start_button.setText("Pause" if self.timer.is_running else "Start")
        self.alarm_button.setVisible(self.timer.state is State.DONE)
        self.status_label.setText(
            {
                State.IDLE: "BEREIT",
                State.RUNNING: "LÄUFT",
                State.PAUSED: "PAUSIERT",
                State.DONE: "FERTIG",
            }[self.timer.state]
        )
        running = self.timer.is_running
        for button in self.preset_buttons:
            button.setEnabled(not running)
        for box in (self.minutes_box, self.seconds_box):
            box.setEnabled(not running)

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
    app.setStyleSheet(theme.stylesheet())

    window = MainWindow()
    window.show()
    return app.exec()
