import sqlite3
import os

from .seed_books import seed_books

DB_FILE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column[1] == column_name for column in columns)


def _ensure_users_role_column(cursor) -> None:
    if not _column_exists(cursor, "users", "role"):
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")

    cursor.execute("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''")
    cursor.execute("UPDATE users SET role = 'admin' WHERE LOWER(COALESCE(job, '')) = 'admin'")


def _ensure_bootstrap_admin(cursor) -> None:
    admin_exists = cursor.execute(
        "SELECT 1 FROM users WHERE LOWER(COALESCE(role, '')) = 'admin' LIMIT 1"
    ).fetchone()

    if admin_exists:
        return

    first_user = cursor.execute(
        "SELECT id FROM users ORDER BY id LIMIT 1"
    ).fetchone()

    if first_user:
        cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (first_user[0],))

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50),
            lastname VARCHAR(20),
            username VARCHAR(10) UNIQUE,
            password VARCHAR(255),
            password_salt VARCHAR(255),
            birthday DATE,
            job VARCHAR(20),
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            offences INTEGER
        )
    """)

    _ensure_users_role_column(cursor)
    _ensure_bootstrap_admin(cursor)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(150),
            category VARCHAR(100),
            author VARCHAR(150),
            year VARCHAR(4)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS book_status (
            id_book INTEGER,
            status VARCHAR(20),
            id_user INTEGER,
            date_servive DATE,
            date_return DATE,
            FOREIGN KEY (id_book) REFERENCES books (id),
            FOREIGN KEY (id_user) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER,
            type INTEGER,
            description VARCHAR(500),
            FOREIGN KEY (id_user) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    print("Database initialized successfully.")
    # Seeds data
    seed_books(get_connection())
