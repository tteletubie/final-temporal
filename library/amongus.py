from typing import Callable

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import time


CREWMATE = [
    ("⠀⠀⠀⠀⢀⣴⣶⠿⠟⠻⠿⢷⣦⣄⠀⠀⠀", "red"),
    ("⠀⠀⠀⠀⣾⠏⠀⠀⣠⣤⣤⣤⣬⣿⣷⣄⡀", "red", 7, 18, "cyan"),
    ("⠀⢀⣀⣸⡿⠀⠀⣼⡟⠁⠀⠀⠀⠀⠀⠙⣷", "red", 7, 18, "cyan"),
    ("⢸⡟⠉⣽⡇⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⢀⣿", "red", 7, 18, "cyan"),
    ("⣾⠇⠀⣿⡇⠀⠀⠘⠿⢶⣶⣤⣤⣶⡶⣿⠋", "red", 7, 18, "cyan"),
    ("⣿⠂⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠃", "red"),
    ("⣿⡆⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀", "red"),
    ("⢿⡇⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀", "red"),
    ("⠘⠻⠷⢿⡇⠀⠀⠀⣴⣶⣶⠶⠖⠀⢸⡟⠀", "red"),
]

LEG_FRAMES = [
    [
        ("⠀⠀⠀⢸⣇⠀⠀⠀⣿⡇⣿⡄⠀⢀⣿⠇⠀", "red"),
        ("⠀⠀⠀⠘⣿⣤⣤⣴⡿⠃⠙⠛⠛⠛⠋⠀⠀", "red"),
    ],
    [
        ("⠀⠀⠀⢸⣧⠀⠀⠀⠀⣿⡇⣿⠀⢀⣿⠇⠀", "red"),
        ("⠀⠀⠀⠘⠀⣿⣤⣤⣴⡿⠙⠛⠛⠛⠋⠀⠀", "red"),
    ],
]


def _build_frame(x_offset: int, leg_frame: int) -> Text:
    text = Text()
    padding = " " * x_offset

    for row in CREWMATE:
        text.append(padding)
        if len(row) == 5:
            line, color, visor_start, visor_end, visor_color = row
            text.append(line[:visor_start], style=color)
            text.append(line[visor_start:visor_end], style=visor_color)
            text.append(line[visor_end:], style=color)
        else:
            text.append(row[0], style=row[1])
        text.append("\n")

    for leg_row in LEG_FRAMES[leg_frame]:
        text.append(padding)
        text.append(leg_row[0], style=leg_row[1])
        text.append("\n")

    return text


def amoung_us(console: Console, read_key: Callable[[], str]) -> None:
    console.clear()
    console.print(Align.center(Panel.fit("Press any key to stop...", title="Among Us", border_style="red")))

    # Size the animation area relative to the console width and center it.
    console_width = max(40, console.size.width)
    SCREEN_WIDTH = min(60, console_width - 4)
    CHAR_WIDTH = 17
    max_x = max(0, SCREEN_WIDTH - CHAR_WIDTH)
    # compute left margin so the animation block is centered
    left_margin = max(0, (console_width - SCREEN_WIDTH) // 2)
    step_size = 2

    x = 0
    direction = 1
    leg = 0
    leg_timer = 0

    with Live("", refresh_per_second=12, console=console) as live:
        while True:
            frame = _build_frame(left_margin + x, leg)
            live.update(frame)
            time.sleep(0.08)

            x += direction * step_size
            if x >= max_x:
                x = max_x
                direction = -1
            elif x <= 0:
                x = 0
                direction = 1

            leg_timer += 1
            if leg_timer >= 3:
                leg = 1 - leg
                leg_timer = 0

            # Non-blocking key check, stop if any key is pressed
            import sys, select
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.read(1)
                break

    console.print(Align.center("\n[bold red]⚠  Red was The Impostor  ⚠[/bold red]"))
    console.print(Align.center("Press any key to continue..."))
    read_key()
    
    ascii_art = (
        "⠀⠀⠀⢸⣦⡀⠀⠀⠀⠀⢀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⢸⣏⠻⣶⣤⡶⢾⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⣀⣼⠷⠀⠀⠁⢀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
        "⠴⣾⣯⣅⣀⠀⠀⠀⠈⢻⣦⡀        ⠀⠀⢀⡇⠀⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠉⢻⡇⣤⣾⣿⣷⣿⣿⣤⠀⠀  ⠀⠀⠀⢀⣴⣿⣿⠀⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠸⣿⡿⠏⠀⢀⠀⠀⠿⣶⣤⣤⣤⣄⣀⣴⣿⡿⢻⣿⡆⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠟⠁⠀⢀⣼⠀⠀⠀⠹⣿⣟⠿⠿⠿⡿⠋⠀⠘⣿⣇⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⢳⣶⣶⣿⣿⣇⣀⠀⠀⠙⣿⣆⠀⠀⠀⠀⠀⠀⠛⠿⣿⣦⣤⣀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠀⣹⣿⣿⣿⣿⠿⠋⠁⠀⣹⣿⠳⠀⠀⠀⠀⠀⠀⢀⣠⣽⣿⡿⠟⠃\n"
        "⠀⠀⠀⠀⠀⢰⠿⠛⠻⢿⡇⠀⠀⠀⣰⣿⠏⠀⠀⢀⠀⠀⠀⣾⣿⠟⠋⠁⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠋⠀⠀⣰⣿⣿⣾⣿⠿⢿⣷⣀⢀⣿⡇⠁⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠋⠉⠁⠀⠀⠀⠀⠙⢿⣿⣿⠇⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⠀⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀\n"
    )

    console.clear()
    console.print(Align.center(Text(ascii_art, style="blue")))
    console.print(Align.center(Text("⠀⠀⠀⠀⠀⠀⠀      CHEESE CREW    ⠀⠀⠀⠀⠀⠀⠀\n", style="yellow")))
    console.print(Align.center("\n[dim]Press any key to return to menu...[/dim]"))
    read_key()
