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
from datetime import date, timedelta
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
        return conn.execute(
            """
            SELECT
                b.id,
                b.name,
                b.category,
                b.author,
                b.year,
                b.borrow_count,
                bs.id_user,
                bs.status
            FROM books b
            LEFT JOIN book_status bs
                ON b.id = bs.id_book
            ORDER BY b.name, b.author, b.year
            """
        ).fetchall()

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
    selected_action_index: int,
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
    table.add_column("Borrowed", style="white", no_wrap=True)

    if rows:
        for index, row in enumerate(visible_rows):
            global_index = start_index + index
            prefix = "[bold black on #00FFB3]" if global_index == selected_index else ""
            suffix = "[/]" if global_index == selected_index else ""
            table.add_row(f"{prefix}{row['name']}{suffix}", f"{prefix}{row['category']}{suffix}", f"{prefix}{row['author']}{suffix}", f"{prefix}{row['year']}{suffix}", f"{prefix}{row['borrow_count']}{suffix}")
        if len(rows) > len(visible_rows):
            table.add_row("...", "More books available", "Use ↑↓ to scroll", "")
    else:
        table.add_row("No books found", "-", "-", "-")

    if rows and str(rows[selected_index]["status"]).lower() == "borrowed":
        actions = ["Unborrow Book", "Back"]
    else:
        actions = ["Borrow", "Back"]

    selected_action_index = min(selected_action_index, len(actions) - 1)
    action_buttons = []
    for index, action in enumerate(actions):
        action_buttons.append(f"[bold black on #00FFB3] {action} [/]" if index == selected_action_index else f"[white on #1A1A1A] {action} [/]")

    body = Table.grid(padding=(0, 0))
    body.add_row(table)
    body.add_row("")
    body.add_row(Align.center("   ".join(action_buttons)))
    console.print(Align.center(Panel.fit(body, border_style="#01796F", box=box.ROUNDED, padding=(0, 1))))
    console.print(Align.center("[dim]Press / to search | ↑↓ select book | Tab/←/→ select action | Enter confirm | q back[/dim]"))

def _browse_books(
    title: str,
    query_label: str,
    default_hint: str,
    search_fn,
    username: str | None = None,
) -> None:
    query = ""
    selected_index = 0
    selected_action_index = 0

    while True:
        rows = _fetch_books() if not query else search_fn(query)
        selected_index = min(selected_index, len(rows) - 1) if rows else 0

        if rows and str(rows[selected_index]["status"]).lower() == "borrowed":
            actions = ["Unborrow Book", "Back"]
        else:
            actions = ["Borrow", "Back"]

        selected_action_index = min(selected_action_index, len(actions) - 1)
        _render_normal_books_view(title, query_label, query, rows, selected_index, selected_action_index, default_hint)
        key = _read_key()

        if key == "BACK":
            return
        if key == "SEARCH":
            query = console.input("Search (Enter for all books): ").strip()
            selected_index = 0
            selected_action_index = 0
            continue
        if key == "UP" and rows:
            selected_index = (selected_index - 1) % len(rows)
            selected_action_index = 0
            continue
        if key == "DOWN" and rows:
            selected_index = (selected_index + 1) % len(rows)
            selected_action_index = 0
            continue
        if key in ("TAB", "RIGHT"):
            selected_action_index = (selected_action_index + 1) % len(actions)
            continue
        if key == "LEFT":
            selected_action_index = (selected_action_index - 1) % len(actions)
            continue
        if key == "ENTER":
            if selected_action_index == 1:
                return
            if not rows:
                _show_admin_message("There are no books available.", title="Books")
                continue

            selected_book = rows[selected_index]

            if str(selected_book["status"]).lower() == "borrowed":
                _unborrow_book_confirm(selected_book)
            else:
                if not username:
                    _show_admin_message("You must be logged in to borrow a book.", title="Borrow")
                    continue
                _borrow_book_confirm(selected_book, username)

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


def show_category(username: str | None = None) -> None:
    _browse_books(
        "Search by Category",
        "Search by category:",
        "Use / to search categories.",
        _search_books_by_category,
        username,
    )


def show_title(username: str | None = None) -> None:
    _browse_books(
        "Title Search",
        "Search by title:",
        "Use / to search titles.",
        _search_books_by_title,
        username,
    )


def show_author(username: str | None = None) -> None:
    _browse_books(
        "Author Search",
        "Search by author:",
        "Use / to search authors.",
        _search_books_by_author,
        username,
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
            SELECT
                books.id,
                books.name,
                books.category,
                books.author,
                books.year,
                COALESCE(book_status.status, 'available') AS status,
                book_status.id_user
            FROM books
            LEFT JOIN book_status
                ON book_status.id_book = books.id
            ORDER BY books.name, books.author, books.year
            """
        ).fetchall()

    return rows

def _get_user_id(username):
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    return row["id"] if row else None


def _get_book_status(book_id: int):
    with db.get_connection() as conn:
        row = conn.execute("SELECT id_book, status, id_user, date_servive, date_return, date_due FROM book_status WHERE id_book = ?", (book_id,)).fetchone()
    return row


def _borrow_book(book_id: int, username: str) -> tuple[bool, str]:
    user_id = _get_user_id(username)
    if user_id is None:
        return False, "You must be logged in to borrow a book."
    with db.get_connection() as conn:
        book = conn.execute("SELECT id, name FROM books WHERE id = ?", (book_id,)).fetchone()
        if book is None:
            return False, "Book not found."
        status = conn.execute("SELECT status, id_user FROM book_status WHERE id_book = ?", (book_id,)).fetchone()
        if status and status["status"] == "borrowed":
            return False, "This book is currently borrowed."
        today = date.today().isoformat()
        # default due date: 14 days from today
        due_date = (date.today() + timedelta(days=14)).isoformat()
        conn.execute("UPDATE books SET borrow_count = borrow_count + 1 WHERE id = ?", (book_id,))
        if status is None:
            conn.execute("INSERT INTO book_status(id_book, status, id_user, date_servive, date_return, date_due) VALUES (?, ?, ?, ?, NULL, ?)", (book_id, "borrowed", user_id, today, due_date))
        else:
            conn.execute("UPDATE book_status SET status = ?, id_user = ?, date_servive = ?, date_return = NULL, date_due = ? WHERE id_book = ?", ("borrowed", user_id, today, due_date, book_id))
        conn.commit()

    return True, f"'{book['name']}' borrowed successfully."


def _borrow_book_confirm(book_row, username: str) -> None:
    console.clear()
    title = str(book_row["name"])
    panel = Panel.fit(f"Borrow [bold #00FFB3]{title}[/bold #00FFB3]?", title="Borrow Book", border_style="#01796F")
    console.print(Align.center(panel))
    confirm = console.input("\nBorrow this book? (y/N): ").strip().lower()
    if confirm != "y":
        console.print(Align.center("[dim]Borrow cancelled.[/dim]"))
        console.input("\nPress Enter to continue...")
        return
    success, message = _borrow_book(int(book_row["id"]), username)
    if success:
        console.print(
            Align.center(
                f"[bold #00FFB3]{message}[/bold #00FFB3]"
            )
        )
    else:
        console.print(
            Align.center(
                f"[bold red]{message}[/bold red]"
            )
        )

    console.input("\nPress Enter to continue...")

def _unborrow_book(book_id: int) -> tuple[bool, str]:
    try:
        with db.get_connection() as conn:
            row = conn.execute("SELECT status FROM book_status WHERE id_book = ?", (book_id,)).fetchone()
            if not row or str(row["status"]).lower() != "borrowed":
                return False, "This book is already available."
            
            conn.execute(
                "UPDATE books SET borrow_count = CASE WHEN borrow_count > 0 THEN borrow_count - 1 ELSE 0 END WHERE id = ?",
                (book_id,)
            )

            today = date.today().isoformat()
            conn.execute(
                """
                UPDATE book_status
                SET status = 'available',
                    id_user = NULL,
                    date_servive = NULL,
                    date_return = ?,
                    date_due = NULL
                WHERE id_book = ?
                """,
                (today, book_id)
            )

            conn.commit()

        return True, "The book is now available."

    except Exception as e:
        return False, f"Could not unborrow the book: {e}"

def _show_book_message(
    message: str,
    title: str = "Books"
) -> None:
    console.clear()

    console.print(
        Align.center(
            Panel.fit(
                message,
                title=title,
                border_style="#01796F"
            )
        )
    )

    console.print()

    console.print(
        Align.center(
            "[dim]Press Enter to continue...[/dim]"
        )
    )

    console.input()

def _unborrow_book_confirm(book_row) -> None:
    console.clear()

    title = str(book_row["name"])

    console.print(
        Panel.fit(
            f"[white]This book is currently borrowed:[/white]\n\n"
            f"[bold #00FFB3]{title}[/bold #00FFB3]",
            title="Borrowed Book",
            border_style="#01796F",
        )
    )

    console.print()

    actions = ["Unborrow Book", "Back"]
    selected_action = 0

    while True:
        buttons = []

        for index, action in enumerate(actions):
            if index == selected_action:
                buttons.append(
                    f"[bold black on #00FFB3] {action} [/]"
                )
            else:
                buttons.append(
                    f"[white on #1A1A1A] {action} [/]"
                )

        console.print(
            Align.center("   ".join(buttons))
        )

        key = _read_key()

        if key in ("BACK",):
            return

        if key in ("LEFT", "UP"):
            selected_action = (selected_action - 1) % len(actions)

        elif key in ("RIGHT", "DOWN", "TAB"):
            selected_action = (selected_action + 1) % len(actions)

        elif key == "ENTER":

            if selected_action == 1:
                return
            if selected_action == 0:

                success, message = _unborrow_book(
                    int(book_row["id"])
                )

                if success:
                    _show_book_message(
                        message,
                        title="Book Available"
                    )
                else:
                    _show_book_message(
                        message,
                        title="Unborrow"
                    )

                return

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

def _add_book(name: str, category: str, author: str, year: str) -> None:
    with db.get_connection() as conn:
        conn.execute("INSERT INTO books(name, category, author, year) VALUES (?, ?, ?, ?)", (name, category, author, year),)
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

    actions = ["Edit", "Delete", "Add Book", "Dashboard", "Back"]
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


def _add_book_form() -> None:
    console.clear()
    console.print(Panel.fit("Create a new book", title="Add Book", border_style="#01796F"))
    name = console.input("Title: ").strip()
    category = console.input("Category: ").strip()
    author = console.input("Author: ").strip()
    year = console.input("Year: ").strip()
    if not name:
        _show_admin_message("Title is required.", title="Add Book")
        return
    if not year:
        _show_admin_message("Year is required.", title="Add Book")
        return
    _add_book(name, category, author, year)
    _show_admin_message("Book added successfully.", title="Add Book")

def _delete_book_confirm(book_row) -> None:
    console.clear()
    title = str(book_row["name"])
    confirm = console.input(f"Delete '{title}'? (y/N): ").strip().lower()
    if confirm == "y":
        _delete_book(int(book_row["id"]))
        _show_admin_message("Book deleted successfully.")
        return
    _show_admin_message("Delete cancelled.")


def _admin_dashboard() -> None:
    console.clear()
    rows = db.get_connection().execute(
        """
        SELECT b.id, b.name, COALESCE(bs.status, 'available') AS status, u.username, bs.date_servive, bs.date_due, bs.date_return
        FROM books b
        LEFT JOIN book_status bs ON bs.id_book = b.id
        LEFT JOIN users u ON u.id = bs.id_user
        WHERE bs.status = 'borrowed'
        ORDER BY bs.date_due IS NULL, bs.date_due
        """
    ).fetchall()

    table = Table(show_header=True, header_style="bold #00FFB3", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("ID", style="white", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Borrower", style="white")
    table.add_column("Borrowed", style="white")
    table.add_column("Due", style="white")
    table.add_column("Overdue", style="white")

    today = date.today()
    if rows:
        for row in rows:
            due = row[5]
            overdue = "No"
            if due:
                try:
                    due_date = date.fromisoformat(due)
                    overdue = "Yes" if today > due_date else "No"
                except Exception:
                    overdue = "Unknown"

            table.add_row(str(row[0]), str(row[1]), str(row[3] or "-"), str(row[4] or "-"), str(due or "-"), overdue)
    else:
        table.add_row("-", "No borrowed books", "-", "-", "-", "-")

    console.print(Align.center(Panel.fit(table, title="Admin Dashboard · Borrowed Books", border_style="#01796F")))
    console.print(Align.center("[dim]Press b to go back[/dim]"))

    try:
        if os.name == "nt":
            import msvcrt
            while True:
                ch = msvcrt.getwch()
                if ch.lower() == "b":
                    return
        else:
            if not sys.stdin.isatty():
                console.input("Press Enter to continue...")
                return

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if not ch:
                        continue
                    if ch.lower() == "b":
                        return
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        console.input("Press Enter to continue...")


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


def show_admin_books(current_role: str = "user") -> None:
    if str(current_role).lower() != "admin":
        _show_admin_message("Admin access required.", title="Access denied")
        return

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
        if key in ("d", "D"):
            _export_all_borrowed_pdf()
            continue
        if key in ("p", "P") and rows:
            selected_book = rows[selected_book_index]
            _export_book_pdf(selected_book)
            continue
        if key == "SEARCH":
            query = console.input("Search books (title/author/category/year/id, Enter for all): ").strip()
            selected_book_index = 0
        elif key == "UP" and rows: selected_book_index = (selected_book_index - 1) % len(rows)
        elif key == "DOWN" and rows: selected_book_index = (selected_book_index + 1) % len(rows)
        elif key in ("TAB", "RIGHT"): selected_action_index = (selected_action_index + 1) % 5
        elif key == "LEFT": selected_action_index = (selected_action_index - 1) % 5
        elif key == "ENTER":
            if selected_action_index == 4:
                return
            if not rows:
                _show_admin_message("There are no books to manage yet.")
                continue

            selected_book = rows[selected_book_index]
            if selected_action_index == 0:
                _edit_book_form(selected_book)
            elif selected_action_index == 1:
                _delete_book_confirm(selected_book)
            elif selected_action_index == 2:
                _add_book_form()
            elif selected_action_index == 3:
                _admin_dashboard()
