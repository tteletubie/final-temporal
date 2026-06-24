# 1. Standard Libraries
import os
import hashlib
import sqlite3

# 2. Third-Party Libraries
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# 3. Local Modules
from database import database as db
from ui import visuals

console = Console()


def login():
    console.clear()
    console.print(
        Align.center(
            Panel(
                Align.center("[bold green]Enter your credentials[/bold green]"),
                title="[bold #00FFB3]Login[/bold #00FFB3]",
                border_style="#00FFB3",
                width=50,
            )
        )
    )

    username = visuals.input("Username")
    password = visuals.input("Password", "password")

    # password = hash_password(password)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Parametrized query avoids SQL injection attacks
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        user = cursor.fetchone()
        return username if user else False


def login_u():
    while True:
        visuals.show_login()

        name = visuals.input("Name").lower()
        lastname = visuals.input("Lastname").lower()
        username = visuals.input("Username").lower()
        password = visuals.input("Password")
        birthday = visuals.enter_date("Date of Birth")
        job = "user"
        offences = 0

        user = {
            "name": name,
            "lastname": lastname,
            "username": username,
            "password": password,
            "birth": birthday,
            "job": job,
            "offences": offences,
        }

        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (name, lastname, username, password, birthday, job, offences) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, lastname, username, password, birthday, job, offences),
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
