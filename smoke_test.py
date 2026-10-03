"""Headless GUI smoke test.

Runs the real window on the offscreen platform: starts a timer, lets it run out,
confirms the alarm kicks in, acknowledges it, and renders both states to PNG so
the layout can be eyeballed without a desktop session.

    python smoke_test.py            # offscreen, writes screenshots to .artifacts/
    python smoke_test.py --visible  # show the window for real
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

if "--visible" not in sys.argv:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtCore import QEventLoop, QPoint, QRect, Qt, QTimer  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QCheckBox, QWidget  # noqa: E402

from eggnoxx import theme  # noqa: E402
from eggnoxx.core import PRESETS  # noqa: E402
from eggnoxx.window import MainWindow  # noqa: E402

ARTIFACTS = Path(__file__).parent / ".artifacts"
failures: list[str] = []


def check(label: str, condition: bool) -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(label)


def pump(ms: int) -> None:
    """Spin the event loop for ``ms`` milliseconds."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def overflowing_widgets(window: MainWindow) -> list[str]:
    """Names of children that stick out of the central widget's rect."""
    central = window.centralWidget()
    bounds = central.rect()
    offenders = []
    for child in central.findChildren(QWidget):
        if not child.isVisible():
            continue
        inner = QRect(child.mapTo(central, QPoint(0, 0)), child.size())
        if not bounds.contains(inner):
            offenders.append(f"{child.objectName() or type(child).__name__} {child.geometry()}")
    return offenders


def main() -> int:
    ARTIFACTS.mkdir(exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow()
    window.timer.set_duration(2)
    window.resize(430, 620)
    window.show()

    print("layout")
    pump(200)
    check("kein Ueberlauf im Ausgangszustand", not overflowing_widgets(window))

    print("start / pause / reset")
    window._toggle()
    check("laeuft nach Start", window.timer.is_running)
    check("Start-Button zeigt PAUSE", window.start_button.text() == "PAUSE")
    pump(600)
    check("Zeit laeuft ab", window.timer.remaining < 2.0)
    check("Ei fuellt sich", 0.0 < window.egg.progress < 1.0)
    window._toggle()
    frozen = window.timer.remaining
    pump(400)
    check("Pause friert die Zeit ein", window.timer.remaining == frozen)
    window._reset()
    check("Reset -> IDLE mit voller Zeit", window.timer.remaining == 2.0)

    print("ablauf + alarm")
    window._toggle()
    pump(2300)  # 2s timer + margin for the tick that flips it to DONE
    check("Zustand DONE", window.timer.state.name == "DONE")
    check("Anzeige 0:00", window.time_label.text() == "0:00")
    check("Alarm-Button sichtbar", window.alarm_button.isVisible())
    check("Signalton aktiv", window.alarmer.is_active)
    pump(100)
    check("kein Ueberlauf mit Alarm-Button", not overflowing_widgets(window))
    window.grab().save(str(ARTIFACTS / "alarm.png"))
    window.alarmer._blink_on = False  # force the dark half of the blink
    window.alarmer._apply_blink()
    window.grab().save(str(ARTIFACTS / "alarm_dark.png"))
    window.alarmer._blink_on = True
    window.alarmer._apply_blink()

    print("quittieren")
    window._acknowledge()
    check("Alarm gestoppt", not window.alarmer.is_active)
    check("zurueck auf IDLE", window.timer.state.name == "IDLE")
    check("Dauer bleibt erhalten", window.timer.total == 2)

    print("presets + freie eingabe")
    window._select_preset(PRESETS[2])
    check("Hart geladen", window.timer.total == 540 and window.time_label.text() == "9:00")
    window.minutes_box.setValue(3)
    window.seconds_box.setValue(15)
    window._apply_free_input()
    check("freie Zeit 3:15", window.timer.display == "3:15")

    print("ausrichtung")
    tops = {
        name: widget.geometry().top()
        for name, widget in (
            ("MIN", window.minutes_box),
            ("SEK", window.seconds_box),
            ("SETZEN", window.set_button),
        )
    }
    check("Min/Sek/Setzen auf gleicher Hoehe", len(set(tops.values())) == 1)
    heights = {
        name: widget.geometry().height()
        for name, widget in (
            ("MIN", window.minutes_box),
            ("SEK", window.seconds_box),
            ("SETZEN", window.set_button),
        )
    }
    check("Min/Sek/Setzen gleich hoch", len(set(heights.values())) == 1)

    print("immer oben")
    box = window.findChild(QCheckBox)
    box.setChecked(True)
    pump(50)
    check(
        "WindowStaysOnTopHint gesetzt",
        bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint),
    )
    box.setChecked(False)
    pump(50)

    print("tastatur")
    window._select_preset(PRESETS[0])
    QTest.keyClick(window, Qt.Key.Key_3)
    pump(50)
    check("Taste 3 laedt Preset Hart", window.timer.total == 540)
    QTest.keyClick(window, Qt.Key.Key_Space)
    pump(50)
    check("Leertaste startet", window.timer.is_running)
    QTest.keyClick(window, Qt.Key.Key_Space)
    pump(50)
    check("Leertaste pausiert", window.timer.state.name == "PAUSED")
    QTest.keyClick(window, Qt.Key.Key_R)
    pump(50)
    check("Taste R resettet", window.timer.state.name == "IDLE")

    window._select_preset(PRESETS[0])
    window.resize(430, 620)
    pump(300)
    window.grab().save(str(ARTIFACTS / "idle.png"))

    print(f"\nScreenshots: {ARTIFACTS}/idle.png, {ARTIFACTS}/alarm.png")
    print("Esc schliesst das Fenster")
    QTest.keyClick(window, Qt.Key.Key_Escape)
    pump(50)
    check("Fenster zu", not window.isVisible())
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED")
        return 1
    print("Alle Checks bestanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
