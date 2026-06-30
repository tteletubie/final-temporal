import sqlite3
import os

from . import seed_books as seed_books

DB_FILE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

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
            offences INTEGER
        )
    """)

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
