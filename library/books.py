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


def _normal_visible_rows(rows: list, selected_index: int) -> tuple[list, int]:
    max_rows = max(3, console.size.height - 18)
    if len(rows) <= max_rows:
        return rows, 0

    start = max(0, selected_index - (max_rows // 2))
    end = start + max_rows
    if end > len(rows):
        end = len(rows)
        start = end - max_rows

    return rows[start:end], start


def _render_normal_books_view(
    title: str,
    query_label: str,
    query: str,
    rows: list,
    selected_index: int,
    default_hint: str,
) -> None:
    console.clear()

    visible_rows, start_index = _normal_visible_rows(rows, selected_index)
    query_text = query if query else "(all books)"

    top = Table.grid(padding=(0, 0))
    top.add_row(f"[bold #00FFB3]{query_label}[/bold #00FFB3] [white]{query_text}[/white]")
    top.add_row(f"[dim]{default_hint}[/dim]")
    top.add_row(f"[dim]Showing {len(visible_rows)} of {len(rows)} result(s). Press / to search.[/dim]")
    console.print(Align.center(Panel.fit(top, border_style="#01796F", title=title)))

    table = Table(show_header=True, header_style="bold #00FFB3", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("Title", style="white", no_wrap=False)
    table.add_column("Category", style="white", no_wrap=False)
    table.add_column("Author", style="white", no_wrap=False)
    table.add_column("Year", style="white", no_wrap=False)

    if rows:
        for index, row in enumerate(visible_rows):
            global_index = start_index + index
            is_selected = global_index == selected_index
            row_style_prefix = "[bold black on #00FFB3]" if is_selected else ""
            row_style_suffix = "[/]" if is_selected else ""

            table.add_row(
                f"{row_style_prefix}{row['name']}{row_style_suffix}",
                f"{row_style_prefix}{row['category']}{row_style_suffix}",
                f"{row_style_prefix}{row['author']}{row_style_suffix}",
                f"{row_style_prefix}{row['year']}{row_style_suffix}",
            )

        if len(rows) > len(visible_rows):
            table.add_row("...", "More books available", "Use ↑↓ to scroll", "")
    else:
        table.add_row("No books found", "-", "-", "-")

    console.print(Align.center(Panel.fit(table, border_style="#01796F", box=box.ROUNDED, padding=(0, 1))))
    console.print(Align.center("[dim]Press / to search | ↑↓ scroll | q back[/dim]"))


def _browse_books(
    title: str,
    query_label: str,
    default_hint: str,
    search_fn,
) -> None:
    query = ""
    selected_index = 0

    while True:
        rows = _fetch_books() if not query else search_fn(query)
        if rows:
            selected_index = min(selected_index, len(rows) - 1)
        else:
            selected_index = 0

        _render_normal_books_view(title, query_label, query, rows, selected_index, default_hint)
        key = _read_key()

        if key == "BACK":
            return
        if key == "SEARCH":
            query = console.input("Search (Enter for all books): ").strip()
            selected_index = 0
        elif key == "UP" and rows:
            selected_index = (selected_index - 1) % len(rows)
        elif key == "DOWN" and rows:
            selected_index = (selected_index + 1) % len(rows)


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
    _browse_books(
        "Search by Category",
        "Search by category:",
        "Use / to search categories.",
        _search_books_by_category,
    )


def show_title() -> None:
    _browse_books(
        "Title Search",
        "Search by title:",
        "Use / to search titles.",
        _search_books_by_title,
    )


def show_author() -> None:
    _browse_books(
        "Author Search",
        "Search by author:",
        "Use / to search authors.",
        _search_books_by_author,
    )


def _map_key(char: str, seq: str = "") -> str:
    if char == "\x1b" and seq == "[A":
        return "UP"
    if char == "\x1b" and seq == "[B":
        return "DOWN"
    if char == "\x1b" and seq == "[D":
        return "LEFT"
    if char == "\x1b" and seq == "[C":
        return "RIGHT"
    if char == "\t":
        return "TAB"
    if char in ("\r", "\n"):
        return "ENTER"
    if char in ("/", "s", "S"):
        return "SEARCH"
    if char in ("q", "Q", "b", "B"):
        return "BACK"
    return "OTHER"


def _read_key() -> str:
    if os.name == "nt":
        if msvcrt is None:
            return "OTHER"

        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            next_char = msvcrt.getwch()
            if next_char == "H":
                return "UP"
            if next_char == "P":
                return "DOWN"
            if next_char == "K":
                return "LEFT"
            if next_char == "M":
                return "RIGHT"
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


def _fetch_books_with_ids() -> list:
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, category, author, year
            FROM books
            ORDER BY name, author, year
            """
        ).fetchall()
    return rows


def _update_book(book_id: int, name: str, category: str, author: str, year: str) -> None:
    with db.get_connection() as conn:
        conn.execute(
            """
            UPDATE books
            SET name = ?, category = ?, author = ?, year = ?
            WHERE id = ?
            """,
            (name, category, author, year, book_id),
        )
        conn.commit()


def _delete_book(book_id: int) -> None:
    with db.get_connection() as conn:
        conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()


def _search_books_for_admin(rows: list, query: str) -> list:
    normalized_query = _normalize_text(query)
    query_tokens = normalized_query.split()
    if not query_tokens:
        return rows

    filtered_rows = []
    for row in rows:
        searchable_text = _normalize_text(
            f"{row['name']} {row['category']} {row['author']} {row['year']} {row['id']}"
        )
        row_tokens = searchable_text.split()
        if all(any(token in row_token for row_token in row_tokens) for token in query_tokens):
            filtered_rows.append(row)

    return filtered_rows


def _admin_visible_rows(rows: list, selected_book_index: int) -> tuple[list, int]:
    max_rows = max(3, console.size.height - 20)
    if len(rows) <= max_rows:
        return rows, 0

    start = max(0, selected_book_index - (max_rows // 2))
    end = start + max_rows
    if end > len(rows):
        end = len(rows)
        start = end - max_rows

    return rows[start:end], start


def _render_admin_books_view(rows: list, selected_book_index: int, selected_action_index: int, query: str) -> None:
    console.clear()

    table = Table(show_header=True, header_style="bold #00FFB3", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("ID", style="white", no_wrap=True)
    table.add_column("Title", style="white", no_wrap=False)
    table.add_column("Category", style="white", no_wrap=False)
    table.add_column("Author", style="white", no_wrap=False)
    table.add_column("Year", style="white", no_wrap=False)

    visible_rows, start_index = _admin_visible_rows(rows, selected_book_index)

    if rows:
        for index, row in enumerate(visible_rows):
            global_index = start_index + index
            is_selected = global_index == selected_book_index
            row_style_prefix = "[bold black on #00FFB3]" if is_selected else ""
            row_style_suffix = "[/]" if is_selected else ""
            table.add_row(
                f"{row_style_prefix}{row['id']}{row_style_suffix}",
                f"{row_style_prefix}{row['name']}{row_style_suffix}",
                f"{row_style_prefix}{row['category']}{row_style_suffix}",
                f"{row_style_prefix}{row['author']}{row_style_suffix}",
                f"{row_style_prefix}{row['year']}{row_style_suffix}",
            )

        if len(rows) > len(visible_rows): table.add_row("...", "More books available", "Use ↑↓ to scroll", "", "")
    else:table.add_row("-", "No books available", "-", "-", "-")

    actions = ["Edit", "Delete", "Back"]
    action_buttons = []
    for index, action in enumerate(actions):
        if index == selected_action_index: action_buttons.append(f"[bold black on #00FFB3] {action} [/]")
        else: action_buttons.append(f"[white on #1A1A1A] {action} [/]")

    body = Table.grid(padding=(0, 0))
    query_label = query if query else "(all books)"
    body.add_row(f"[bold #00FFB3]Search[/bold #00FFB3]: [white]{query_label}[/white]")
    body.add_row(f"[dim]Showing {len(visible_rows)} of {len(rows)} result(s). Press / to search.[/dim]")
    body.add_row("")
    body.add_row(table)
    body.add_row("")
    body.add_row(Align.center("   ".join(action_buttons)))

    panel = Panel.fit(body, title="Admin · Books", border_style="#01796F", padding=(1, 1))
    console.print(Align.center(panel))
    console.print(Align.center("[dim]Press / then Enter to search | ↑↓ select book | Tab/←/→ select action | Enter confirm | q back[/dim]"))


def _show_admin_message(message: str, title: str = "Admin Books") -> None:
    console.clear()
    console.print(Panel.fit(message, title=title, border_style="#01796F"))
    console.input("Press Enter to continue...")


def _edit_book_form(book_row) -> None:
    console.clear()
    console.print(Panel.fit(f"Editing book ID {book_row['id']}", title="Edit Book", border_style="#01796F"))

    title_value = console.input(f"Title [{book_row['name']}]: ").strip() or str(book_row["name"])
    category_value = console.input(f"Category [{book_row['category']}]: ").strip() or str(book_row["category"])
    author_value = console.input(f"Author [{book_row['author']}]: ").strip() or str(book_row["author"])
    year_value = console.input(f"Year [{book_row['year']}]: ").strip() or str(book_row["year"])

    _update_book(int(book_row["id"]), title_value, category_value, author_value, year_value)
    _show_admin_message("Book updated successfully.")


def _delete_book_confirm(book_row) -> None:
    console.clear()
    title = str(book_row["name"])
    confirm = console.input(f"Delete '{title}'? (y/N): ").strip().lower()
    if confirm == "y":
        _delete_book(int(book_row["id"]))
        _show_admin_message("Book deleted successfully.")
        return
    _show_admin_message("Delete cancelled.")


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


def show_admin_books() -> None:
    selected_book_index = 0
    selected_action_index = 0
    query = ""

    while True:
        all_rows = _fetch_books_with_ids()
        rows = _search_books_for_admin(all_rows, query)
        if rows:
            selected_book_index = min(selected_book_index, len(rows) - 1)
        else:
            selected_book_index = 0

        _render_admin_books_view(rows, selected_book_index, selected_action_index, query)
        key = _read_key()

        if key == "BACK": return
        if key == "SEARCH":
            query = console.input("Search books (title/author/category/year/id, Enter for all): ").strip()
            selected_book_index = 0
        elif key == "UP" and rows: selected_book_index = (selected_book_index - 1) % len(rows)
        elif key == "DOWN" and rows: selected_book_index = (selected_book_index + 1) % len(rows)
        elif key in ("TAB", "RIGHT"): selected_action_index = (selected_action_index + 1) % 3
        elif key == "LEFT": selected_action_index = (selected_action_index - 1) % 3
        elif key == "ENTER":
            if selected_action_index == 2:
                return
            if not rows:
                _show_admin_message("There are no books to manage yet.")
                continue

            selected_book = rows[selected_book_index]
            if selected_action_index == 0:
                _edit_book_form(selected_book)
            elif selected_action_index == 1:
                _delete_book_confirm(selected_book)
