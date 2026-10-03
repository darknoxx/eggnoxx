"""Erzeugt den Alarmton als WAV-Datei.

Bewusst ohne fremde Bibliothek: `wave` und `math` aus der Standardbibliothek
reichen, das Ergebnis ist damit reproduzierbar und ohne Download nachvollziehbar.

    python tools/make_sound.py

Zwei kurze Töne statt eines langen Sirenentons - ein Timer soll nicht nerven.
Kurze Ein- und Ausblendungen, damit der Ton nicht klickt.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44_100
TONE_HZ = 1_180  # klar, aber nicht schrill
TONE_SECONDS = 0.12
GAP_SECONDS = 0.06
PEAK = 0.55  # von voller Aussteuerung, damit es nicht erschreckt
ATTACK = 0.008
RELEASE = 0.022

OUTPUT = Path(__file__).resolve().parent.parent / "eggnoxx" / "assets" / "sounds" / "alarm.wav"


def _envelope(position: float, total: float) -> float:
    """Rampe hoch und runter, damit Start und Ende nicht klicken."""
    if position < ATTACK:
        return position / ATTACK
    if position > total - RELEASE:
        return max(0.0, (total - position) / RELEASE)
    return 1.0


def _tone(frequency: float, seconds: float) -> list[int]:
    """Ein einzelner Sinuston als 16-Bit-PCM-Werte."""
    count = int(SAMPLE_RATE * seconds)
    step = 2 * math.pi * frequency / SAMPLE_RATE
    samples = []
    for index in range(count):
        envelope = _envelope(index / SAMPLE_RATE, seconds)
        value = math.sin(step * index) * envelope * PEAK
        samples.append(int(max(-1.0, min(1.0, value)) * 32_767))
    return samples


def build_signal() -> list[int]:
    """Zwei Töne mit kurzer Pause dazwischen."""
    samples: list[int] = []
    samples += _tone(TONE_HZ, TONE_SECONDS)
    samples += [0] * int(SAMPLE_RATE * GAP_SECONDS)
    samples += _tone(TONE_HZ, TONE_SECONDS)
    return samples


def write_wav(path: Path = OUTPUT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = build_signal()
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return path


if __name__ == "__main__":
    written = write_wav()
    size_kb = written.stat().st_size / 1024
    print(f"geschrieben: {written} ({size_kb:.1f} KB)")
