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
# Every validate_* function returns a tuple (is_valid: bool, error_message: str).
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


def validate_required(value: str, field_label: str = "Field") -> tuple[bool, str]:
    """Generic 'not empty' check, used for simple required fields (e.g. Login)."""
    if not value or not value.strip():
        return False, f"{field_label} cannot be empty."
    return True, ""


def validate_name(name: str, field_label: str = "Name", max_len: int = NAME_MAX_LEN) -> tuple[bool, str]:
    """Validate a person's first name: not empty, no numbers,
    at least 2 characters, spaces allowed."""
    name = name.strip()

    if not name:
        return False, f"{field_label} cannot be empty."
    if len(name) < NAME_MIN_LEN:
        return False, f"{field_label} must have at least {NAME_MIN_LEN} characters."
    if len(name) > max_len:
        return False, f"{field_label} must not exceed {max_len} characters."
    if not _NAME_REGEX.match(name):
        return False, f"{field_label} can only contain letters and single spaces between words."

    return True, ""


def validate_lastname(lastname: str) -> tuple[bool, str]:
    """Validate a person's lastname. Uses the same rules as validate_name
    but with the shorter max length defined by the lastname column."""
    return validate_name(lastname, field_label="Lastname", max_len=LASTNAME_MAX_LEN)


def validate_username(username: str) -> tuple[bool, str]:
    """Validate the format of a username: not empty, 4-20 characters,
    no spaces. Uniqueness is checked separately via username_exists()."""
    if not username or not username.strip():
        return False, "Username cannot be empty."
    if len(username) < USERNAME_MIN_LEN:
        return False, f"Username must have at least {USERNAME_MIN_LEN} characters."
    if len(username) > USERNAME_MAX_LEN:
        return False, f"Username must not exceed {USERNAME_MAX_LEN} characters."
    if " " in username:
        return False, "Username cannot contain spaces."

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength: 8-16 characters, at least one
    uppercase, one lowercase, one number and one special character."""
    if not password:
        return False, "Password cannot be empty."
    if " " in password:
        return False, "Password cannot contain spaces."
    if len(password) < PASSWORD_MIN_LEN:
        return False, f"Password must have at least {PASSWORD_MIN_LEN} characters."
    if len(password) > PASSWORD_MAX_LEN:
        return False, f"Password must not exceed {PASSWORD_MAX_LEN} characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not _SPECIAL_CHARS_REGEX.search(password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)."

    return True, ""


def validate_passwords_match(password: str, confirm_password: str) -> tuple[bool, str]:
    """Check that the password confirmation matches the original password."""
    if password != confirm_password:
        return False, "Passwords do not match."
    return True, ""


def validate_birthday(birthday: str, date_format: str = "%Y-%m-%d") -> tuple[bool, str]:
    """Validate a date of birth: not empty, correct format, not in the
    future, and not before MIN_BIRTH_YEAR."""
    if not birthday or not birthday.strip():
        return False, "Date of birth cannot be empty."

    try:
        birth_date = datetime.strptime(birthday, date_format).date()
    except (ValueError, TypeError):
        return False, "Invalid date format."

    today = date.today()

    if birth_date > today:
        return False, "Date of birth cannot be in the future."
    if birth_date.year < MIN_BIRTH_YEAR:
        return False, f"Date of birth cannot be before {MIN_BIRTH_YEAR}."

    return True, ""

def _ask_required(prompt_text: str, field_type: str = "text") -> str:
    """Keep asking until the user actually types something."""
    while True:
        value = visuals.input(prompt_text, field_type)
        valid, message = validate_required(value, prompt_text)
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
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

    if user and verify_password(user[4], user[5], password):
        return username

    # Deliberately generic: never reveal whether it was the username or the
    # password that was wrong.
    visuals.error("Invalid username or password")
    console.input("\n[dim]Press Enter to continue...[/dim]")
    return False
def _ask_name() -> str:
    while True:
        name = visuals.input("Name").strip()
        valid, message = validate_name(name)
        if valid:
            return name.lower()
        visuals.error(message)


def _ask_lastname() -> str:
    while True:
        lastname = visuals.input("Lastname").strip()
        valid, message = validate_lastname(lastname)
        if valid:
            return lastname.lower()
        visuals.error(message)


def _ask_username() -> str:
    while True:
        username = visuals.input("Username").strip()
        valid, message = validate_username(username)
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
        valid, message = validate_password(password)
        if not valid:
            visuals.error(message)
            continue

        confirm_password = visuals.input("Confirm Password", "password")
        match, message = validate_passwords_match(password, confirm_password)
        if not match:
            visuals.error(message)
            continue

        return password


def _ask_birthday() -> str:
    while True:
        birthday = visuals.enter_date("Date of Birth")
        valid, message = validate_birthday(birthday)
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
            cursor.execute(
                "INSERT INTO users (name, lastname, username, password, password_salt, birthday, job, offences) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, lastname, username, hashed_password, password_salt, birthday, job, offences),
            )
            conn.commit()

        visuals.exit("Account created successfully! You can now log in.")
        return login()


def logout():
    pass


def authenticate(username, password):
    pass


def get_user_role(id_user):
    pass


def create_account():
    pass


def username_exists(username: str) -> bool:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
