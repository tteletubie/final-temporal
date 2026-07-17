# 1. Standard Libraries
import os
import select
import signal
import sys
import time
from typing import List

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
from rich.panel import Panel
from rich.table import Table

# 3. Local Modules
from library import books
from auth import credentials
from ui import visuals
from database import database

# Create console instance
console = Console()


def handle_sigint(signum, frame) -> None:
    raise visuals.UserCancelledError()


MENUBOOKS = [
    { "name": " Books ", "topics": ["Title", "Categories", "Author"], "color": "green" },
    { "name": "Login / Sign In", "topics": ["Login", "Sign Up"], "color": "green" },
    { "name": "About", "topics": ["Staff", "Rules", "Made by"], "color": "green" }
]


def draw_menu(title: str, options: List[str], color: str, selected: int) -> None:
    console.clear()
    visuals.big_title("BOOKWORMS")

    table = Table(show_header=False, box=None, expand=True, pad_edge=False)
    table.add_column(ratio=1)

    updated_options = [MENUBOOKS[0]["name"] if opt == MENUBOOKS[0]["name"] else opt for opt in options]

    # 2. Calculation
    longest_opt_len = max(len(opt) for opt in updated_options)
    total_width = longest_opt_len + 40

    for idx, opt in enumerate(updated_options):
        if idx > 0:
            table.add_row("")

        if idx == selected:
            table.add_row(f"[bold white on {color}]{opt:^{total_width}}[/]")
        else:
            table.add_row(f"{opt:^{total_width}}")

    help_text = "Use Up/Down arrows and Enter to select. Press q to exit."
    panel = Panel.fit(
        table,
        title=f"[bold #00FFB3]{title}[/bold #00FFB3]",
        subtitle=help_text,
        border_style="#00FFB3",
        width=70,
        padding=(1, 4),
    )
    console.print(Align.center(panel))


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


def read_key() -> str:
    """Read one keypress and map arrows, enter, back, and quit to semantic values."""
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


def wait_for_exit(delay: float = 5.0) -> None:
    """Wait briefly for a keypress before exiting, using a portable implementation."""
    if os.name == "nt":
        if msvcrt is None:
            return
        end_time = time.time() + delay
        while time.time() < end_time:
            if msvcrt.kbhit():
                msvcrt.getwch()
                break
            time.sleep(0.1)
        return

    if not sys.stdin.isatty():
        return
    select.select([sys.stdin], [], [], delay)
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        sys.stdin.read(1)


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
            draw_menu("🐛 MENU 🐛", group_options, "blue", selected)
            key = read_key()

            if key == "QUIT":
                break
            if key == "UP":
                selected = (selected - 1) % len(group_options)
            elif key == "DOWN":
                selected = (selected + 1) % len(group_options)
            elif key == "ENTER":
                if selected == len(group_options) - 1:
                    break
                current_group = selected
                selected = 0
                view = "topics"
        else:
            topics = MENUBOOKS[current_group]["topics"]
            topic_options = topics + ["← Back"]
            color = MENUBOOKS[current_group]["color"]
            draw_menu(MENUBOOKS[current_group]["name"], topic_options, color, selected)
            key = read_key()

            if key == "QUIT":
                break
            if key == "UP":
                selected = (selected - 1) % len(topic_options)
            elif key == "DOWN":
                selected = (selected + 1) % len(topic_options)
            elif key == "BACK":
                selected = 0
                view = "groups"
            elif key == "ENTER":
                if selected == len(topic_options) - 1:
                    selected = 0
                    view = "groups"
                else:
                    topic = topics[selected]
                    if topic == "Login":
                        logged_username = credentials.login()
                        if logged_username:
                            # Here you can add the authentication logic
                            show_placeholder(
                                f"Attempting to log in as {logged_username}..."
                            )      
                    elif topic == "Sign Up":
                        credentials.sign_up()
                        """
                        role, user = credentials.sign_up()
                        # Here you can add the user creation logic
                        show_placeholder(
                            f"User {user['username']} created with role {role}"
                        )"""
                    elif topic == "Categories": 
                        books.show_category()
                    elif topic == "Title":
                        books.show_title()
                    elif topic == "Author":
                        books.show_author()
                    else:
                        show_placeholder(topic)
                    selected = 0


def main() -> None:
    # ★ -> Start for first time (improve this piece of SHIT :poop:)
    database.initialize_database()

    # Program Code
    console.clear()
    visuals.big_title("BOOKWORMS")
    run_menu()

    # Exit code
    console.clear()
    visuals.big_title("BOOKWORMS")
    console.print(
        Align.center(
            Panel("📖 ¡THANK YOU FOR USING WORMBOOKS! 📖", border_style="#01796F")
        )
    )
    console.print(Align.center("[dim]Press Enter or wait 5s to exit...[/dim]"))
    wait_for_exit(5)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        main()
    except (KeyboardInterrupt, visuals.UserCancelledError):
        visuals.show_cancelled_panel(console)
