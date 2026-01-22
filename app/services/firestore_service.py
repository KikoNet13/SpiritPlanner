from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import firestore
from app.services.score_service import calculate_score


@dataclass(frozen=True)
class ActiveIncursion:
    era_id: str
    period_id: str
    incursion_id: str


class FirestoreService:
    def __init__(self) -> None:
        self.db = self._init_firestore()

    @staticmethod
    def _init_firestore() -> firestore.Client:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        return firestore.client()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def list_eras(self) -> list[dict[str, Any]]:
        eras = []
        for doc in self.db.collection("eras").stream():
            data = doc.to_dict()
            data["id"] = doc.id
            eras.append(data)
        return eras

    def list_periods(self, era_id: str) -> list[dict[str, Any]]:
        periods = []
        for doc in (
            self.db.collection("eras").document(era_id).collection("periods").stream()
        ):
            data = doc.to_dict()
            data["id"] = doc.id
            periods.append(data)
        return sorted(periods, key=lambda item: item.get("index", 0))

    def list_incursions(self, era_id: str, period_id: str) -> list[dict[str, Any]]:
        incursions = []
        for doc in (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .stream()
        ):
            data = doc.to_dict()
            data["id"] = doc.id
            incursions.append(data)
        return sorted(incursions, key=lambda item: item.get("index", 0))

    def list_sessions(
        self, era_id: str, period_id: str, incursion_id: str
    ) -> list[dict[str, Any]]:
        sessions = []
        for doc in (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .document(incursion_id)
            .collection("sessions")
            .stream()
        ):
            data = doc.to_dict()
            data["id"] = doc.id
            sessions.append(data)
        sessions.sort(key=lambda item: item.get("started_at") or self._utc_now())
        return sessions

    def get_active_incursion(self, era_id: str) -> ActiveIncursion | None:
        for period in self.list_periods(era_id):
            period_id = period["id"]
            for incursion in self.list_incursions(era_id, period_id):
                if incursion.get("started_at") and not incursion.get("ended_at"):
                    return ActiveIncursion(era_id, period_id, incursion["id"])
        return None

    def reveal_period(self, era_id: str, period_id: str, adversary_id: str) -> None:
        periods = self.list_periods(era_id)
        target_index: int | None = None
        for idx, period in enumerate(periods):
            if period["id"] == period_id:
                target_index = idx
                break
        if target_index is None:
            raise ValueError("Periodo no encontrado.")
        if target_index > 0:
            previous = periods[target_index - 1]
            if not previous.get("ended_at"):
                raise ValueError(
                    "No puedes revelar este periodo hasta que el anterior este finalizado."
                )

        period_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
        )
        period_ref.update({"revealed_at": self._utc_now()})

        incursions_ref = period_ref.collection("incursions")
        batch = self.db.batch()
        for doc in incursions_ref.stream():
            batch.update(doc.reference, {"adversary_id": adversary_id})
        batch.commit()

    def start_incursion(
        self,
        era_id: str,
        period_id: str,
        incursion_id: str,
        adversary_level: str,
        difficulty: int,
    ) -> None:
        if self.get_active_incursion(era_id):
            raise ValueError("Ya existe una incursion activa en esta Era.")

        incursion_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .document(incursion_id)
        )
        incursion_ref.update(
            {
                "started_at": self._utc_now(),
                "adversary_level": adversary_level,
                "difficulty": difficulty,
            }
        )
        self._ensure_period_started(era_id, period_id)
        self._create_session(incursion_ref)

    def resume_incursion(self, era_id: str, period_id: str, incursion_id: str) -> None:
        active = self.get_active_incursion(era_id)
        if active and (
            active.period_id != period_id or active.incursion_id != incursion_id
        ):
            raise ValueError("Ya existe una incursion activa en esta Era.")

        incursion_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .document(incursion_id)
        )
        open_sessions = list(
            incursion_ref.collection("sessions").where("ended_at", "==", None).stream()
        )
        if not open_sessions:
            self._create_session(incursion_ref)

    def pause_incursion(self, era_id: str, period_id: str, incursion_id: str) -> None:
        sessions_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .document(incursion_id)
            .collection("sessions")
        )
        open_sessions = list(sessions_ref.where("ended_at", "==", None).stream())
        if not open_sessions:
            return
        open_sessions[0].reference.update({"ended_at": self._utc_now()})

    def finalize_incursion(
        self,
        era_id: str,
        period_id: str,
        incursion_id: str,
        result: str,
        player_count: int,
        invader_cards_remaining: int,
        invader_cards_out_of_deck: int,
        dahan_alive: int,
        blight_on_island: int,
    ) -> None:
        incursion_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .document(incursion_id)
        )
        snapshot = incursion_ref.get()
        incursion_data = snapshot.to_dict() or {}
        if incursion_data.get("ended_at"):
            raise ValueError("La incursion ya esta finalizada. El score es inmutable.")

        difficulty = int(incursion_data.get("difficulty", 0) or 0)
        score = calculate_score(
            difficulty=difficulty,
            result=result,
            invader_cards_remaining=invader_cards_remaining,
            invader_cards_out_of_deck=invader_cards_out_of_deck,
            player_count=player_count,
            dahan_alive=dahan_alive,
            blight_on_island=blight_on_island,
        )

        self.pause_incursion(era_id, period_id, incursion_id)
        incursion_ref.update(
            {
                "ended_at": self._utc_now(),
                "result": result,
                "player_count": player_count,
                "invader_cards_remaining": invader_cards_remaining,
                "invader_cards_out_of_deck": invader_cards_out_of_deck,
                "dahan_alive": dahan_alive,
                "blight_on_island": blight_on_island,
                "score": score,
            }
        )
        if self._period_complete(era_id, period_id):
            self.db.collection("eras").document(era_id).collection("periods").document(
                period_id
            ).update({"ended_at": self._utc_now()})

    def _create_session(self, incursion_ref: firestore.DocumentReference) -> None:
        incursion_ref.collection("sessions").add(
            {"started_at": self._utc_now(), "ended_at": None}
        )

    def _period_complete(self, era_id: str, period_id: str) -> bool:
        incursions = self.list_incursions(era_id, period_id)
        return all(incursion.get("ended_at") for incursion in incursions)

    def _ensure_period_started(self, era_id: str, period_id: str) -> None:
        period_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
        )
        snapshot = period_ref.get()
        data = snapshot.to_dict() or {}
        if not data.get("started_at"):
            period_ref.update({"started_at": self._utc_now()})
