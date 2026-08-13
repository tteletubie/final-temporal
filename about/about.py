# 1. Standard Libraries
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

# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.console import Group
from rich.panel import Panel

# 3. Local Modules``
from ui import visuals

console = Console()


def _map_key(char: str, seq: str = "") -> str:
    if char == "\x03":
        raise visuals.UserCancelledError()
    if char == "\x1b" and seq == "[A":
        return "UP"
    if char == "\x1b" and seq == "[B":
        return "DOWN"
    if char in ("\r", "\n"):
        return "ENTER"
    if char in ("q", "Q"):
        return "QUIT"
    if char in ("b", "B"):
        return "BACK"
    return "OTHER"


def _read_key() -> str:
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
            return "OTHER"
        return _map_key(char)

    if tty is None or termios is None or not sys.stdin.isatty():
        return "OTHER"

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x1b":
            seq = sys.stdin.read(2)
            return _map_key(char, seq)
        return _map_key(char)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def show_staff():
    while True:
        console.clear()
        visuals.big_title("BOOKWORMS")
        staff_panel = Panel(
            Group(
                Align.center("\n[bold]Luis [green]Gael [/green]Gonzalez Torres\n"),
                Align.center("[bold][red]Carlos[/red] Silva Cortes\n"),
                Align.center("[bold][magenta]Lesly [/magenta] Adilene Terrazo Rodriguez\n"),
                Align.center("[bold]Maria [purple]Fernanda[/purple] Obregon Ramirez\n"),
            ),
            title="[bold #00FFB3]BookWorm Admins [/bold #00FFB3]",
            border_style="#00FFB3",
            width=50,
        )
        console.print(Align.center(staff_panel))
        console.print(Align.center("[dim]q back | b back | Enter return[/dim]"))

        key = _read_key()
        if key in ("QUIT", "BACK", "ENTER"): return


def show_rules():
    while True:
        console.clear()
        visuals.big_title("BOOKWORMS")
        rules_panel = Panel(
            Group(
                Align.center("\n[bold][green]1.[/green] Be respectful to others.\n"),
                Align.center("[bold][green]2.[/green] No spamming or advertising.\n"),
                Align.center("[bold][green]3.[/green] Use appropriate language.\n"),
                Align.center("[bold][green]4.[/green] Follow the community guidelines.\n"),
                Align.center("[bold][green]5.[/green] Report any suspicious activity.\n"),
            ),
            title="[bold #00FFB3]BookWorm Rules [/bold #00FFB3]",
            border_style="#00FFB3",
            width=60,
        )
        console.print(Align.center(rules_panel))
        console.print(Align.center("[dim]q back | b back | Enter return[/dim]"))

        key = _read_key()
        if key in ("QUIT", "BACK", "ENTER"): return


def show_made_by():
    while True:
        console.clear()
        visuals.big_title("BOOKWORMS")
        credits_panel = Panel(
            Group(
                Align.center("\n[bold]Luis [green]Gael [/green]Gonzalez Torres\n"),
                Align.center("[bold][red]Carlos[/red] Silva Cortes\n"),
                Align.center("[bold][magenta]Lesly [/magenta] Adilene Terrazo Rodriguez\n"),
                Align.center("[bold]Maria [purple]Fernanda[/purple] Obregon Ramirez\n"),
            ),
            title="[bold #00FFB3]Made By [/bold #00FFB3]",
            border_style="#00FFB3",
            width=60,
        )
        console.print(Align.center(credits_panel))
        console.print(Align.center("[dim]q back | b back | Enter return[/dim]"))

        key = _read_key()
        if key in ("QUIT", "BACK", "ENTER"): return
