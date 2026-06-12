from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterator


def _json_default(value: Any) -> Any:
    if isinstance(value, (Path,)):
        return str(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - defensive
            pass
    return str(value)


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=_json_default)


def _loads(value: str | None) -> Any:
    if value is None:
        return None
    return json.loads(value)


def _derive_dedupe_key(company: dict[str, Any]) -> str:
    explicit = company.get("dedupe_key")
    if explicit:
        return str(explicit)

    yandex_id = company.get("yandex_id")
    if yandex_id not in (None, ""):
        return f"yandex_id:{yandex_id}"

    url = company.get("url")
    if url not in (None, ""):
        return f"url:{url}"

    latitude = company.get("latitude")
    longitude = company.get("longitude")
    if latitude not in (None, "") and longitude not in (None, ""):
        return f"coords:{latitude}:{longitude}"

    canonical = _dumps(company)
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    return f"sha1:{digest}"


class SQLiteStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    dedupe_key TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    UNIQUE(job_id, dedupe_key)
                );

                CREATE INDEX IF NOT EXISTS idx_results_job_id_id
                ON results(job_id, id);
                """
            )

    def create_job(self, job: dict[str, Any]) -> dict[str, Any]:
        payload = dict(job)
        payload.setdefault("id", str(uuid.uuid4()))
        job_id = str(payload["id"])
        serialized = _dumps(payload)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs(id, data)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET data=excluded.data
                """,
                (job_id, serialized),
            )

        return payload

    def update_job(self, job_id: str, **fields: Any) -> dict[str, Any]:
        current = self.get_job(job_id)
        if current is None:
            raise KeyError(job_id)

        current.update(fields)
        current["id"] = job_id
        serialized = _dumps(current)

        with self._connect() as conn:
            conn.execute("UPDATE jobs SET data=? WHERE id=?", (serialized, job_id))

        return current

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return _loads(row["data"])

    def add_result(self, job_id: str, company: dict[str, Any]) -> dict[str, Any]:
        payload = dict(company)
        dedupe_key = _derive_dedupe_key(payload)
        payload["dedupe_key"] = dedupe_key
        serialized = _dumps(payload)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO results(job_id, dedupe_key, data)
                VALUES (?, ?, ?)
                """,
                (job_id, dedupe_key, serialized),
            )

        return payload

    def list_results(self, job_id: str, offset: int, limit: int) -> dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS total FROM results WHERE job_id=?", (job_id,)
            ).fetchone()["total"]
            rows = conn.execute(
                """
                SELECT data
                FROM results
                WHERE job_id=?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (job_id, limit, offset),
            ).fetchall()
        return {
            "items": [_loads(row["data"]) for row in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def all_results(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT data
                FROM results
                WHERE job_id=?
                ORDER BY id ASC
                """,
                (job_id,),
            ).fetchall()
        return [_loads(row["data"]) for row in rows]
