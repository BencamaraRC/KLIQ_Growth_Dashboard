"""
SQLite tracker: records which messages have been sent to which prospects,
so we never double-send.
"""

import sqlite3
from datetime import datetime
from config import DB_PATH


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            sequence_step TEXT NOT NULL,
            channel TEXT NOT NULL,          -- 'sms' or 'email'
            recipient TEXT NOT NULL,        -- phone or email
            sent_at TEXT NOT NULL,
            status TEXT DEFAULT 'sent',
            message_id TEXT,                -- external ID from Twilio/SendGrid
            UNIQUE(application_id, sequence_step, channel)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            application_id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            coach_type TEXT,
            country TEXT,
            signup_date TEXT,
            profile_json TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    return conn


def already_sent(application_id, sequence_step, channel):
    """Check if a message was already sent for this prospect + step + channel."""
    conn = _get_db()
    row = conn.execute(
        "SELECT 1 FROM sent_messages WHERE application_id=? AND sequence_step=? AND channel=?",
        (application_id, sequence_step, channel),
    ).fetchone()
    conn.close()
    return row is not None


def record_sent(application_id, sequence_step, channel, recipient, message_id=None):
    """Record that a message was sent."""
    conn = _get_db()
    conn.execute(
        """INSERT OR IGNORE INTO sent_messages
           (application_id, sequence_step, channel, recipient, sent_at, message_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (application_id, sequence_step, channel, recipient, datetime.utcnow().isoformat(), message_id),
    )
    conn.commit()
    conn.close()


def upsert_prospect(application_id, name=None, email=None, phone=None,
                     coach_type=None, country=None, signup_date=None, profile_json=None):
    """Insert or update a prospect record."""
    conn = _get_db()
    conn.execute(
        """INSERT INTO prospects (application_id, name, email, phone, coach_type, country, signup_date, profile_json, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(application_id) DO UPDATE SET
               name = COALESCE(excluded.name, prospects.name),
               email = COALESCE(excluded.email, prospects.email),
               phone = COALESCE(excluded.phone, prospects.phone),
               coach_type = COALESCE(excluded.coach_type, prospects.coach_type),
               country = COALESCE(excluded.country, prospects.country),
               signup_date = COALESCE(excluded.signup_date, prospects.signup_date),
               profile_json = COALESCE(excluded.profile_json, prospects.profile_json),
               updated_at = excluded.updated_at""",
        (application_id, name, email, phone, coach_type, country, signup_date, profile_json, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_prospect(application_id):
    """Retrieve a prospect record."""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM prospects WHERE application_id=?", (application_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_prospects():
    """Retrieve all prospect records."""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM prospects ORDER BY signup_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sent_history(application_id=None):
    """Retrieve sent message history, optionally filtered by prospect."""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    if application_id:
        rows = conn.execute(
            "SELECT * FROM sent_messages WHERE application_id=? ORDER BY sent_at DESC",
            (application_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sent_messages ORDER BY sent_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
