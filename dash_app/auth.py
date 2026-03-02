"""
KLIQ Dashboard Authentication for Dash
Uses Flask-Login for session management.
SQLite backend (same schema as Streamlit version).
"""

import os
import sqlite3
import hashlib
import secrets
import datetime

DB_PATH = os.environ.get(
    "AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "users.db")
)
ADMIN_EMAILS = [
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "ben@joinkliq.io").split(",")
]
APPROVED_EMAILS = [
    e.strip().lower()
    for e in os.environ.get("APPROVED_EMAILS", "will@joinkliq.io").split(",")
    if e.strip()
]

SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Bootstrap admin accounts
    for admin_email in ADMIN_EMAILS:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (admin_email,)
        ).fetchone()
        if not exists:
            salt = secrets.token_hex(16)
            pw_hash = _hash_password(
                os.environ.get("ADMIN_DEFAULT_PASSWORD", "KLIQ3055!54321"), salt
            )
            conn.execute(
                "INSERT INTO users (email, password_hash, salt, full_name, status) "
                "VALUES (?, ?, ?, ?, 'approved')",
                (admin_email, pw_hash, salt, admin_email.split("@")[0].title()),
            )
    conn.commit()

    # Auto-approve pre-approved emails
    for approved_email in APPROVED_EMAILS:
        row = conn.execute(
            "SELECT status FROM users WHERE email = ?", (approved_email,)
        ).fetchone()
        if row and row[0] != "approved":
            conn.execute(
                "UPDATE users SET status = 'approved' WHERE email = ?",
                (approved_email,),
            )
    conn.commit()
    return conn


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()


def authenticate(email, password):
    """Returns (success, status, full_name)."""
    conn = _get_db()
    email = email.strip().lower()
    row = conn.execute(
        "SELECT password_hash, salt, status, full_name FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()
    if not row:
        return False, "", ""
    password_hash, salt, status, full_name = row
    if _hash_password(password, salt) != password_hash:
        return False, "", ""
    return True, status, full_name


def register_user(email, password, full_name):
    conn = _get_db()
    email = email.strip().lower()
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    status = "approved" if email in ADMIN_EMAILS or email in APPROVED_EMAILS else "pending"
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, salt, full_name, status) VALUES (?, ?, ?, ?, ?)",
            (email, password_hash, salt, full_name, status),
        )
        conn.commit()
        return True, "Account created!" if status == "approved" else "Registration submitted. Awaiting admin approval."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()


def is_admin(email):
    return email.strip().lower() in ADMIN_EMAILS


def get_pending_users():
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, email, full_name, created_at FROM users WHERE status = 'pending' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [{"id": r[0], "email": r[1], "full_name": r[2], "created_at": r[3]} for r in rows]


def get_all_users():
    conn = _get_db()
    rows = conn.execute(
        "SELECT id, email, full_name, status, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "email": r[1], "full_name": r[2], "status": r[3], "created_at": r[4]}
        for r in rows
    ]


def update_user_status(user_id, status):
    conn = _get_db()
    conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = _get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
