from __future__ import annotations

from typing import Any

import firebase_admin
from firebase_admin import firestore


def init_firestore() -> firestore.Client:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    return firestore.client()


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
            "revealed_at": None,
            "started_at": None,
            "ended_at": None,
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
