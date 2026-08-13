from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 3. Local Modules

from database import database as db
from library.search_utils import normalize_text
from ui.key_input import read_key
from auth import credentials


console = Console()


def _fetch_users_with_ids() -> list:
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, lastname, username, password, password_salt, birthday, job, role, offences
            FROM users
            ORDER BY id
            """
        ).fetchall()
    return rows


def _update_user(user_id: int, name: str, lastname: str, username: str, password, password_salt, birthday: str, job: str, role: str) -> None:
    with db.get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET name = ?, lastname = ?, username = ?, password = ?, password_salt = ?, birthday = ?, job = ?, role = ?
            WHERE id = ?
            """,
            (name, lastname, username, password, password_salt, birthday, job, role, user_id),
        )
        conn.commit()


def _delete_user(user_id: int) -> None:
    with db.get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


def _search_users_for_admin(rows: list, query: str) -> list:
    normalized_query = normalize_text(query)
    query_tokens = normalized_query.split()

    if not query_tokens:
        return rows

    filtered_rows = []

    for row in rows:
        searchable_text = normalize_text(
            f"{row['id']} {row['name']} {row['lastname']} {row['username']} {row['password']} {row['birthday']} {row['job']} {row['role']} {row['offences']}")
        row_tokens = searchable_text.split()
        if all(any(token in row_token for row_token in row_tokens) for token in query_tokens):
            filtered_rows.append(row)
    return filtered_rows


def _admin_visible_rows(rows: list, selected_user_index: int) -> tuple[list, int]:
    max_rows = max(3, console.size.height - 20)
    if len(rows) <= max_rows:
        return rows, 0
    start = max(0, selected_user_index - (max_rows // 2))
    end = start + max_rows
    if end > len(rows):
        end = len(rows)
        start = end - max_rows
    return rows[start:end], start


def _render_admin_users_view(rows: list, selected_user_index: int, selected_action_index: int, query: str,) -> None:
    console.clear()
    table = Table(show_header=True, header_style="bold #00FFB3", box=box.SIMPLE_HEAVY, expand=True,)
    table.add_column("ID", style="white", no_wrap=True)
    table.add_column("Name", style="white", no_wrap=False)
    table.add_column("Lastname", style="white", no_wrap=False)
    table.add_column("Username", style="white", no_wrap=False)
    #table.add_column("Password", style="white", no_wrap=False)
    table.add_column("Birthday", style="white", no_wrap=False)
    table.add_column("Job", style="white", no_wrap=False)
    table.add_column("Role", style="white", no_wrap=False)
    table.add_column("Offences", style="white", no_wrap=True)

    visible_rows, start_index = _admin_visible_rows(rows, selected_user_index,)

    if rows:
        for index, row in enumerate(visible_rows):
            global_index = start_index + index
            is_selected = (global_index == selected_user_index)
            row_style_prefix = "[bold black on #00FFB3]" if is_selected else ""
            row_style_suffix = "[/]" if is_selected else ""
            table.add_row(
                f"{row_style_prefix}{row['id']}{row_style_suffix}",
                f"{row_style_prefix}{row['name']}{row_style_suffix}",
                f"{row_style_prefix}{row['lastname']}{row_style_suffix}",
                f"{row_style_prefix}{row['username']}{row_style_suffix}",
                #f"{row_style_prefix}{row['password']}{row_style_suffix}",
                f"{row_style_prefix}{row['birthday']}{row_style_suffix}",
                f"{row_style_prefix}{row['job']}{row_style_suffix}",
                f"{row_style_prefix}{row['role']}{row_style_suffix}",
                f"{row_style_prefix}{row['offences']}{row_style_suffix}",
            )

        if len(rows) > len(visible_rows):
                table.add_row("...", "More users available", "Use ↑↓ to scroll", "", "", "", "", "", "")
    else: table.add_row("-", "No users available", "-", "-", "-", "-", "-", "-", "-")

    actions = ["Edit", "Delete","Back"]
    action_buttons = []

    for index, action in enumerate(actions):
        if index == selected_action_index:
            action_buttons.append(f"[bold black on #00FFB3] {action} [/]")
        else:
            action_buttons.append(f"[white on #1A1A1A] {action} [/]")

    body = Table.grid(padding=(0, 0))
    query_label = (query if query else "(all users)")

    body.add_row(f"[bold #00FFB3]Search[/bold #00FFB3]: [white]{query_label}[/white]")
    body.add_row(f"[dim]Showing {len(visible_rows)} of {len(rows)} result(s). Press / to search.[/dim]")
    body.add_row("")
    body.add_row(table)
    body.add_row("")
    body.add_row(
        Align.center("   ".join(action_buttons)))

    panel = Panel.fit(body, title="Admin · Users", border_style="#01796F", padding=(1, 1),)
    console.print(Align.center(panel))
    console.print(Align.center("[dim] Press / then Enter to search | ↑↓ select user | Tab/←/→ select action | Enter confirm | q back [/dim]"))


def _show_admin_message(message: str, title: str = "Admin Users",) -> None:
    console.clear()
    console.print(Panel.fit(message, title=title, border_style="#01796F",))
    console.input("Press Enter to continue...")

def _edit_user_form(user_row) -> None:
    console.clear()
    console.print(Panel.fit(f"Editing user ID {user_row['id']}", title="Edit User", border_style="#01796F"))
    name_value = console.input(f"Name [{user_row['name']}]: ").strip() or user_row["name"]
    lastname_value = console.input(f"Lastname [{user_row['lastname']}]: ").strip() or user_row["lastname"]
    username_value = console.input(f"Username [{user_row['username']}]: ").strip() or user_row["username"]
    # If password left blank, preserve existing hash and salt. Otherwise hash new password.
    new_password = console.input("Password (leave blank to keep current): ").strip()
    if new_password:
        hashed_password, new_salt = credentials.hash_password(new_password)
        password_value = hashed_password
        password_salt_value = new_salt
    else:
        password_value = user_row["password"]
        # Some rows may not include password_salt (legacy); fall back to None
        password_salt_value = user_row["password_salt"] if "password_salt" in user_row.keys() else None
    birthday_value = console.input(f"Birthday [{user_row['birthday']}]: ").strip() or user_row["birthday"]
    job_value = console.input(f"Job [{user_row['job']}]: ").strip() or user_row["job"]
    role_value = console.input(f"Role [{user_row['role']}]: ").strip().lower() or user_row["role"]
    if role_value not in ("user", "admin"):
        _show_admin_message("Role must be either 'user' or 'admin'.")
        return
    _update_user(int(user_row["id"]), name_value, lastname_value, username_value, password_value, password_salt_value, birthday_value, job_value, role_value)
    _show_admin_message("User updated successfully.")


def _delete_user_confirm(user_row) -> None:
    console.clear()
    username = str(user_row["username"])
    confirm = console.input(f"Delete '{username}'? (y/N): ").strip().lower()
    if confirm == "y":
        _delete_user(int(user_row["id"]))
        _show_admin_message("User deleted successfully.")
        return
    _show_admin_message("Delete cancelled.")


def show_admin_users(current_role: str = "user") -> None:
    if str(current_role).lower() != "admin":
        _show_admin_message("Admin access required.", title="Access denied")
        return

    selected_user_index = 0
    selected_action_index = 0
    query = ""

    while True:
        all_rows = _fetch_users_with_ids()
        rows = _search_users_for_admin(all_rows, query)
        if rows:
            selected_user_index = min(selected_user_index, len(rows) - 1)
        else:
            selected_user_index = 0

        _render_admin_users_view(rows, selected_user_index, selected_action_index, query)
        key = read_key(enable_left_right=True, enable_tab=True, enable_search=True)

        if key == "BACK":
            return
        if key == "SEARCH":
            query = console.input("Search users (name/lastname/username/password/birthday/job/role/id, Enter for all): ").strip() 
            selected_user_index = 0
        elif key == "UP" and rows:
            selected_user_index = (selected_user_index - 1) % len(rows)
        elif key == "DOWN" and rows:
            selected_user_index = (selected_user_index + 1) % len(rows)
        elif key in ("TAB", "RIGHT"):
            selected_action_index = (selected_action_index + 1) % 3
        elif key == "LEFT":
            selected_action_index = (selected_action_index - 1) % 3
        elif key == "ENTER":
            if selected_action_index == 2:
                return
            if not rows:
                _show_admin_message("There are no users to manage yet.")
                continue

            selected_user = rows[selected_user_index]
            if selected_action_index == 0:
                _edit_user_form(selected_user)
            elif selected_action_index == 1:
                _delete_user_confirm(selected_user)

            selected_user_index = 0
            selected_action_index = 0
