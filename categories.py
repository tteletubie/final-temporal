import sys

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - Windows fallback
    termios = None
    tty = None

from rich.align import Align
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from database import database as db


console = Console()


def _map_key(char: str, seq: str = "") -> str:
    if char == "\x1b" and seq == "[A":
        return "UP"
    if char == "\x1b" and seq == "[B":
        return "DOWN"
    if char in ("\r", "\n"):
        return "ENTER"
    if char in ("q", "Q", "b", "B"):
        return "BACK"
    return "OTHER"


def _read_key() -> str:
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


def _fetch_categories() -> list[str]:
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM books ORDER BY category"
        ).fetchall()
    return [str(row["category"]) for row in rows]


def _fetch_books_by_category(category: str):
    with db.get_connection() as conn:
        return conn.execute(
            """
            SELECT name, author, year
            FROM books
            WHERE category = ?
            ORDER BY name
            """,
            (category,),
        ).fetchall()


def _render_categories_view(categories: list[str], selected_index: int) -> None:
    console.clear()

    selected_category = categories[selected_index]
    books = _fetch_books_by_category(selected_category)

    category_table = Table(show_header=False, box=None, expand=True, pad_edge=False)
    category_table.add_column(style="white", no_wrap=False)

    for index, category in enumerate(categories):
        if index == selected_index:
            category_table.add_row(f"[bold black on #00FFB3] {category} [/]")
        else:
            category_table.add_row(f"[white] {category} [/]")

    book_table = Table(show_header=True, header_style="bold #00FFB3", box=box.SIMPLE_HEAVY, expand=True)
    book_table.add_column("Title", style="white", no_wrap=False)
    book_table.add_column("Author", style="white", no_wrap=False)
    book_table.add_column("Year", style="white", no_wrap=False)

    if books:
        for row in books:
            book_table.add_row(str(row["name"]), str(row["author"]), str(row["year"]))
    else:
        book_table.add_row("No books found", "-", "-")

    category_panel_body = Table.grid(padding=(0, 0))
    category_panel_body.add_row("[bold #00FFB3]Categories[/bold #00FFB3]")
    category_panel_body.add_row(category_table)

    book_panel_body = Table.grid(padding=(0, 0))
    book_panel_body.add_row(f"[bold #00FFB3]Books in {selected_category}[/bold #00FFB3]")
    book_panel_body.add_row(book_table)

    layout = Table.grid(expand=True, padding=(0, 1))
    layout.add_column(ratio=1, no_wrap=True)
    layout.add_column(ratio=3)
    layout.add_row(
        Panel.fit(category_panel_body, border_style="#01796F", padding=(0, 1)),
        Panel.fit(book_panel_body, border_style="#01796F", padding=(0, 1)),
    )

    console.print(layout)
    console.print(Align.center("[dim]↑↓ change category | q back[/dim]"))


def show_categories(view: str) -> None:
    if view == "Categories":
        categories = _fetch_categories()
        if not categories:
            console.clear()
            console.print(Panel.fit("No categories available.", title="Categories", border_style="green"))
            console.input("Press Enter to return...")
            return

        selected_index = 0

        while True:
            _render_categories_view(categories, selected_index)
            key = _read_key()

            if key in ("BACK", "ENTER"):
                return
            if key == "UP":
                selected_index = (selected_index - 1) % len(categories)
            elif key == "DOWN":
                selected_index = (selected_index + 1) % len(categories)

        
    console.clear()
    console.print(Panel.fit("This view currently only supports Categories.", title="Categories", border_style="green"))
    console.input("Press Enter to return...")