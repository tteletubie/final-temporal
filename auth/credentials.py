# 1. Standard Libraries
import os
import hashlib
import hmac

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

def login():
    console.clear()
    console.print(Align.center(Panel(Align.center("[bold green]Enter your credentials[/bold green]"), title="[bold #00FFB3]Login[/bold #00FFB3]", border_style="#00FFB3",width=50)))

    username = visuals.input("Username")
    password = visuals.input("Password", "password")    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            return username if verify_password(user[4], user[5], password) else False


def sign_up():
    while True:
        console.clear()
        #console.print("[#7FFFD4]Library Management System[/#7FFFD4]")
        console.print(Align.center(Panel(Align.center("[bold green]Create an account[/bold green]"), title="[bold #00FFB3]Sign Up[/bold #00FFB3]", border_style="#00FFB3",width=50)))

        name = visuals.input("Name").lower()
        lastname = visuals.input("Lastname").lower()
        username = visuals.input("Username").lower()
        password = visuals.input("Password", "password")
        birthday = visuals.enter_date("Date of Birth")
        job = "user"
        offences = 0
        password, password_salt = hash_password(password)

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, lastname, username, password, password_salt, birthday, job, offences) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, lastname, username, password, password_salt, birthday, job, offences),
            )
            conn.commit()

        return login()


def logout():
    pass


def authenticate(username, password):
    pass


def get_user_role(id_user):
    pass


def create_account():
    pass


def username_exists(username):
    pass
