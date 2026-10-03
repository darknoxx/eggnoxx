"""End-of-time signalling: an alarm tone plus an inverting blink."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QWidget

from eggnoxx.theme import BLACK, BLINK_MS, WHITE, stylesheet

SOUND_FILE = Path(__file__).parent / "assets" / "sounds" / "alarm.wav"
VOLUME = 0.7


def _load_sound(volume: float = VOLUME):
    """Return a ``QSoundEffect`` for the alarm tone, or None if audio is absent.

    QtMultimedia is an optional part of the PySide6 stack, so its absence must
    not be fatal. Loading is asynchronous - Qt6 starts it on ``setSource`` and
    reports the outcome through ``status()``, so there is no ``load()`` call.
    """
    try:
        from PySide6.QtMultimedia import QSoundEffect
    except ImportError:
        return None
    if not SOUND_FILE.is_file():
        return None
    try:
        # No explicit audio device: QSoundEffect routes through the system
        # mixer on its own.
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(str(SOUND_FILE)))
        effect.setVolume(volume)
    except Exception:  # noqa: BLE001 - a missing tone must not take the app down
        return None
    return effect


def _is_usable(effect) -> bool:
    """Whether the tone can actually play.

    The effect reports ``Error`` when the audio device rejects the format, which
    happens on dummy outputs such as a headless PipeWire sink.
    """
    if effect is None:
        return False
    try:
        from PySide6.QtMultimedia import QSoundEffect

        return effect.status() not in (QSoundEffect.Status.Error, QSoundEffect.Status.Null)
    except Exception:  # noqa: BLE001 - never let audio break the alarm
        return False


class Alarmer(QObject):
    """Plays a tone once per second and blinks the window until acknowledged.

    The blink swaps the application stylesheet (and the window palette the egg
    reads), so the entire window inverts rather than just the numbers.
    """

    def __init__(self, target: QWidget, tone: bool = True) -> None:
        super().__init__(target)
        self._target = target
        self._app = QApplication.instance()
        self._sound = _load_sound() if tone else None
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

    @property
    def has_tone(self) -> bool:
        """Whether the WAV is in use; False means the system bell takes over."""
        return _is_usable(self._sound)

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
        """Play the alarm tone, falling back to the system bell."""
        if self.has_tone:
            try:
                if self._sound.isPlaying():
                    self._sound.stop()
                self._sound.play()
                return
            except Exception:  # noqa: BLE001 - audio must never break the alarm
                pass
        QApplication.beep()

    def _toggle_blink(self) -> None:
        self._blink_on = not self._blink_on
        self._apply_blink()

    def _apply_blink(self) -> None:
        dark = not self._blink_on
        if self._app is not None:
            self._app.setStyleSheet(stylesheet(dark=dark))

        # Start from the resolved palette: roles left unset would fall back to
        # the light theme and only some widgets would invert.
        palette = QPalette(self._target.palette())
        window, text = (BLACK, WHITE) if dark else (WHITE, BLACK)
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            palette.setColor(group, QPalette.ColorRole.Window, window)
            palette.setColor(group, QPalette.ColorRole.WindowText, text)
            palette.setColor(group, QPalette.ColorRole.Base, window)
            palette.setColor(group, QPalette.ColorRole.Text, text)
            palette.setColor(group, QPalette.ColorRole.Button, window)
            palette.setColor(group, QPalette.ColorRole.ButtonText, text)
        self._target.setPalette(palette)
        self._target.style().unpolish(self._target)
        self._target.style().polish(self._target)
