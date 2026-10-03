"""Pure-logic tests for the countdown. No Qt, no display needed."""

from __future__ import annotations

import pytest

from eggnoxx.core import (
    BOILING_WATER_HINT,
    COLD_WATER_HINT,
    PRESETS,
    PRESETS_BY_KEY,
    Countdown,
    State,
    clamp_duration,
    format_mmss,
)


class FakeClock:
    """Manually advanced monotonic clock."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


# -- formatting --------------------------------------------------------
@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0:00"),
        (5, "0:05"),
        (65, "1:05"),
        (390, "6:30"),
        (599, "9:59"),
        (3600, "1:00:00"),
        (3725, "1:02:05"),
        (-10, "0:00"),
    ],
)
def test_format_mmss(seconds: float, expected: str) -> None:
    assert format_mmss(seconds) == expected


def test_clamp_duration_keeps_positive() -> None:
    assert clamp_duration(6, 30) == 390
    assert clamp_duration(0, 0) == 1
    assert clamp_duration(0, -5) == 1


# -- presets -----------------------------------------------------------
def test_presets_are_the_classic_egg_times() -> None:
    assert [preset.key for preset in PRESETS] == ["weich", "halbweich", "hart"]
    assert [preset.seconds for preset in PRESETS] == [390, 420, 540]
    assert PRESETS[0].display == "6:30"
    assert PRESETS_BY_KEY["hart"].label == "Hart"


def test_no_preset_is_called_wachtel() -> None:
    """ "Wachtel" means a quail egg; the middle stage is "halbweich"."""
    assert all("wachtel" not in preset.label.lower() for preset in PRESETS)
    assert all("wachtel" not in preset.key for preset in PRESETS)
    assert set(PRESETS_BY_KEY) == {"weich", "halbweich", "hart"}


def test_every_preset_describes_the_result() -> None:
    """A time alone does not say what the yolk should look like."""
    for preset in PRESETS:
        assert preset.note
    assert "fluessig" in PRESETS_BY_KEY["weich"].note
    assert "fest" in PRESETS_BY_KEY["hart"].note


def test_presets_are_ordered_from_soft_to_hard() -> None:
    times = [preset.seconds for preset in PRESETS]
    assert times == sorted(times)


def test_hints_name_the_counting_convention() -> None:
    assert "kochende" in BOILING_WATER_HINT
    assert "Kaltwasser" in COLD_WATER_HINT


# -- countdown ---------------------------------------------------------
def test_starts_idle_with_full_duration(clock: FakeClock) -> None:
    timer = Countdown(390, clock)
    assert timer.state is State.IDLE
    assert timer.remaining == 390
    assert timer.display == "6:30"
    assert timer.progress == 0.0


def test_running_counts_down(clock: FakeClock) -> None:
    timer = Countdown(390, clock)
    timer.start()
    clock.advance(90)
    assert timer.remaining == 300
    assert timer.display == "5:00"
    assert timer.progress == pytest.approx(90 / 390)


def test_pause_freezes_and_resume_continues(clock: FakeClock) -> None:
    timer = Countdown(390, clock)
    timer.start()
    clock.advance(60)
    timer.pause()
    clock.advance(500)  # time passes while paused
    assert timer.state is State.PAUSED
    assert timer.remaining == 330
    timer.start()
    clock.advance(30)
    assert timer.remaining == 300


def test_toggle_flips_between_running_and_paused(clock: FakeClock) -> None:
    timer = Countdown(60, clock)
    timer.toggle()
    assert timer.is_running
    timer.toggle()
    assert timer.state is State.PAUSED
    timer.toggle()
    assert timer.is_running


def test_reaching_zero_switches_to_done(clock: FakeClock) -> None:
    timer = Countdown(10, clock)
    timer.start()
    clock.advance(9.9)
    assert timer.tick() is False
    clock.advance(0.2)
    assert timer.tick() is True
    assert timer.state is State.DONE
    assert timer.remaining == 0.0
    assert timer.progress == 1.0
    assert timer.display == "0:00"


def test_finished_timer_restarts_from_the_beginning(clock: FakeClock) -> None:
    timer = Countdown(10, clock)
    timer.start()
    clock.advance(10)
    timer.tick()
    timer.start()
    assert timer.state is State.RUNNING
    assert timer.remaining == 10


def test_reset_restores_idle(clock: FakeClock) -> None:
    timer = Countdown(60, clock)
    timer.start()
    clock.advance(25)
    timer.reset()
    assert timer.state is State.IDLE
    assert timer.remaining == 60


def test_acknowledge_clears_done_but_keeps_duration(clock: FakeClock) -> None:
    timer = Countdown(45, clock)
    timer.start()
    clock.advance(45)
    timer.tick()
    timer.acknowledge()
    assert timer.state is State.IDLE
    assert timer.remaining == 45


def test_set_duration_resets_state(clock: FakeClock) -> None:
    timer = Countdown(60, clock)
    timer.start()
    clock.advance(30)
    timer.set_duration(540)
    assert timer.state is State.IDLE
    assert timer.total == 540
    assert timer.display == "9:00"


def test_ticking_while_idle_reports_not_done(clock: FakeClock) -> None:
    assert Countdown(30, clock).tick() is False


def test_countdown_does_not_drift(clock: FakeClock) -> None:
    """Ten ticks of 100 ms must equal exactly one second of remaining time."""
    timer = Countdown(100, clock)
    timer.start()
    for _ in range(10):
        clock.advance(0.1)
        timer.tick()
    assert timer.remaining == pytest.approx(99.0)
