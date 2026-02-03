"""Administrative utilities for era maintenance in Firestore."""

from __future__ import annotations

from dataclasses import dataclass

if __package__:
    from .firestore_service import init_firestore
else:
    from firestore_service import init_firestore


@dataclass(frozen=True)
class EraTreeCounts:
    era_exists: bool
    num_periods: int
    num_incursions: int
    num_sessions: int


def count_era_tree(era_id: str) -> EraTreeCounts:
    db = init_firestore()
    era_ref = db.collection("eras").document(era_id)
    era_snapshot = era_ref.get()

    num_periods = 0
    num_incursions = 0
    num_sessions = 0

    for period_snapshot in era_ref.collection("periods").stream():
        num_periods += 1
        for incursion_snapshot in period_snapshot.reference.collection("incursions").stream():
            num_incursions += 1
            for _ in incursion_snapshot.reference.collection("sessions").stream():
                num_sessions += 1

    return EraTreeCounts(
        era_exists=era_snapshot.exists,
        num_periods=num_periods,
        num_incursions=num_incursions,
        num_sessions=num_sessions,
    )


def delete_era_tree(era_id: str) -> None:
    db = init_firestore()
    era_ref = db.collection("eras").document(era_id)

    for period_snapshot in era_ref.collection("periods").stream():
        period_ref = period_snapshot.reference
        for incursion_snapshot in period_ref.collection("incursions").stream():
            incursion_ref = incursion_snapshot.reference
            for session_snapshot in incursion_ref.collection("sessions").stream():
                session_snapshot.reference.delete()
            incursion_ref.delete()
        period_ref.delete()

    era_ref.delete()
