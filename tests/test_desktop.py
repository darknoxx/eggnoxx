"""Tests for the desktop entry, above all the ``Exec`` quoting.

The quoting is not cosmetic. The specification reserves the space character, so
an unquoted path containing one gets split into two arguments and the launcher
fails without an error message. ``desktop-file-validate`` does not catch that -
verified against a 1.16 installation - which is why it is pinned down here.

The reference implementation is a tokeniser following the "Exec key" rules of
the desktop entry specification. ``quote_exec`` has to survive a round trip
through it, which is a much stronger statement than "the string looks right".
"""

from __future__ import annotations

import pytest

from eggnoxx import desktop

# Characters the specification reserves inside a value. Backslash is handled on
# its own; these four only matter inside double quotes.
RESERVED = '"\\`$'


def parse_exec(value: str) -> list[str]:
    """Split an ``Exec`` value into arguments the way the specification says.

    Quote marks are removed, ``\\x`` is an escaped literal ``x``, and an
    unquoted run ends at the next reserved character.
    """
    arguments: list[str] = []
    current: list[str] = []
    quoted = False
    escaping = False
    for char in value:
        if escaping:
            current.append(char)
            escaping = False
        elif char == "\\":
            escaping = True
        elif char == '"':
            quoted = not quoted
        elif char == " " and not quoted:
            arguments.append("".join(current))
            current = []
        else:
            current.append(char)
    assert not escaping, "trailing backslash escapes nothing"
    assert not quoted, "unbalanced quote"
    arguments.append("".join(current))
    return arguments


# Paths that have to survive the round trip. All of these occur in real
# checkouts or are reserved characters the spec lists explicitly.
AWKWARD_PATHS = [
    "/home/user/EggNoxx/.venv/bin/python",
    "/home/user/My Project/.venv/bin/python",
    "/home/user/Meine Projekte/Egg N0xx/.venv/bin/python",
    '/home/user/say "hi"/.venv/bin/python',
    "/home/user/back\\slash/.venv/bin/python",
    "/home/user/tick`tock/.venv/bin/python",
    "/home/user/cost$money/.venv/bin/python",
    '/home/user/all of them "$\\` /.venv/bin/python',
]


@pytest.mark.parametrize("part", AWKWARD_PATHS)
def test_single_argument_round_trips(part: str) -> None:
    """A quoted argument must come back out of ``parse_exec`` unchanged."""
    assert parse_exec(desktop.quote_exec(part)) == [part]


@pytest.mark.parametrize("parts", [AWKWARD_PATHS, ["/tmp/plain", "-m", "eggnoxx"]])
def test_command_round_trips(parts: list[str]) -> None:
    """The joined Exec line must split back into exactly the given arguments."""
    line = " ".join(desktop.quote_exec(part) for part in parts)
    assert parse_exec(line) == parts


def test_space_would_break_without_quoting() -> None:
    """Guards the premise: the unquoted form really is ambiguous.

    Without this, the tests above would pass just as well if quoting were
    removed entirely, and the bug would come back unnoticed.
    """
    assert parse_exec("/home/user/My Project/python -m eggnoxx") != [
        "/home/user/My Project/python",
        "-m",
        "eggnoxx",
    ]


def test_desktop_contents_exec_is_quoted(monkeypatch: pytest.MonkeyPatch) -> None:
    """The generated entry must keep a spaced path in one piece."""
    parts = ["/home/user/My Project/.venv/bin/python", "-m", "eggnoxx"]
    monkeypatch.setattr(desktop, "launch_command", lambda: parts)
    exec_line = next(
        line for line in desktop.desktop_contents().splitlines() if line.startswith("Exec=")
    )
    assert parse_exec(exec_line.removeprefix("Exec=")) == parts


def test_desktop_contents_has_no_path_key() -> None:
    """``Path=`` used to point at the source checkout; it must stay gone."""
    assert "\nPath=" not in "\n" + desktop.desktop_contents()


def test_launch_command_is_usable() -> None:
    """The command must be absolute, or the entry breaks outside the checkout."""
    command = desktop.launch_command()
    assert command
    assert command[0].startswith("/")
    # Either the installed console script on its own, or interpreter plus module.
    assert command == [command[0]] or command[1:] == ["-m", desktop.APP_ID]
