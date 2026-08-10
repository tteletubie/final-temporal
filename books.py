# 2. Third-Party Libraries
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 3. Local Modules
from database import database as db

# Create console instance
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
    return query_tokens in (["all"], ["books"], ["all", "books"], ["books", "all"])


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

        if match: results.append(row)

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
    else: table.add_row("No books found", "-", "-", "-")

    return table


def _visible_book_rows(rows: list, show_all: bool = False) -> list:
    if show_all: return rows

    max_rows = max(1, console.size.height - 14)
    if len(rows) <= max_rows: return rows

    return rows[: max_rows - 1]


def _render_title_search_view(query: str, rows: list) -> None:
    console.clear()

    query_text = query if query else "(default view)"
    show_all = _is_show_all_query(query)
    visible_rows = _visible_book_rows(rows, show_all=show_all)
    has_more_rows = len(rows) > len(visible_rows)

    search_panel = Table.grid(padding=(0, 0))
    search_panel.add_row(f"[bold #00FFB3]Search by title:[/bold #00FFB3] [white]{query_text}[/white]")
    search_panel.add_row("[dim]Press Enter for the default view, or type all books to show everything. q to back.[/dim]")

    console.print(Align.center(Panel.fit(search_panel, border_style="#01796F", title="Title Search")))

    book_panel_body = Table.grid(padding=(0, 0))
    book_panel_body.add_row(f"[bold #00FFB3]Books with title: {query_text}[/bold #00FFB3]")
    book_table = _build_books_table(visible_rows)
    if has_more_rows: book_table.add_row("... more results available", "-", "-", "-")
    book_panel_body.add_row(book_table)

    console.print(Align.center(Panel.fit(book_panel_body, border_style="#01796F", box=box.ROUNDED, padding=(0, 1))))
    if has_more_rows: console.print(Align.center("[dim]Showing the first page only. Type all books to show every result.[/dim]"))


def show_title() -> None:
    query = ""
    rows = _fetch_books()

    if not rows:
        console.clear()
        console.print(Panel.fit("No books available.", title="Title Search", border_style="green"))
        console.input("Press Enter to return...")
        return

    while True:
        _render_title_search_view(query, rows)
        user_input = console.input("[bold #00FFB3]Search title[/bold #00FFB3] (q to back, Enter for default): ").strip()

        if user_input.lower() in ("q", "b"):
            return

        query = user_input
        if _is_show_all_query(query):
            rows = _fetch_books()
        else:
            rows = _search_books_by_title(query) if query else _fetch_books()
