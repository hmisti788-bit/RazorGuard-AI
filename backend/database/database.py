"""SQLite persistence for prediction audit records."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "razorguard.db"
DB_PATH = Path(os.getenv("RAZORGUARD_DB_PATH", DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                amount REAL NOT NULL,
                hour INTEGER NOT NULL,
                transaction_frequency INTEGER NOT NULL,
                average_amount REAL NOT NULL,
                recipient_is_new INTEGER NOT NULL,
                device_changed INTEGER NOT NULL,
                location_changed INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                account_age_days INTEGER NOT NULL,
                previous_failed_transactions INTEGER NOT NULL,
                fraud_probability REAL NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                reasons TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def insert_prediction(transaction: dict[str, Any], result: dict[str, Any]) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO predictions (
                transaction_id, amount, hour, transaction_frequency,
                average_amount, recipient_is_new, device_changed,
                location_changed, transaction_type, account_age_days,
                previous_failed_transactions, fraud_probability, risk_score,
                risk_level, reasons, recommended_action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["transaction_id"],
                transaction["amount"],
                transaction["hour"],
                transaction["transaction_frequency"],
                transaction["average_amount"],
                transaction["recipient_is_new"],
                transaction["device_changed"],
                transaction["location_changed"],
                transaction["transaction_type"],
                transaction["account_age_days"],
                transaction["previous_failed_transactions"],
                result["fraud_probability"],
                result["risk_score"],
                result["risk_level"],
                json.dumps(result["reasons"]),
                result["recommended_action"],
                result["created_at"],
            ),
        )


def list_predictions(limit: int, offset: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [_deserialize_row(row) for row in rows]


def get_analytics() -> dict[str, Any]:
    with get_connection() as connection:
        summary = connection.execute(
            """
            SELECT COUNT(*) AS total_predictions,
                   COALESCE(AVG(risk_score), 0) AS average_risk_score
            FROM predictions
            """
        ).fetchone()
        levels = connection.execute(
            "SELECT risk_level, COUNT(*) AS count FROM predictions GROUP BY risk_level"
        ).fetchall()
    counts = {row["risk_level"]: row["count"] for row in levels}
    return {
        "total_predictions": summary["total_predictions"],
        "average_risk_score": round(summary["average_risk_score"], 4),
        "safe_count": counts.get("Safe", 0),
        "suspicious_count": counts.get("Suspicious", 0),
        "high_risk_count": counts.get("High Risk", 0),
    }


def _deserialize_row(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)
    record["reasons"] = json.loads(record["reasons"])
    return record


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()