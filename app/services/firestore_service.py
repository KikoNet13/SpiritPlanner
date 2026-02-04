from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import firestore
from services.score_service import calculate_score
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ActiveIncursion:
    era_id: str
    period_id: str
    incursion_id: str


class FirestoreService:
    _ACTIVE_INCURSION_SEPARATOR = "::"

    def __init__(self) -> None:
        logger.debug("Initializing FirestoreService")
        self.db = self._init_firestore()
        logger.debug("FirestoreService initialized db=%s", self.db)

    @staticmethod
    def _init_firestore() -> firestore.Client:
        logger.debug("Initializing Firestore client")
        if not firebase_admin._apps:
            logger.info("Firebase app not initialized; initializing now")
            firebase_admin.initialize_app()
        client = firestore.client()
        logger.debug("Firestore client created=%s", client)
        return client

    @staticmethod
    def _utc_now() -> datetime:
        now = datetime.now(timezone.utc)
        logger.debug("UTC now=%s", now)
        return now

    def list_eras(self) -> list[dict[str, Any]]:
        logger.debug("Listing eras")
        eras = []
        for doc in self.db.collection("eras").stream():
            data = doc.to_dict()
            data["id"] = doc.id
            eras.append(data)
        logger.debug("Listed eras count=%s", len(eras))
        return eras

    def list_periods(self, era_id: str) -> list[dict[str, Any]]:
        logger.debug("Listing periods era_id=%s", era_id)
        periods = []
        for doc in (
            self.db.collection("eras").document(era_id).collection("periods").stream()
        ):
            data = doc.to_dict()
            data["id"] = doc.id
            periods.append(data)
        periods_sorted = sorted(periods, key=lambda item: item.get("index", 0))
        logger.debug("Listed periods count=%s era_id=%s", len(periods_sorted), era_id)
        return periods_sorted

    def list_incursions(self, era_id: str, period_id: str) -> list[dict[str, Any]]:
        logger.debug("Listing incursions era_id=%s period_id=%s", era_id, period_id)
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
        incursions_sorted = sorted(incursions, key=lambda item: item.get("index", 0))
        logger.debug(
            "Listed incursions count=%s era_id=%s period_id=%s",
            len(incursions_sorted),
            era_id,
            period_id,
        )
        return incursions_sorted

    def list_sessions(
        self, era_id: str, period_id: str, incursion_id: str
    ) -> list[dict[str, Any]]:
        logger.debug(
            "Listing sessions era_id=%s period_id=%s incursion_id=%s",
            era_id,
            period_id,
            incursion_id,
        )
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
        logger.debug(
            "Listed sessions count=%s era_id=%s period_id=%s incursion_id=%s",
            len(sessions),
            era_id,
            period_id,
            incursion_id,
        )
        return sessions

    def _build_active_incursion_id(self, period_id: str, incursion_id: str) -> str:
        return f"{period_id}{self._ACTIVE_INCURSION_SEPARATOR}{incursion_id}"

    def _parse_active_incursion_id(
        self, active_incursion_id: str | None
    ) -> tuple[str, str] | None:
        if not active_incursion_id:
            return None
        if self._ACTIVE_INCURSION_SEPARATOR not in active_incursion_id:
            logger.warning(
                "Invalid active_incursion_id format value=%s",
                active_incursion_id,
            )
            return None
        period_id, incursion_id = active_incursion_id.split(
            self._ACTIVE_INCURSION_SEPARATOR, 1
        )
        if not period_id or not incursion_id:
            logger.warning(
                "Invalid active_incursion_id split value=%s",
                active_incursion_id,
            )
            return None
        return period_id, incursion_id

    def get_active_incursion(self, era_id: str) -> ActiveIncursion | None:
        logger.debug("Getting active incursion era_id=%s", era_id)
        era_ref = self.db.collection("eras").document(era_id)
        era_data = era_ref.get().to_dict() or {}
        active_incursion_id = era_data.get("active_incursion_id")
        parsed = self._parse_active_incursion_id(active_incursion_id)
        if parsed:
            period_id, incursion_id = parsed
            logger.debug(
                "Active incursion found in era document period_id=%s incursion_id=%s",
                period_id,
                incursion_id,
            )
            return ActiveIncursion(era_id, period_id, incursion_id)
        logger.debug("No active incursion found era_id=%s", era_id)
        return None

    def reveal_period(self, era_id: str, period_id: str) -> None:
        logger.info("Reveal period request era_id=%s period_id=%s", era_id, period_id)
        periods = self.list_periods(era_id)
        target_index: int | None = None
        for idx, period in enumerate(periods):
            if period["id"] == period_id:
                target_index = idx
                break
        if target_index is None:
            logger.error("Periodo no encontrado era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Periodo no encontrado.")
        if target_index > 0:
            previous = periods[target_index - 1]
            if not previous.get("ended_at"):
                logger.warning(
                    "Cannot reveal period; previous not ended era_id=%s period_id=%s",
                    era_id,
                    period_id,
                )
                raise ValueError(
                    "No puedes revelar este periodo hasta que el anterior este finalizado."
                )

        period_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
        )
        snapshot = period_ref.get()
        if not snapshot.exists:
            logger.error("Periodo no encontrado in Firestore era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Periodo no encontrado.")
        period_data = snapshot.to_dict() or {}
        if period_data.get("revealed_at"):
            logger.warning("Periodo ya revelado era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Este periodo ya esta revelado.")
        logger.debug("Updating period revealed_at era_id=%s period_id=%s", era_id, period_id)
        period_ref.update({"revealed_at": self._utc_now()})
        logger.info("Period revealed era_id=%s period_id=%s", era_id, period_id)

    def set_incursion_adversary(
        self, era_id: str, period_id: str, incursion_id: str, adversary_id: str | None
    ) -> None:
        logger.info(
            "Set incursion adversary era_id=%s period_id=%s incursion_id=%s adversary_id=%s",
            era_id,
            period_id,
            incursion_id,
            adversary_id,
        )
        period_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
        )
        period_snapshot = period_ref.get()
        if not period_snapshot.exists:
            logger.error("Periodo no encontrado era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Periodo no encontrado.")
        period_data = period_snapshot.to_dict() or {}
        if period_data.get("adversaries_assigned_at"):
            logger.warning("Adversaries already assigned era_id=%s period_id=%s", era_id, period_id)
            raise ValueError(
                "No puedes modificar adversarios cuando ya fueron asignados."
            )
        if not period_data.get("revealed_at"):
            logger.warning("Periodo not revealed era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("No puedes asignar adversarios sin revelar el periodo.")
        if period_data.get("ended_at"):
            logger.warning("Periodo already ended era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("No puedes modificar adversarios en un periodo finalizado.")

        incursion_ref = period_ref.collection("incursions").document(incursion_id)
        incursion_snapshot = incursion_ref.get()
        if not incursion_snapshot.exists:
            logger.error("Incursion no encontrada incursion_id=%s", incursion_id)
            raise ValueError("Incursion no encontrada.")
        logger.debug("Updating incursion adversary incursion_id=%s", incursion_id)
        incursion_ref.update({"adversary_id": adversary_id})
        logger.info("Incursion adversary updated incursion_id=%s", incursion_id)

    def assign_period_adversaries(
        self, era_id: str, period_id: str, assignments: dict[str, str | None]
    ) -> None:
        logger.info(
            "Assign period adversaries era_id=%s period_id=%s assignments_count=%s",
            era_id,
            period_id,
            len(assignments),
        )
        period_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
        )
        period_snapshot = period_ref.get()
        if not period_snapshot.exists:
            logger.error("Periodo no encontrado era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Periodo no encontrado.")
        period_data = period_snapshot.to_dict() or {}
        if not period_data.get("revealed_at"):
            logger.warning("Periodo not revealed era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("No puedes asignar adversarios sin revelar el periodo.")
        if period_data.get("ended_at"):
            logger.warning("Periodo already ended era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("No puedes asignar adversarios en un periodo finalizado.")
        if period_data.get("adversaries_assigned_at"):
            logger.warning(
                "Periodo already has adversaries assigned era_id=%s period_id=%s",
                era_id,
                period_id,
            )
            raise ValueError("Este periodo ya tiene adversarios asignados.")

        incursions = self.list_incursions(era_id, period_id)
        if len(incursions) != 4:
            logger.warning(
                "Invalid incursion count for assignments count=%s",
                len(incursions),
            )
            raise ValueError("El periodo debe tener exactamente 4 incursiones.")
        incursion_ids = {incursion["id"] for incursion in incursions}
        if set(assignments.keys()) != incursion_ids:
            logger.warning(
                "Assignment keys do not match incursions expected=%s actual=%s",
                incursion_ids,
                set(assignments.keys()),
            )
            raise ValueError("Debes asignar adversarios a las 4 incursiones.")

        adversaries = list(assignments.values())
        if any(not adversary for adversary in adversaries):
            logger.warning("Missing adversary assignments")
            raise ValueError("Debes asignar adversario a todas las incursiones.")
        if len(set(adversaries)) != len(adversaries):
            logger.warning("Duplicate adversaries in assignments")
            raise ValueError("Los adversarios deben ser distintos en el periodo.")

        batch = self.db.batch()
        for incursion in incursions:
            incursion_ref = period_ref.collection("incursions").document(incursion["id"])
            batch.update(incursion_ref, {"adversary_id": assignments[incursion["id"]]})
        batch.update(
            period_ref,
            {"adversaries_assigned_at": self._utc_now()},
        )
        logger.debug("Committing batch assignments period_id=%s", period_id)
        batch.commit()
        logger.info("Assigned adversaries period_id=%s", period_id)

    def start_session(
        self,
        era_id: str,
        period_id: str,
        incursion_id: str,
    ) -> None:
        logger.info(
            "Start session era_id=%s period_id=%s incursion_id=%s",
            era_id,
            period_id,
            incursion_id,
        )
        era_ref = self.db.collection("eras").document(era_id)
        period_ref = era_ref.collection("periods").document(period_id)
        period_snapshot = period_ref.get()
        if not period_snapshot.exists:
            logger.error("Periodo no encontrado era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Periodo no encontrado.")
        period_data = period_snapshot.to_dict() or {}
        if not period_data.get("revealed_at"):
            logger.warning("Periodo not revealed era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("No puedes iniciar una incursion sin revelar el periodo.")
        if period_data.get("ended_at"):
            logger.warning("Periodo already ended era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("El periodo ya esta finalizado.")
        if not period_data.get("adversaries_assigned_at"):
            logger.warning("Adversaries not assigned era_id=%s period_id=%s", era_id, period_id)
            raise ValueError("Debes asignar adversarios antes de iniciar incursiones.")

        active_incursion = self.get_active_incursion(era_id)
        if active_incursion and (
            active_incursion.period_id != period_id
            or active_incursion.incursion_id != incursion_id
        ):
            logger.warning("Active incursion exists era_id=%s", era_id)
            raise ValueError("Ya existe una incursion activa en esta Era.")

        incursion_ref = (
            period_ref.collection("incursions").document(incursion_id)
        )
        incursion_snapshot = incursion_ref.get()
        if not incursion_snapshot.exists:
            logger.error("Incursion no encontrada incursion_id=%s", incursion_id)
            raise ValueError("Incursion no encontrada.")
        incursion_data = incursion_snapshot.to_dict() or {}
        if incursion_data.get("ended_at") or incursion_data.get("result"):
            logger.warning("Incursion already ended incursion_id=%s", incursion_id)
            raise ValueError("La incursion ya esta finalizada.")

        sessions_ref = incursion_ref.collection("sessions")
        open_sessions = list(sessions_ref.where("ended_at", "==", None).stream())
        if open_sessions:
            logger.warning("Open session already exists incursion_id=%s", incursion_id)
            raise ValueError("Ya hay una sesión abierta.")

        has_sessions = bool(self.list_sessions(era_id, period_id, incursion_id))
        if not has_sessions:
            if not incursion_data.get("adversary_level"):
                logger.warning("Missing adversary level incursion_id=%s", incursion_id)
                raise ValueError("Debes seleccionar un nivel válido.")
            if incursion_data.get("difficulty") is None:
                logger.warning("Missing difficulty incursion_id=%s", incursion_id)
                raise ValueError("Debes seleccionar un nivel válido.")

            incursions = self.list_incursions(era_id, period_id)
            if len(incursions) != 4:
                logger.warning("Invalid incursion count=%s", len(incursions))
                raise ValueError("El periodo debe tener exactamente 4 incursiones.")
            adversaries = [incursion.get("adversary_id") for incursion in incursions]
            if any(not adversary for adversary in adversaries):
                logger.warning("Missing adversary assignment in period")
                raise ValueError(
                    "Todas las incursiones deben tener un adversario asignado."
                )
            if len(set(adversaries)) != 4:
                logger.warning("Duplicate adversaries found in period")
                raise ValueError("Los adversarios del periodo deben ser distintos.")

        update_data: dict[str, Any] = {"is_active": True}
        if not incursion_data.get("started_at"):
            update_data["started_at"] = self._utc_now()
        logger.debug("Updating incursion start metadata incursion_id=%s", incursion_id)
        incursion_ref.update(update_data)
        active_incursion_id = self._build_active_incursion_id(period_id, incursion_id)
        logger.debug("Updating era active incursion era_id=%s", era_id)
        era_ref.update(
            {
                "active_incursion_id": active_incursion_id,
                "active_incursion": {
                    "period_id": period_id,
                    "incursion_id": incursion_id,
                },
            }
        )
        self._create_session(incursion_ref)
        logger.info("Session started incursion_id=%s", incursion_id)

    def update_incursion_adversary_level(
        self,
        era_id: str,
        period_id: str,
        incursion_id: str,
        adversary_id: str | None,
        adversary_level: str | None,
        difficulty: int | None,
    ) -> None:
        logger.info(
            "Update incursion adversary level era_id=%s period_id=%s incursion_id=%s level=%s difficulty=%s",
            era_id,
            period_id,
            incursion_id,
            adversary_level,
            difficulty,
        )
        incursion_ref = (
            self.db.collection("eras")
            .document(era_id)
            .collection("periods")
            .document(period_id)
            .collection("incursions")
            .document(incursion_id)
        )
        update_data: dict[str, object | None] = {
            "adversary_level": adversary_level,
            "difficulty": difficulty,
        }
        if adversary_id is not None:
            update_data["adversary_id"] = adversary_id
        incursion_ref.update(update_data)
        logger.info("Incursion adversary level updated incursion_id=%s", incursion_id)

    def end_session(self, era_id: str, period_id: str, incursion_id: str) -> None:
        logger.info(
            "End session era_id=%s period_id=%s incursion_id=%s",
            era_id,
            period_id,
            incursion_id,
        )
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
            logger.warning("No open sessions to end incursion_id=%s", incursion_id)
            return
        logger.debug("Closing session id=%s", open_sessions[0].id)
        open_sessions[0].reference.update({"ended_at": self._utc_now()})
        logger.info("Session ended incursion_id=%s", incursion_id)

    def finalize_incursion(
        self,
        era_id: str,
        period_id: str,
        incursion_id: str,
        result: str,
        dahan_alive: int,
        blight_on_island: int,
        player_count: int | None = None,
        invader_cards_remaining: int | None = None,
        invader_cards_out_of_deck: int | None = None,
    ) -> None:
        logger.info(
            "Finalize incursion era_id=%s period_id=%s incursion_id=%s result=%s",
            era_id,
            period_id,
            incursion_id,
            result,
        )
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
            logger.error("Incursion already finalized incursion_id=%s", incursion_id)
            raise ValueError("La incursion ya esta finalizada. El score es inmutable.")

        difficulty = int(incursion_data.get("difficulty", 0) or 0)
        resolved_player_count = 2
        if result == "win":
            if invader_cards_remaining is None:
                raise ValueError("Debes indicar las cartas en el mazo.")
            if invader_cards_remaining < 0:
                raise ValueError("Las cartas en el mazo deben ser 0 o más.")
        if result == "loss":
            if invader_cards_out_of_deck is None:
                raise ValueError("Debes indicar las cartas fuera del mazo.")
            if invader_cards_out_of_deck < 0:
                raise ValueError("Las cartas fuera del mazo deben ser 0 o más.")
        logger.debug("Calculating score difficulty=%s result=%s", difficulty, result)
        score = calculate_score(
            difficulty=difficulty,
            result=result,
            dahan_alive=dahan_alive,
            blight_on_island=blight_on_island,
            player_count=resolved_player_count,
            invader_cards_remaining=invader_cards_remaining,
            invader_cards_out_of_deck=invader_cards_out_of_deck,
        )

        self.end_session(era_id, period_id, incursion_id)
        logger.debug("Updating incursion finalize fields incursion_id=%s", incursion_id)
        update_payload: dict[str, object | None] = {
            "ended_at": self._utc_now(),
            "result": result,
            "dahan_alive": dahan_alive,
            "blight_on_island": blight_on_island,
            "score": score,
            "is_active": False,
            "player_count": resolved_player_count,
        }
        if result == "win":
            update_payload["invader_cards_remaining"] = invader_cards_remaining
        if result == "loss":
            update_payload["invader_cards_out_of_deck"] = invader_cards_out_of_deck
        incursion_ref.update(update_payload)
        logger.debug("Clearing active incursion era_id=%s", era_id)
        self.db.collection("eras").document(era_id).update(
            {
                "active_incursion_id": firestore.DELETE_FIELD,
                "active_incursion": firestore.DELETE_FIELD,
            }
        )
        if self._period_complete(era_id, period_id):
            logger.info("Period completed; marking ended era_id=%s period_id=%s", era_id, period_id)
            self.db.collection("eras").document(era_id).collection("periods").document(
                period_id
            ).update({"ended_at": self._utc_now()})
        logger.info("Incursion finalized incursion_id=%s score=%s", incursion_id, score)

    def _create_session(self, incursion_ref: firestore.DocumentReference) -> None:
        logger.debug("Creating session for incursion_ref=%s", incursion_ref)
        incursion_ref.collection("sessions").add(
            {"started_at": self._utc_now(), "ended_at": None}
        )
        logger.debug("Session created")

    def _period_complete(self, era_id: str, period_id: str) -> bool:
        logger.debug("Checking period completion era_id=%s period_id=%s", era_id, period_id)
        incursions = self.list_incursions(era_id, period_id)
        complete = all(incursion.get("ended_at") for incursion in incursions)
        logger.debug(
            "Period completion result=%s era_id=%s period_id=%s",
            complete,
            era_id,
            period_id,
        )
        return complete
