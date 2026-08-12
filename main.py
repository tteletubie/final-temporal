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
from auth import credentials
from library.books import show_author
from library.books import show_title
from library.books import show_categories
from library.books import show_admin_books
from library.books import _generate_full_pdf_report
from library.users import show_admin_users
from database.seed_books import seed_books
from ui import visuals
from library import about
from database import database
from library.amongus import amoung_us

# Create console instance
console = Console()


def handle_sigint(signum, frame) -> None:
    raise visuals.UserCancelledError()


MENUBOOKS = [
    { "name": " 📚 Books ", "topics": ["Title", "Categories", "Author"], "color": "green" },
    { "name": "👤 Login / Sign In", "topics": ["Login", "Sign Up"], "color": "cyan" },
    { "name": "🔒 Admin", "topics": ["Books", "Users", "Generate PDF"], "color": "dark_orange3" },
    { "name": "ℹ️ About", "topics": ["Staff", "Rules", "Made by"], "color": "magenta" }
]


def draw_menu(title: str, options: List[str], color: str, selected: int) -> None:
    console.clear()
    visuals.big_title("BOOKWORMS", color)

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
        title=f"[bold {color}]{title}[/bold {color}]",
        subtitle=help_text,
        border_style=color,
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
    if char in ("k", "K"):
        return "AMONGUS"
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
    current_user = None

    def _get_dynamic_menubooks():
        books_copy = [group.copy() for group in MENUBOOKS]

        if current_user:
            # Filter out Login when logged in (substring match tolerates emoji)
            books_copy = [g for g in books_copy if "Login" not in g["name"]]
            logout_group = { "name": "🚪 Log Out", "topics": ["Confirm Log Out"], "color": "red" }
            about_index = next((i for i, g in enumerate(books_copy) if "About" in g["name"]), -1)
            if about_index != -1:
                books_copy.insert(about_index + 1, logout_group)
            else:
                books_copy.append(logout_group)

        # Hide admin for non-admin users (substring match)
        if not (current_user and current_user.get("role") == "admin"):
            books_copy = [g for g in books_copy if "Admin" not in g["name"]]

        return books_copy

    while True:
        current_menubooks = _get_dynamic_menubooks()

        if view == "groups":
            group_options = [group["name"] for group in current_menubooks] + ["◄ Exit"]
            selected = min(selected, len(group_options) - 1)
            active_color = current_menubooks[selected]["color"] if selected < len(current_menubooks) else "blue"
            draw_menu("🐛 MENU 🐛", group_options, active_color, selected)
            key = read_key()

            if key == "AMONGUS":
                try:
                    amoung_us(console, read_key)
                except Exception:
                    pass
                continue

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

                if "Log Out" in current_menubooks[current_group]["name"]:
                    current_user = None
                    show_placeholder("Successfully logged out!")
                    view = "groups"
                else:
                    view = "topics"
        else:
            topics = current_menubooks[current_group]["topics"]
            topic_options = topics + ["← Back"]
            color = current_menubooks[current_group]["color"]
            draw_menu(current_menubooks[current_group]["name"], topic_options, color, selected)
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
                    group_name = current_menubooks[current_group]["name"]

                    if topic == "Categories":
                        show_categories(topic)
                    elif topic == "Login":
                        authenticated_user = credentials.login()
                        if authenticated_user:
                            current_user = authenticated_user
                            show_placeholder(f"Logged in as {current_user['username']}")
                    elif topic == "Sign Up":
                        authenticated_user = credentials.sign_up()
                        if authenticated_user:
                            current_user = authenticated_user
                            show_placeholder(f"Logged in as {current_user['username']}")
                    elif topic == "Title":
                        show_title(current_user["username"] if current_user else None)
                    elif topic == "Author":
                        show_author(current_user["username"] if current_user else None)
                    elif topic == "Staff":
                        about.show_staff()
                    elif topic == "Rules":
                        about.show_rules()
                    elif topic == "Made by":
                        about.show_made_by()
                    elif "Admin" in group_name and topic == "Books":
                        show_admin_books(current_user["role"] if current_user else "user")
                    elif "Admin" in group_name and topic == "Users":
                        show_admin_users(current_user["role"] if current_user else "user")
                    elif "Admin" in group_name and topic == "Generate PDF":
                        try:
                            _generate_full_pdf_report()
                        except Exception:
                            show_placeholder("Failed to generate PDF report.")
                    else:
                        show_placeholder(topic)
                    selected = 0


def main() -> None:
    database.initialize_database()

    # Program Code
    console.clear()
    visuals.big_title("BOOKWORMS", "#00FF7F")
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
    except visuals.ExitApp:
        console.clear()
        visuals.big_title("BOOKWORMS")
        console.print(
            Align.center(
                Panel("📖 ¡THANK YOU FOR USING WORMBOOKS! 📖", border_style="#01796F")
            )
        )
        console.print(Align.center("[dim]Press Enter or wait 5s to exit...[/dim]"))
        wait_for_exit(5)
    except (KeyboardInterrupt, visuals.UserCancelledError):
        visuals.show_cancelled_panel(console)