from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import firestore


def init_firestore() -> firestore.Client:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    return firestore.client()


def _resolve_sort_timestamp(data: dict[str, Any]) -> datetime:
    for field_name in ("updated_at", "created_at"):
        value = data.get(field_name)
        if isinstance(value, datetime):
            return value
    return datetime.min.replace(tzinfo=timezone.utc)


def list_eras(limit: int = 50) -> list[dict[str, Any]]:
    db = init_firestore()
    rows: list[dict[str, Any]] = []

    for era_snapshot in db.collection("eras").stream():
        data = era_snapshot.to_dict() or {}
        row: dict[str, Any] = {"era_id": era_snapshot.id}
        row.update(data)
        rows.append(row)

    has_timestamp = any(
        isinstance(row.get("updated_at"), datetime) or isinstance(row.get("created_at"), datetime)
        for row in rows
    )

    if has_timestamp:
        rows.sort(
            key=lambda row: (
                _resolve_sort_timestamp(row),
                row["era_id"],
            ),
            reverse=True,
        )
    else:
        rows.sort(key=lambda row: row["era_id"])

    return rows[:limit]


def era_exists(era_id: str) -> bool:
    db = init_firestore()
    return db.collection("eras").document(era_id).get().exists


def create_era(era_id: str) -> None:
    db = init_firestore()
    db.collection("eras").document(era_id).set(
        {
            "is_active": True,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )


def create_period(era_id: str, period_id: str, index: int) -> None:
    db = init_firestore()
    db.collection("eras").document(era_id).collection("periods").document(period_id).set(
        {
            "index": index,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )


def create_incursion(era_id: str, period_id: str, incursion_id: str, data: dict[str, Any]) -> None:
    db = init_firestore()
    (
        db.collection("eras")
        .document(era_id)
        .collection("periods")
        .document(period_id)
        .collection("incursions")
        .document(incursion_id)
        .set(data)
    )
