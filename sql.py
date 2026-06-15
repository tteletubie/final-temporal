import sqlite3

conn = sqlite3.connect("database.db")
try:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()

    if not tables:
        print("No user tables found in the db.")

    print("\nTables shit")
    for table in tables:
        print(f"- {table[0]}")

finally:
    conn.close()
