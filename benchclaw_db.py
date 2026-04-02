"""BenchClaw — SQLite persistence layer (auth + protocol sharing)."""

import hashlib
import secrets
import sqlite3

import streamlit as st

DB_PATH = "benchclaw.db"


@st.cache_resource
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            salt     TEXT    NOT NULL,
            pw_hash  TEXT    NOT NULL,
            created  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS protocols (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            title   TEXT    NOT NULL,
            ptype   TEXT    NOT NULL,
            body    TEXT    NOT NULL,
            token   TEXT    UNIQUE NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()


def db_create_user(username: str, password: str) -> tuple:
    """Register a new user. Returns (True, None) or (False, error_msg)."""
    conn = get_db()
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    try:
        conn.execute(
            "INSERT INTO users (username, salt, pw_hash) VALUES (?, ?, ?)",
            (username, salt, pw_hash),
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Username already taken."


def db_verify_user(username: str, password: str) -> tuple:
    """Verify credentials. Returns (user_id, None) or (None, error_msg)."""
    conn = get_db()
    row = conn.execute(
        "SELECT id, salt, pw_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    if not row:
        return None, "User not found."
    pw_hash = hashlib.sha256((row["salt"] + password).encode()).hexdigest()
    if pw_hash != row["pw_hash"]:
        return None, "Incorrect password."
    return row["id"], None


def db_save_protocol(user_id: int, title: str, ptype: str, body: str) -> str:
    """Save a protocol and return its shareable token."""
    conn = get_db()
    token = secrets.token_urlsafe(12)
    conn.execute(
        "INSERT INTO protocols (user_id, title, ptype, body, token) VALUES (?, ?, ?, ?, ?)",
        (user_id, title, ptype, body, token),
    )
    conn.commit()
    return token


def db_load_by_token(token: str):
    """Load a protocol by share token. Returns a Row or None."""
    conn = get_db()
    return conn.execute(
        "SELECT * FROM protocols WHERE token = ?", (token,)
    ).fetchone()


def db_user_protocols(user_id: int) -> list:
    """Return all protocols saved by this user, newest first."""
    conn = get_db()
    return conn.execute(
        "SELECT id, title, ptype, token, created FROM protocols "
        "WHERE user_id = ? ORDER BY created DESC",
        (user_id,),
    ).fetchall()


def db_delete_protocol(protocol_id: int, user_id: int) -> bool:
    """Delete a protocol (only if owned by user_id). Returns True on success."""
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM protocols WHERE id = ? AND user_id = ?",
        (protocol_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0
