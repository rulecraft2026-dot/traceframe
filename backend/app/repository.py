import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .models import ProvenanceRecord


class ProvenanceRepository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY, parent_id TEXT, prompt TEXT NOT NULL,
                    provider TEXT NOT NULL, model TEXT NOT NULL, params TEXT NOT NULL,
                    status TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT,
                    asset_url TEXT, asset_sha256 TEXT, manifest_sha256 TEXT,
                    manifest_url TEXT, error TEXT, replayable INTEGER NOT NULL DEFAULT 1
                )"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_generations_created ON generations(created_at DESC)")

    def save(self, record: ProvenanceRecord) -> ProvenanceRecord:
        values = record.model_dump()
        values["params"] = json.dumps(values["params"], sort_keys=True)
        values["created_at"] = record.created_at.isoformat()
        values["completed_at"] = record.completed_at.isoformat() if record.completed_at else None
        values["replayable"] = int(record.replayable)
        columns = ", ".join(values)
        placeholders = ", ".join(f":{key}" for key in values)
        updates = ", ".join(f"{key}=excluded.{key}" for key in values if key != "id")
        with self.connect() as connection:
            connection.execute(
                f"INSERT INTO generations ({columns}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {updates}",
                values,
            )
        return record

    def get(self, record_id: str) -> ProvenanceRecord | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM generations WHERE id = ?", (record_id,)).fetchone()
        return self._record(row) if row else None

    def list(self, limit: int = 50) -> list[ProvenanceRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM generations ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._record(row) for row in rows]

    @staticmethod
    def _record(row: sqlite3.Row) -> ProvenanceRecord:
        values = dict(row)
        values["params"] = json.loads(values["params"])
        values["created_at"] = datetime.fromisoformat(values["created_at"])
        values["completed_at"] = datetime.fromisoformat(values["completed_at"]) if values["completed_at"] else None
        values["replayable"] = bool(values["replayable"])
        return ProvenanceRecord(**values)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
