# 1. Standard Libraries
import signal
import sys
import termios
import tty

# 2. Third-Party Libraries
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 3. Local Modules
import visual
from login import login_u
from visual import UserCancelledError, show_cancelled_panel
# Create console instance
console = Console()


MENUBOOKS = [
    {
        "name": "Functions",
        "topics": [
            "Users",
            "Admins",
            "Books",
            "Services",
            "Offences"
        ],
        "color": "green"
    },
]

def draw_menu(title: str, options: list[str], color: str, selected: int) -> None:
    console.clear()
    visual.title("MENU")
    table = Table(show_header=False, box=None, expand=True, pad_edge=False)
    table.add_column(ratio=1)

    for idx, opt in enumerate(options):
        if idx == selected: table.add_row(f"[bold black on {color}]> {opt}[/]")
        else: table.add_row(f"  {opt}")

    help_text = "Use Up/Down arrows and Enter to select. Press q to exit."
    panel = Panel.fit(table, title=f"[bold]{title}[/bold]", subtitle=help_text, border_style=color)
    console.print(panel)


def read_key() -> str:
    """Read one keypress and map arrows, enter, back, and quit to semantic values."""

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)

        if char == "\x03":
            raise UserCancelledError()

        if char == "\x1b":
            seq = sys.stdin.read(2)
            if seq == "[A": return "UP"
            if seq == "[B": return "DOWN"
            return "OTHER"

        if char in ("\r", "\n"): return "ENTER"
        if char in ("q", "Q"): return "QUIT"
        if char in ("b", "B"): return "BACK"
        return "OTHER"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def show_placeholder(topic: str) -> None:
    console.clear()
    console.print(Panel.fit(f"[bold]Selected:[/bold] {topic}\n\nPlaceholder: ....", title="Topic", border_style="green"))
    console.print("Press any key to return...")
    read_key()


def run_menu() -> None:
    view = "groups"
    selected = 0
    current_group = 0

    while True:
        if view == "groups":
            group_options = [g["name"] for g in MENUBOOKS] + ["◄ Exit"]
            draw_menu(" MENU ", group_options, "blue", selected)
            key = read_key()

            if key == "QUIT": break
            if key == "UP": selected = (selected - 1) % len(group_options)
            elif key == "DOWN": selected = (selected + 1) % len(group_options)
            elif key == "ENTER":
                if selected == len(group_options) - 1: break
                current_group = selected
                selected = 0
                view = "topics"
        else:
            topics = MENUBOOKS[current_group]["topics"]
            topic_options = topics + ["← Back"]
            color = MENUBOOKS[current_group]["color"]

            draw_menu(MENUBOOKS[current_group]["name"], topic_options, color, selected)
            key = read_key()

            if key == "QUIT": break
            if key == "UP": selected = (selected - 1) % len(topic_options)
            elif key == "DOWN": selected = (selected + 1) % len(topic_options)
            elif key == "BACK":
                selected = 0
                view = "groups"
            elif key == "ENTER":
                if selected == len(topic_options) - 1:
                    selected = 0
                    view = "groups"
                """ else:
                    topic_name = topics[selected]
                    topic_handler = TOPIC_HANDLERS.get(topic_name)

                    if topic_handler is not None:
                        topic_handler(console, read_key)
                    else:
                        show_placeholder(topic_name)"""