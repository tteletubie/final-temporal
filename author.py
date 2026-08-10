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


def _is_show_all_query(query: str) -> bool:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    return query_tokens in (["all"], ["authors"], ["all", "authors"], ["authors", "all"])


def _fetch_books() -> list:
    with db.get_connection() as conn:
        rows = conn.execute("SELECT name, category, author, year FROM books ORDER BY author, name, year").fetchall()
    return rows


def _search_books_by_author(query: str) -> list:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    if not query_tokens: return _fetch_books()

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

        if match: results.append(row)

    return results


def _build_books_table(rows: list) -> Table:
    table = Table(show_header=True, header_style="bold #00FFB3", box=box.SIMPLE_HEAVY, expand=True,)
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


def _render_author_search_view(query: str, rows: list) -> None:
    console.clear()

    query_text = query if query else "(default view)"
    show_all = _is_show_all_query(query)
    visible_rows = _visible_book_rows(rows, show_all=show_all)
    has_more_rows = len(rows) > len(visible_rows)

    search_panel = Table.grid(padding=(0, 0))
    search_panel.add_row(f"[bold #00FFB3]Search by author:[/bold #00FFB3] [white]{query_text}[/white]")
    search_panel.add_row("[dim]Press Enter for the default view, or type all authors to show everything. q to back.[/dim]")

    console.print(Align.center(Panel.fit(search_panel, border_style="#01796F", title="Author Search")))

    book_panel_body = Table.grid(padding=(0, 0))
    book_panel_body.add_row(f"[bold #00FFB3]Books with author: {query_text}[/bold #00FFB3]")
    book_table = _build_books_table(visible_rows)
    if has_more_rows: book_table.add_row("... more results available", "-", "-", "-")
    book_panel_body.add_row(book_table)

    console.print(Align.center(Panel.fit(book_panel_body, border_style="#01796F", box=box.ROUNDED, padding=(0, 1))))
    if has_more_rows: console.print(Align.center("[dim]Showing the first page only. Type all authors to show every result.[/dim]"))


def show_author() -> None:
    query = ""
    rows = _fetch_books()

    if not rows:
        console.clear()
        console.print(Panel.fit("No books available.", title="Author Search", border_style="green"))
        console.input("Press Enter to return...")
        return

    while True:
        _render_author_search_view(query, rows)
        user_input = console.input("[bold #00FFB3]Search author[/bold #00FFB3] (q to back, Enter for default): ").strip()

        if user_input.lower() in ("q", "b"):
            return

        query = user_input
        if _is_show_all_query(query):
            rows = _fetch_books()
        else:
            rows = _search_books_by_author(query) if query else _fetch_books()