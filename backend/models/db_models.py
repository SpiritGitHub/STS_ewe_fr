from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistoryItem:
    id: int
    created_at: str
    direction: str
    kind: str  # stt|translate|tts|sts
    input_text: str | None
    output_text: str | None
    meta_json: str | None


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              direction TEXT NOT NULL,
              kind TEXT NOT NULL,
              input_text TEXT,
              output_text TEXT,
              meta_json TEXT
            );
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC);")


def add_history(
    db_path: Path,
    *,
    direction: str,
    kind: str,
    input_text: str | None = None,
    output_text: str | None = None,
    meta_json: str | None = None,
) -> int:
    init_db(db_path)
    with sqlite3.connect(str(db_path)) as con:
        cur = con.execute(
            "INSERT INTO history(direction, kind, input_text, output_text, meta_json) VALUES (?, ?, ?, ?, ?)",
            (direction, kind, input_text, output_text, meta_json),
        )
        return int(cur.lastrowid)


def list_history(db_path: Path, limit: int = 50) -> list[HistoryItem]:
    init_db(db_path)
    with sqlite3.connect(str(db_path)) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id, created_at, direction, kind, input_text, output_text, meta_json FROM history ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()

    items: list[HistoryItem] = []
    for r in rows:
        items.append(
            HistoryItem(
                id=int(r["id"]),
                created_at=str(r["created_at"]),
                direction=str(r["direction"]),
                kind=str(r["kind"]),
                input_text=r["input_text"],
                output_text=r["output_text"],
                meta_json=r["meta_json"],
            )
        )
    return items
