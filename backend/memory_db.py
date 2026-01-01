import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("memory.db")

class MemoryDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_prefs (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS short_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            created_at TEXT,
            expires_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            source TEXT,
            created_at TEXT
        )
        """)

        self.conn.commit()

    # ---------- USER PREFS ----------
    def set_pref(self, key, value):
        self.conn.execute(
            "REPLACE INTO user_prefs VALUES (?, ?, ?)",
            (key, value, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def get_prefs(self):
        cur = self.conn.execute("SELECT key, value FROM user_prefs")
        return {row["key"]: row["value"] for row in cur.fetchall()}

    # ---------- SHORT TERM MEMORY ----------
    def add_short_term(self, role, content, ttl_minutes=30):
        expires = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        self.conn.execute(
            "INSERT INTO short_term_memory VALUES (NULL, ?, ?, ?, ?)",
            (role, content, datetime.utcnow().isoformat(), expires.isoformat())
        )
        self.conn.commit()

    def get_short_term(self, limit=6):
        self.cleanup_short_term()
        cur = self.conn.execute("""
            SELECT role, content FROM short_term_memory
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return list(reversed(cur.fetchall()))

    def cleanup_short_term(self):
        self.conn.execute(
            "DELETE FROM short_term_memory WHERE expires_at < ?",
            (datetime.utcnow().isoformat(),)
        )
        self.conn.commit()

    # ---------- LONG TERM MEMORY ----------
    def add_long_term(self, content, source="explicit"):
        self.conn.execute(
            "INSERT INTO long_term_memory VALUES (NULL, ?, ?, ?)",
            (content, source, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def get_long_term(self, limit=10):
        cur = self.conn.execute("""
            SELECT id, content, source, created_at FROM long_term_memory
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [{"id": row["id"], "content": row["content"], "source": row["source"], "created_at": row["created_at"]} for row in cur.fetchall()]

    def delete_long_term(self, entry_id: int):
        self.conn.execute("DELETE FROM long_term_memory WHERE id = ?", (entry_id,))
        self.conn.commit()
