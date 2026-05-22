from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List
import json
from datetime import datetime


DB_PATH = Path("insightmate_history.db")


def init_db(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS review_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            quality_score REAL,
            status TEXT,
            rows INTEGER,
            columns INTEGER,
            payload TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_review(dataset_name: str, payload: Dict[str, Any], db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    profile = payload.get("profile", {})
    quality = payload.get("quality", {})
    cur.execute(
        """
        INSERT INTO review_history
        (dataset_name, created_at, quality_score, status, rows, columns, payload)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dataset_name,
            datetime.utcnow().isoformat(timespec="seconds"),
            quality.get("score"),
            quality.get("status"),
            profile.get("rows"),
            profile.get("columns"),
            json.dumps(payload, default=str),
        ),
    )
    conn.commit()
    conn.close()


def load_history(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT dataset_name, created_at, quality_score, status, rows, columns
        FROM review_history
        ORDER BY id DESC
        LIMIT 20
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "dataset_name": row[0],
            "created_at": row[1],
            "quality_score": row[2],
            "status": row[3],
            "rows": row[4],
            "columns": row[5],
        }
        for row in rows
    ]
