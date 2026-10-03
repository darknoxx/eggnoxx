"""Timer logic without any Qt dependency.

Kept deliberately free of GUI imports so it can be unit tested directly.
All timing is derived from a single :func:`time.monotonic` deadline instead of
accumulating tick intervals, so the countdown never drifts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto

TICK_INTERVAL_MS = 100  # ~10 redraws per second is plenty for a countdown


class State(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    DONE = auto()


@dataclass(frozen=True)
class Preset:
    """A named cooking time offered as a one-click button."""

    key: str
    label: str
    seconds: int

    @property
    def display(self) -> str:
        return format_mmss(self.seconds)


PRESETS: tuple[Preset, ...] = (
    Preset(key="weich", label="Weich", seconds=6 * 60 + 30),
    Preset(key="wachtel", label="Wachtel", seconds=7 * 60),
    Preset(key="hart", label="Hart", seconds=9 * 60),
)

PRESETS_BY_KEY = {preset.key: preset for preset in PRESETS}


def format_mmss(seconds: float) -> str:
    """Format a duration as ``M:SS`` (or ``H:MM:SS`` past an hour)."""
    total = max(0, int(round(seconds)))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def clamp_duration(minutes: int, secs: int) -> int:
    """Combine minute/second inputs into a sane, positive duration."""
    return max(1, minutes * 60 + secs)


class Countdown:
    """Monotonic countdown that can be started, paused, reset and queried."""

    def __init__(self, seconds: int, clock: callable = time.monotonic) -> None:
        self._clock = clock
        self._total = max(1, int(seconds))
        self._remaining = float(self._total)
        self._deadline = 0.0
        self._state = State.IDLE

    # -- properties -----------------------------------------------------
    @property
    def state(self) -> State:
        return self._state

    @property
    def total(self) -> int:
        """Configured duration in seconds."""
        return self._total

    @property
    def remaining(self) -> float:
        """Seconds left, always fresh even between ticks."""
        if self._state is State.RUNNING:
            self._remaining = max(0.0, self._deadline - self._clock())
        return self._remaining

    @property
    def is_running(self) -> bool:
        return self._state is State.RUNNING

    @property
    def is_done(self) -> bool:
        return self.remaining <= 0.0

    @property
    def progress(self) -> float:
        """Fraction of the duration already elapsed, clamped to 0.0..1.0."""
        if self._total <= 0:
            return 1.0
        return min(1.0, max(0.0, 1.0 - self.remaining / self._total))

    @property
    def display(self) -> str:
        return format_mmss(self.remaining)

    # -- commands -------------------------------------------------------
    def set_duration(self, seconds: int) -> None:
        """Load a new duration and go back to IDLE."""
        self._total = max(1, int(seconds))
        self._remaining = float(self._total)
        self._state = State.IDLE

    def start(self) -> None:
        """(Re)start from the remaining time; a finished timer restarts fully."""
        if self._state is State.DONE or self._remaining <= 0.0:
            self._remaining = float(self._total)
        self._deadline = self._clock() + self._remaining
        self._state = State.RUNNING

    def pause(self) -> None:
        if self._state is State.RUNNING:
            self._remaining = max(0.0, self._deadline - self._clock())
            self._state = State.PAUSED if self._remaining > 0 else State.DONE

    def toggle(self) -> None:
        """Space-bar behaviour: run/pause, or start fresh once finished."""
        if self._state is State.RUNNING:
            self.pause()
        else:
            self.start()

    def reset(self) -> None:
        self._remaining = float(self._total)
        self._state = State.IDLE

    def acknowledge(self) -> None:
        """Dismiss the finished state, keeping the duration for a re-run."""
        if self._state is State.DONE:
            self._remaining = float(self._total)
            self._state = State.IDLE

    def tick(self) -> bool:
        """Advance internal state; return ``True`` once the time is up."""
        if self._state is not State.RUNNING:
            return self._state is State.DONE
        # Read the live property: ``_remaining`` may be stale since the last tick.
        if self.remaining <= 0.0:
            self._remaining = 0.0
            self._state = State.DONE
            return True
        return False
