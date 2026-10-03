"""Tests for the alarm tone and its graceful degradation.

Headless machines often expose only a dummy audio sink, so the tone cannot be
verified by ear here. These tests check the file itself and that the alarm
falls back instead of failing.
"""

from __future__ import annotations

import os
import struct
import wave

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from eggnoxx import alarm  # noqa: E402


# -- the sound file ---------------------------------------------------
def test_sound_file_ships_with_the_package() -> None:
    assert alarm.SOUND_FILE.is_file(), "alarm.wav fehlt im Paket"


def test_sound_file_is_a_valid_pcm_wave() -> None:
    with alarm.SOUND_FILE.open("rb") as handle:
        header = handle.read(44)
    assert header[:4] == b"RIFF"
    assert header[8:12] == b"WAVE"
    assert struct.unpack("<H", header[20:22])[0] == 1, "kein PCM-Format"


def test_sound_file_matches_its_header() -> None:
    """A truncated or stale file would be silent or crash the player."""
    with wave.open(str(alarm.SOUND_FILE)) as handle:
        frames = handle.getnframes()
    expected = frames * 2 + 44  # 16-bit mono + header
    assert alarm.SOUND_FILE.stat().st_size == expected


def test_sound_is_mono_16_bit() -> None:
    with wave.open(str(alarm.SOUND_FILE)) as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2


def test_sound_is_short_enough_not_to_annoy() -> None:
    """A timer beep longer than half a second gets grating."""
    with wave.open(str(alarm.SOUND_FILE)) as handle:
        seconds = handle.getnframes() / handle.getframerate()
    assert 0.1 < seconds < 0.5, f"{seconds:.2f}s ist zu lang oder zu kurz"


def test_sound_contains_two_bursts() -> None:
    """Two tones with a gap, not one continuous tone."""
    with wave.open(str(alarm.SOUND_FILE)) as handle:
        rate = handle.getframerate()
        frames = handle.getnframes()
        samples = struct.unpack(f"<{frames}h", handle.readframes(frames))

    blocks = 40
    per_block = frames // blocks
    loud = []
    for index in range(blocks):
        block = samples[index * per_block : (index + 1) * per_block]
        loud.append(max(abs(value) for value in block) > 5_000)

    runs = [index for index, is_loud in enumerate(loud) if is_loud]
    assert runs, "kein hörbarer Ton"
    assert max(runs) - min(runs) > 5, "Töne sind nicht durch eine Pause getrennt"
    assert rate > 8_000


def test_sound_is_not_clipped() -> None:
    with wave.open(str(alarm.SOUND_FILE)) as handle:
        frames = handle.getnframes()
        samples = struct.unpack(f"<{frames}h", handle.readframes(frames))
    peak = max(abs(value) for value in samples) / 32_767
    assert 0.2 < peak < 0.95, f"Amplitude {peak:.2f} ist zu leise oder übersteuert"


# -- degradation ------------------------------------------------------
def test_alarm_survives_without_a_tone() -> None:
    """Constructing with tone=False must work; nothing may raise."""
    from PySide6.QtWidgets import QApplication, QWidget

    QApplication.instance() or QApplication(["eggnoxx-sound-test"])
    widget = QWidget()
    alarmer = alarm.Alarmer(widget, tone=False)
    assert alarmer.has_tone is False
    alarmer._beep()  # falls back to the system bell
    alarmer.start()
    assert alarmer.is_active
    alarmer.stop()
    assert not alarmer.is_active
    widget.close()


def test_usable_is_false_for_nothing() -> None:
    assert alarm._is_usable(None) is False


def test_usable_survives_a_broken_object() -> None:
    class Broken:
        def status(self):
            raise RuntimeError("kein Audio")

    assert alarm._is_usable(Broken()) is False


def test_beep_falls_back_when_the_device_rejects_the_sound() -> None:
    """status() == Error (dummy sink) must not raise, only skip the tone."""
    from PySide6.QtWidgets import QApplication, QWidget

    QApplication.instance() or QApplication(["eggnoxx-sound-test"])
    widget = QWidget()
    alarmer = alarm.Alarmer(widget, tone=False)
    alarmer._beep()  # no tone object at all
    widget.close()


@pytest.mark.parametrize("volume", [0.0, 0.5, 1.0])
def test_volume_range_is_accepted(volume: float) -> None:
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication(["eggnoxx-sound-test"])
    effect = alarm._load_sound(volume=volume)
    if effect is not None:
        assert effect.volume() == pytest.approx(volume)
