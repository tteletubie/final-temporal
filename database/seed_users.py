import hashlib
import secrets

def hash_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """Hashes a password using PBKDF2-HMAC-SHA256 and a secure random salt."""
    if not salt:
        salt = secrets.token_bytes(16)
    
    passwd_hash = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=password.encode('utf-8'),
        salt=salt,
        iterations=600000
    )
    return passwd_hash, salt

def seed_users(conn):
    users_data = [
        ("Admin", "System", "admin", "admin", "1980-01-01", "admin"),
        ("Alice", "Smith", "alice12", "Software", "1992-05-14", "user"),
        ("Bob", "Johnson", "bobby", "Teacher", "1985-09-22", "user"),
        ("Charlie", "Brown", "charlieb", "Student", "2000-11-03", "user"),
        ("Diana", "Prince", "diana", "Manager", "1990-12-25", "user"),
        ("Evan", "Wright", "evanw", "Engineer", "1988-07-19", "user"),
        ("Fiona", "Gallagher", "fionag", "Designer", "1995-03-30", "user"),
        ("George", "Costanza", "georgec", "Architect", "1969-05-22", "user"),
        ("Hannah", "Abbott", "hannah", "Nurse", "1993-08-11", "user"),
        ("Ian", "Malcolm", "ianm", "Mathematician", "1975-04-15", "user"),
        ("Julia", "Roberts", "juliar", "Actor", "1967-10-28", "user"),
    ]

    with conn:
        cursor = conn.cursor()
        before = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

        for name, lastname, username, job, birthday, role in users_data:
            # Everyone gets 'bookworm' as their password
            pwd_hash, salt = hash_password("bookworm")
            
            cursor.execute(
                """
                INSERT INTO users (name, lastname, username, password, password_salt, birthday, job, role, offences)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, 0
                WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = ?)
                """, 
                (name, lastname, username, pwd_hash, salt, birthday, job, role, username)
            )

        conn.commit()
        after = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    print(f"Users added: {after - before}")
    print(f"Total users: {after}")

if __name__ == '__main__':
    from database import get_connection
    seed_users(get_connection())