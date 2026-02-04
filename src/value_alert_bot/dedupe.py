from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


@dataclass(frozen=True)
class DedupeItem:
    hash_value: str
    created_at: str


def _ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            hash TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def build_hash(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


class DedupeStore:
    def __init__(self, db_path: str, ttl_hours: int) -> None:
        self.db_path = db_path
        self.ttl_hours = ttl_hours

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def purge(self) -> None:
        cutoff = datetime.utcnow() - timedelta(hours=self.ttl_hours)
        cutoff_iso = cutoff.replace(microsecond=0).isoformat() + "Z"
        with self._connect() as conn:
            _ensure_db(conn)
            conn.execute("DELETE FROM alerts WHERE created_at < ?", (cutoff_iso,))
            conn.commit()

    def seen(self, hash_value: str) -> bool:
        with self._connect() as conn:
            _ensure_db(conn)
            cur = conn.execute("SELECT 1 FROM alerts WHERE hash = ?", (hash_value,))
            return cur.fetchone() is not None

    def add(self, hash_value: str) -> None:
        with self._connect() as conn:
            _ensure_db(conn)
            conn.execute(
                "INSERT OR IGNORE INTO alerts(hash, created_at) VALUES(?, ?)",
                (hash_value, _now_iso()),
            )
            conn.commit()

    def add_many(self, hashes: Iterable[str]) -> None:
        with self._connect() as conn:
            _ensure_db(conn)
            conn.executemany(
                "INSERT OR IGNORE INTO alerts(hash, created_at) VALUES(?, ?)",
                [(hash_value, _now_iso()) for hash_value in hashes],
            )
            conn.commit()
