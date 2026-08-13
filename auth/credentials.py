# 1. Standard Libraries
import os
import hashlib
import hmac
import re
from datetime import date, datetime

# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# 3. Local Modules
from database import database as db
from ui import visuals

console = Console()


# Hash password functions
def hash_password(password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)     
    hashed = hashlib.pbkdf2_hmac(
        hash_name = 'sha256',
        password = password.encode('utf-8'),
        salt = salt,
        iterations = 600000
    )
    return hashed, salt

def verify_password(stored_hash: bytes, stored_salt: bytes, input_password: str) -> bool:
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("latin-1")
    if isinstance(stored_salt, str):
        stored_salt = stored_salt.encode("latin-1")

    new_hash = hashlib.pbkdf2_hmac(
        hash_name = 'sha256',
        password = input_password.encode('utf-8'),
        salt = stored_salt,
        iterations=600000
    )
    return hmac.compare_digest(stored_hash, new_hash)
# =========================================================================
# VALIDATION FUNCTIONS
# =========================================================================
# validate_field() returns a tuple (is_valid: bool, error_message: str).
# error_message is "" when is_valid is True.

NAME_MIN_LEN = 2
NAME_MAX_LEN = 50
LASTNAME_MAX_LEN = 20

USERNAME_MIN_LEN = 4
USERNAME_MAX_LEN = 20

PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 16

MIN_BIRTH_YEAR = 1900  # reject unrealistically old dates of birth

# Letters (with Spanish accents/ñ) and single spaces between words, e.g. "Maria Jose"
_NAME_REGEX = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+(?: [A-Za-zÁÉÍÓÚáéíóúÑñÜü]+)*$")

_SPECIAL_CHARS_REGEX = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:,.<>?/|~]")


def validate_field(
    validation_type: str,
    value: str,
    field_label: str = "Field",
    *,
    max_len: int | None = None,
    confirm_value: str | None = None,
    date_format: str = "%Y-%m-%d",
) -> tuple[bool, str]:
    """Validate a value by type.

    Supported validation_type values:
    required, name, lastname, username, password, password_match, birthday.
    """
    kind = validation_type.strip().lower()

    match kind:
        case "required":
            if not value or not value.strip(): return False, f"{field_label} cannot be empty."
            return True, ""

        case "name" | "lastname":
            trimmed_value = value.strip()
            limit = max_len if max_len is not None else (LASTNAME_MAX_LEN if kind == "lastname" else NAME_MAX_LEN)

            if not trimmed_value: return False, f"{field_label} cannot be empty."
            if len(trimmed_value) < NAME_MIN_LEN: return False, f"{field_label} must have at least {NAME_MIN_LEN} characters."
            if len(trimmed_value) > limit: return False, f"{field_label} must not exceed {limit} characters."
            if not _NAME_REGEX.match(trimmed_value): return False, f"{field_label} can only contain letters and single spaces between words."

            return True, ""

        case "username":
            if not value or not value.strip(): return False, "Username cannot be empty."
            if len(value) < USERNAME_MIN_LEN: return False, f"Username must have at least {USERNAME_MIN_LEN} characters."
            if len(value) > USERNAME_MAX_LEN: return False, f"Username must not exceed {USERNAME_MAX_LEN} characters."
            if " " in value: return False, "Username cannot contain spaces."

            return True, ""

        case "password":
            if not value: return False, "Password cannot be empty."
            if " " in value: return False, "Password cannot contain spaces."
            if len(value) < PASSWORD_MIN_LEN: return False, f"Password must have at least {PASSWORD_MIN_LEN} characters."
            if len(value) > PASSWORD_MAX_LEN: return False, f"Password must not exceed {PASSWORD_MAX_LEN} characters."
            if not re.search(r"[A-Z]", value): return False, "Password must contain at least one uppercase letter."
            if not re.search(r"[a-z]", value): return False, "Password must contain at least one lowercase letter."
            if not re.search(r"[0-9]", value): return False, "Password must contain at least one number."
            if not _SPECIAL_CHARS_REGEX.search(value):return False, "Password must contain at least one special character (!@#$%^&* etc.)."

            return True, ""

        case "password_match":
            if confirm_value is None:return False, "Confirmation value is required."
            if value != confirm_value: return False, "Passwords do not match."
            return True, ""

        case "birthday":
            if not value or not value.strip(): return False, f"{field_label} cannot be empty."

            try:
                birth_date = datetime.strptime(value, date_format).date()
            except (ValueError, TypeError):
                return False, "Invalid date format."

            today = date.today()

            if birth_date > today: return False, f"{field_label} cannot be in the future."
            if birth_date.year < MIN_BIRTH_YEAR:return False, f"{field_label} cannot be before {MIN_BIRTH_YEAR}."

            return True, ""

        case _:
            return False, f"Unknown validation type: {validation_type}"

def _ask_required(prompt_text: str, field_type: str = "text") -> str:
    """Keep asking until the user actually types something."""
    while True:
        value = visuals.input(prompt_text, field_type)
        valid, message = validate_field("required", value, prompt_text)
        if valid:
            return value
        visuals.error(message)


def login():
    console.clear()
    console.print(Align.center(Panel(Align.center("[bold green]Enter your credentials[/bold green]"), title="[bold #00FFB3]Login[/bold #00FFB3]", border_style="#00FFB3",width=50)))

    username = _ask_required("Username").strip().lower()
    password = _ask_required("Password", "password")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, password, password_salt FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

    if user and verify_password(user[3], user[4], password):
        return {
            "id": int(user[0]),
            "username": str(user[1]),
            "role": str(user[2] or "user").lower(),
        }

    # Deliberately generic: never reveal whether it was the username or the
    # password that was wrong.
    visuals.error("Invalid username or password")
    console.input("\n[dim]Press Enter to continue...[/dim]")
    return False
def _ask_name() -> str:
    while True:
        name = visuals.input("Name").strip()
        valid, message = validate_field("name", name, "Name")
        if valid:
            return name.lower()
        visuals.error(message)


def _ask_lastname() -> str:
    while True:
        lastname = visuals.input("Lastname").strip()
        valid, message = validate_field("lastname", lastname, "Lastname", max_len=LASTNAME_MAX_LEN)
        if valid:
            return lastname.lower()
        visuals.error(message)


def _ask_username() -> str:
    while True:
        username = visuals.input("Username").strip()
        valid, message = validate_field("username", username, "Username")
        if not valid:
            visuals.error(message)
            continue

        username = username.lower()
        if username_exists(username):
            visuals.error("That username is already taken. Please choose a different one.")
            continue

        return username


def _ask_password() -> str:
    while True:
        password = visuals.input("Password", "password")
        valid, message = validate_field("password", password, "Password")
        if not valid:
            visuals.error(message)
            continue

        confirm_password = visuals.input("Confirm Password", "password")
        match, message = validate_field("password_match", confirm_password, "Confirm Password", confirm_value=password)
        if not match:
            visuals.error(message)
            continue

        return password


def _ask_birthday() -> str:
    while True:
        birthday = visuals.enter_date("Date of Birth")
        valid, message = validate_field("birthday", birthday, "Date of Birth")
        if valid:
            return birthday
        visuals.error(message)

def sign_up():
    while True:
        console.clear()
        #console.print("[#7FFFD4]Library Management System[/#7FFFD4]")
        console.print(Align.center(Panel(Align.center("[bold green]Create an account[/bold green]"), title="[bold #00FFB3]Sign Up[/bold #00FFB3]", border_style="#00FFB3",width=50)))

        name = _ask_name()
        lastname = _ask_lastname()
        username = _ask_username()
        password = _ask_password()
        birthday = _ask_birthday()
        job = "user"
        offences = 0
        hashed_password, password_salt = hash_password(password)

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users LIMIT 1")
            has_users = cursor.fetchone() is not None

        role = "user" if has_users else "admin"

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, lastname, username, password, password_salt, birthday, job, role, offences) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, lastname, username, hashed_password, password_salt, birthday, job, role, offences),
            )
            conn.commit()

        visuals.exit("Account created successfully! You can now log in.")
        return login()


def logout():
    pass


def authenticate(username, password):
    pass


def get_user_role(id_user):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (id_user,))
        user = cursor.fetchone()
        if not user:
            return None
        return str(user[0] or "user").lower()


def create_account():
    return sign_up()


def username_exists(username: str) -> bool:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
