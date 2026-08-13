import os
import sys

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - Windows fallback
    termios = None
    tty = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - Unix fallback
    msvcrt = None

from ui import visuals


def _map_key(
    char: str,
    seq: str = "",
    *,
    enable_left_right: bool = False,
    enable_tab: bool = False,
    enable_search: bool = False,
    enable_amongus: bool = False,
    separate_quit_back: bool = False,
) -> str:
    if char == "\x03":
        raise visuals.UserCancelledError()

    if char == "\x1b" and seq == "[A":
        return "UP"
    if char == "\x1b" and seq == "[B":
        return "DOWN"

    if enable_left_right:
        if char == "\x1b" and seq == "[D":
            return "LEFT"
        if char == "\x1b" and seq == "[C":
            return "RIGHT"

    if enable_tab and char == "\t":
        return "TAB"

    if char in ("\r", "\n"):
        return "ENTER"

    if enable_search and char in ("/", "s", "S"):
        return "SEARCH"

    if separate_quit_back:
        if char in ("q", "Q"):
            return "QUIT"
        if char in ("b", "B"):
            return "BACK"
    elif char in ("q", "Q", "b", "B"):
        return "BACK"

    if enable_amongus and char in ("k", "K"):
        return "AMONGUS"

    return "OTHER"


def read_key(
    *,
    enable_left_right: bool = False,
    enable_tab: bool = False,
    enable_search: bool = False,
    enable_amongus: bool = False,
    separate_quit_back: bool = False,
) -> str:
    if os.name == "nt":
        if msvcrt is None:
            return "OTHER"

        char = msvcrt.getwch()
        if char == "\x03":
            raise visuals.UserCancelledError()

        if char in ("\x00", "\xe0"):
            next_char = msvcrt.getwch()
            if next_char == "H":
                return "UP"
            if next_char == "P":
                return "DOWN"
            if enable_left_right and next_char == "K":
                return "LEFT"
            if enable_left_right and next_char == "M":
                return "RIGHT"
            return "OTHER"

        return _map_key(
            char,
            enable_left_right=enable_left_right,
            enable_tab=enable_tab,
            enable_search=enable_search,
            enable_amongus=enable_amongus,
            separate_quit_back=separate_quit_back,
        )

    if tty is None or termios is None or not sys.stdin.isatty():
        return "OTHER"

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x1b":
            seq = sys.stdin.read(2)
            return _map_key(
                char,
                seq,
                enable_left_right=enable_left_right,
                enable_tab=enable_tab,
                enable_search=enable_search,
                enable_amongus=enable_amongus,
                separate_quit_back=separate_quit_back,
            )

        return _map_key(
            char,
            enable_left_right=enable_left_right,
            enable_tab=enable_tab,
            enable_search=enable_search,
            enable_amongus=enable_amongus,
            separate_quit_back=separate_quit_back,
        )
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
