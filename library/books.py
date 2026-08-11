# 1. Standard Libraries
import sys

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - Windows fallback
    termios = None
    tty = None

# 2. Third-Party Libraries
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 3. Local Modules
from database import database as db
from ui import visuals


console = Console()


def _normalize_text(value: str) -> str:
    cleaned = []
    for char in value.lower():
        cleaned.append(char if (char.isalnum() or char.isspace()) else " ")
    return " ".join("".join(cleaned).split())


def _stem_token(token: str) -> str:
    if len(token) > 3 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _is_show_all_query(query: str) -> bool:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    return query_tokens in (
        ["all"],
        ["books"],
        ["authors"],
        ["categories"],
        ["all", "books"],
        ["books", "all"],
        ["all", "authors"],
        ["authors", "all"],
        ["all", "categories"],
        ["categories", "all"],
    )


def _fetch_books() -> list:
    with db.get_connection() as conn:
        rows = conn.execute("SELECT name, category, author, year FROM books ORDER BY name, author, year").fetchall()
    return rows


def _search_books_by_title(query: str) -> list:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    if not query_tokens:
        return _fetch_books()

    results = []
    for row in _fetch_books():
        title_tokens = _normalize_text(str(row["name"])).split()
        title_token_set = set(title_tokens)
        title_stem_set = {_stem_token(token) for token in title_tokens}

        match = True
        for token in query_tokens:
            token_stem = _stem_token(token)
            has_prefix_match = any(
                title_token.startswith(token) or title_token.startswith(token_stem)
                for title_token in title_token_set
            )
            has_stem_match = token_stem in title_stem_set
            if not (has_prefix_match or has_stem_match):
                match = False
                break

        if match:
            results.append(row)

    return results


def _search_books_by_author(query: str) -> list:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    if not query_tokens:
        return _fetch_books()

    results = []
    for row in _fetch_books():
        author_tokens = _normalize_text(str(row["author"])).split()
        author_token_set = set(author_tokens)

        match = True
        for token in query_tokens:
            has_prefix_match = any(author_token.startswith(token) for author_token in author_token_set)
            if not has_prefix_match:
                match = False
                break

        if match:
            results.append(row)

    return results


def _search_books_by_category(query: str) -> list:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    if not query_tokens:
        return _fetch_books()

    results = []
    for row in _fetch_books():
        category_tokens = _normalize_text(str(row["category"])).split()
        category_token_set = set(category_tokens)

        match = True
        for token in query_tokens:
            has_prefix_match = any(category_token.startswith(token) for category_token in category_token_set)
            if not has_prefix_match:
                match = False
                break

        if match:
            results.append(row)

    return results


def _build_books_table(rows: list) -> Table:
    table = Table(
        show_header=True,
        header_style="bold #00FFB3",
        box=box.SIMPLE_HEAVY,
        expand=True,
    )
    table.add_column("Title", style="white", no_wrap=False)
    table.add_column("Category", style="white", no_wrap=False)
    table.add_column("Author", style="white", no_wrap=False)
    table.add_column("Year", style="white", no_wrap=False)

    if rows:
        for row in rows:
            table.add_row(
                str(row["name"]),
                str(row["category"]),
                str(row["author"]),
                str(row["year"]),
            )
    else:
        table.add_row("No books found", "-", "-", "-")

    return table


def _visible_book_rows(rows: list, show_all: bool = False) -> list:
    if show_all:
        return rows

    max_rows = max(1, console.size.height - 14)
    if len(rows) <= max_rows:
        return rows

    return rows[: max_rows - 1]


def _render_search_view(title: str, query_label: str, query: str, rows: list, help_message: str) -> None:
    console.clear()

    query_text = query if query else "(default view)"
    show_all = _is_show_all_query(query)
    visible_rows = _visible_book_rows(rows, show_all=show_all)
    has_more_rows = len(rows) > len(visible_rows)

    search_panel = Table.grid(padding=(0, 0))
    search_panel.add_row(f"[bold #00FFB3]{query_label}[/bold #00FFB3] [white]{query_text}[/white]")
    search_panel.add_row(f"[dim]{help_message} q to back.[/dim]")

    console.print(Align.center(Panel.fit(search_panel, border_style="#01796F", title=title)))

    book_panel_body = Table.grid(padding=(0, 0))
    book_panel_body.add_row(f"[bold #00FFB3]Results for: {query_text}[/bold #00FFB3]")
    book_table = _build_books_table(visible_rows)
    if has_more_rows:
        book_table.add_row("... more results available", "-", "-", "-")
    book_panel_body.add_row(book_table)

    console.print(Align.center(Panel.fit(book_panel_body, border_style="#01796F", box=box.ROUNDED, padding=(0, 1))))
    if has_more_rows:
        console.print(Align.center("[dim]Showing the first page only. Type all to show every result.[/dim]"))


def show_category() -> None:
    query = ""
    rows = _fetch_books()

    if not rows:
        console.clear()
        console.print(Panel.fit("No books available.", title="Category Search", border_style="green"))
        console.input("Press Enter to return...")
        return

    while True:
        _render_search_view(
            "Search by Category",
            "Search by category:",
            query,
            rows,
            "Press Enter for the default view, or type all categories to show everything.",
        )
        user_input = console.input("[bold #00FFB3]Search category[/bold #00FFB3] (q to back, Enter for default): ").strip()

        if user_input.lower() in ("q", "b"):
            return

        query = user_input
        if _is_show_all_query(query):
            rows = _fetch_books()
        else:
            rows = _search_books_by_category(query) if query else _fetch_books()


def show_title() -> None:
    query = ""
    rows = _fetch_books()

    if not rows:
        console.clear()
        console.print(Panel.fit("No books available.", title="Title Search", border_style="green"))
        console.input("Press Enter to return...")
        return

    while True:
        _render_search_view(
            "Title Search",
            "Search by title:",
            query,
            rows,
            "Press Enter for the default view, or type all books to show everything.",
        )
        user_input = console.input("[bold #00FFB3]Search title[/bold #00FFB3] (q to back, Enter for default): ").strip()

        if user_input.lower() in ("q", "b"):
            return

        query = user_input
        if _is_show_all_query(query):
            rows = _fetch_books()
        else:
            rows = _search_books_by_title(query) if query else _fetch_books()


def show_author() -> None:
    query = ""
    rows = _fetch_books()

    if not rows:
        console.clear()
        console.print(Panel.fit("No books available.", title="Author Search", border_style="green"))
        console.input("Press Enter to return...")
        return

    while True:
        _render_search_view(
            "Author Search",
            "Search by author:",
            query,
            rows,
            "Press Enter for the default view, or type all authors to show everything.",
        )
        user_input = console.input("[bold #00FFB3]Search author[/bold #00FFB3] (q to back, Enter for default): ").strip()

        if user_input.lower() in ("q", "b"):
            return

        query = user_input
        if _is_show_all_query(query):
            rows = _fetch_books()
        else:
            rows = _search_books_by_author(query) if query else _fetch_books()


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


def show_category_browser() -> None:
    show_categories("Categories")
