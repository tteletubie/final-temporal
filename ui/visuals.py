# 1. Standard Libraries
from datetime import datetime
from typing import Callable

# 2. Third-Party Libraries
from rich.console import Console
from rich.align import Align
from rich import print
from rich.panel import Panel
from pyfiglet import figlet_format

# 3. Local Modules
# Create console instance
console = Console()


def big_title(text: str, color: str = "#00FF7F") -> None:
    big = figlet_format(text, font="slant")
    print(Align.center(f"[{color}]{big}[/{color}]"))


def input(text, field_type="text"):
    console.print(Panel.fit(text, border_style="#01796F"))
    return console.input(
        f"[#01796F] ➜ [/#01796F] ", password=(field_type == "password")
    )


def input_int(text):
    while True:
        value = input(text)
        try:
            return int(value)
        except ValueError:
            error("Please enter a valid integer.")


def enter_date(text):
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]
    while True:
        value = input(text)
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                continue
        error(
            "Please enter a valid date in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY or MM/DD/YYYY format."
        )


def title(text):
    print(Panel(text, style="bold bright_green"))


def exit(text):
    print(f"[green][✓][/green] {text}")


def error(text):
    print(f"[red][✗][/red] {text}")


def alerta(text):
    print(f"[yellow][!][/yellow] {text}")


class UserCancelledError(Exception):
    """Raised when the user cancels the program with Ctrl+C."""


def show_cancelled_panel(console: Console) -> None:
    """Render a consistent cancellation message before exiting."""
    # console.clear()    # Clear the screen after of the exit (the last user process is deleted!)
    console.print(
        "\n",
        Panel.fit(
            "[bold yellow]Execution cancelled by user.[/bold yellow]\n\n"
            "The program closed safely.",
            title="[bold red]CTRL + C[/bold red]",
            border_style="bright_red",
        ),
    )


def show_topic_panel(console: Console, read_key: Callable[[], str], topic: str) -> None:
    """Render a placeholder panel for a selected topic and wait for keypress."""
    console.clear()
    message = (
        f"[bold]Selected:[/bold] {topic}\n\nPlaceholder: add calculator logic here."
    )
    console.print(Panel.fit(message, title="Topic", border_style="green"))
    console.print("Press any key to return...")
    read_key()
