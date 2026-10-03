"""Tests for the pure geometry behind the pixel-art egg (no Qt needed)."""

from __future__ import annotations

import pytest

from eggnoxx.egg import EGG_ASPECT, egg_profile, fill_height


def test_profile_is_zero_at_both_ends() -> None:
    assert egg_profile(0.0) == 0.0
    assert egg_profile(1.0) == 0.0
    assert egg_profile(-0.1) == 0.0
    assert egg_profile(1.1) == 0.0


def test_profile_is_positive_inside() -> None:
    for step in range(1, 100):
        assert egg_profile(step / 100) > 0.0


def test_widest_point_sits_below_the_middle() -> None:
    """That is what makes it read as an egg rather than a circle."""
    heights = [i / 200 for i in range(1, 200)]
    widest = max(heights, key=egg_profile)
    assert widest < 0.5


def test_top_is_narrower_than_the_bottom() -> None:
    """Compare equal distances above and below the centre."""
    below, above = egg_profile(0.35), egg_profile(0.65)
    assert below > above


def test_profile_stays_within_unit_range() -> None:
    for step in range(201):
        assert 0.0 <= egg_profile(step / 200) <= 1.05


@pytest.mark.parametrize(
    ("progress", "expected"),
    [(0.0, 0.0), (1.0, 1.0)],
)
def test_fill_height_endpoints(progress: float, expected: float) -> None:
    assert fill_height(progress) == pytest.approx(expected, abs=0.02)


def test_fill_height_is_monotonic() -> None:
    heights = [fill_height(p / 50) for p in range(51)]
    assert heights == sorted(heights)


def test_fill_height_stays_in_range() -> None:
    for step in range(101):
        assert 0.0 <= fill_height(step / 100) <= 1.0


def test_fill_height_is_clamped() -> None:
    assert fill_height(-5.0) == 0.0
    assert fill_height(5.0) == 1.0


def test_fill_height_tracks_area_not_height() -> None:
    """Half the time should fill noticeably less than half the height.

    The egg is wider at the bottom, so a straight height ramp would overstate
    how full it looks. This guards the volume mapping.
    """
    assert fill_height(0.5) < 0.5


def test_aspect_is_egg_like() -> None:
    assert 1.2 < EGG_ASPECT < 1.7
