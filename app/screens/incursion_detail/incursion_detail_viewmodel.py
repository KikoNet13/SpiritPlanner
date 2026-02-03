from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import flet as ft

from app.screens.data_lookup import (
    get_adversary_difficulty,
    get_adversary_name,
    get_adversary_levels,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)
from app.screens.incursion_detail.incursion_detail_model import (
    FinalizeFormData,
    IncursionDetailModel,
    SessionEntryModel,
    SESSION_STATE_FINALIZED,
    SESSION_STATE_NOT_STARTED,
    build_period_label,
    compute_score_preview,
    resolve_session_state,
)
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)


@ft.observable
class IncursionDetailViewModel:
    def __init__(self) -> None:
        self.era_id: str | None = None
        self.period_id: str | None = None
        self.incursion_id: str | None = None
        self.detail: IncursionDetailModel | None = None
        self.sessions: list[SessionEntryModel] = []
        self.open_session = False
        self.has_sessions = False
        self.session_state = SESSION_STATE_NOT_STARTED
        self.loading = False
        self.error: str | None = None
        self.adversary_level: str | None = None
        self.finalize_form = FinalizeFormData(
            result=None,
            dahan_alive="",
            blight_on_island="",
            invader_cards_remaining="",
            invader_cards_out_of_deck="",
        )
        self.show_finalize_confirm = False
        self.toast_message: str | None = None
        self.toast_version = 0
        self.score_dialog_open = False
        self.score_dialog_version = 0
        self.timer_running = False
        self.timer_now: datetime | None = None

    def ensure_loaded(
        self,
        service: FirestoreService,
        era_id: str,
        period_id: str,
        incursion_id: str,
    ) -> None:
        self.era_id = era_id
        self.period_id = period_id
        self.incursion_id = incursion_id
        self.load_detail(service)

    def load_detail(self, service: FirestoreService) -> None:
        if not self.era_id or not self.period_id or not self.incursion_id:
            return
        logger.info(
            "Firestore load incursion detail era_id=%s period_id=%s incursion_id=%s",
            self.era_id,
            self.period_id,
            self.incursion_id,
        )
        self.loading = True
        self.error = None
        try:
            incursions = service.list_incursions(self.era_id, self.period_id)
            incursion = next(
                (item for item in incursions if item["id"] == self.incursion_id), None
            )
            if not incursion:
                logger.warning(
                    "Incursion not found incursion_id=%s", self.incursion_id
                )
                self.error = "not_found"
                self.detail = None
                self.sessions = []
                return
            period = next(
                (
                    item
                    for item in service.list_periods(self.era_id)
                    if item["id"] == self.period_id
                ),
                None,
            )
            sessions = service.list_sessions(
                self.era_id, self.period_id, self.incursion_id
            )
            self.sessions = [
                SessionEntryModel(
                    started_at=session.get("started_at"),
                    ended_at=session.get("ended_at"),
                )
                for session in sessions
            ]
            self.open_session = any(session.ended_at is None for session in self.sessions)
            self.has_sessions = bool(self.sessions)
            self.session_state = resolve_session_state(
                incursion, self.has_sessions, self.open_session
            )

            detail = IncursionDetailModel(
                incursion_id=incursion["id"],
                index=incursion.get("index", 0),
                spirit_1_name=get_spirit_name(incursion.get("spirit_1_id")),
                spirit_2_name=get_spirit_name(incursion.get("spirit_2_id")),
                layout_id=incursion.get("board_layout") or "",
                board_1_name=get_board_name(incursion.get("board_1")),
                board_2_name=get_board_name(incursion.get("board_2")),
                layout_name=get_layout_name(incursion.get("board_layout")),
                board_1_id=incursion.get("board_1") or "",
                board_2_id=incursion.get("board_2") or "",
                adversary_id=incursion.get("adversary_id"),
                adversary_name=get_adversary_name(incursion.get("adversary_id")),
                adversary_level=incursion.get("adversary_level"),
                difficulty=incursion.get("difficulty"),
                period_label=build_period_label(period),
                result=incursion.get("result"),
                score=incursion.get("score"),
                dahan_alive=incursion.get("dahan_alive"),
                blight_on_island=incursion.get("blight_on_island"),
                player_count=incursion.get("player_count"),
                invader_cards_remaining=incursion.get("invader_cards_remaining"),
                invader_cards_out_of_deck=incursion.get("invader_cards_out_of_deck"),
            )
            self.detail = detail
            self.adversary_level = detail.adversary_level
            self.finalize_form = FinalizeFormData(
                result=detail.result,
                dahan_alive=str(detail.dahan_alive or ""),
                blight_on_island=str(detail.blight_on_island or ""),
                invader_cards_remaining=str(detail.invader_cards_remaining or ""),
                invader_cards_out_of_deck=str(detail.invader_cards_out_of_deck or ""),
            )
            self.show_finalize_confirm = False
            self.timer_running = (
                self.open_session and self.session_state != SESSION_STATE_FINALIZED
            )
            self.timer_now = datetime.now(timezone.utc) if self.timer_running else None
        except Exception as exc:
            logger.error(
                "Failed to load incursion detail error=%s", exc, exc_info=True
            )
            self.error = "load_failed"
            self.detail = None
            self.sessions = []
        finally:
            self.loading = False

    def update_adversary_level(
        self, service: FirestoreService, level: str | None
    ) -> None:
        if not self.detail:
            return
        if self.session_state == SESSION_STATE_FINALIZED or self.has_sessions:
            return
        if not self.era_id or not self.period_id or not self.incursion_id:
            return
        adversary_id = self.detail.adversary_id
        if not adversary_id:
            self.show_toast("No hay adversario asignado.")
            return
        difficulty = get_adversary_difficulty(adversary_id, level)
        logger.info(
            "Firestore update adversary level incursion_id=%s level=%s",
            self.incursion_id,
            level,
        )
        try:
            service.update_incursion_adversary_level(
                era_id=self.era_id,
                period_id=self.period_id,
                incursion_id=self.incursion_id,
                adversary_id=adversary_id,
                adversary_level=level,
                difficulty=difficulty,
            )
        except ValueError as exc:
            logger.error(
                "Failed to update adversary level error=%s", exc, exc_info=True
            )
            self.show_toast(str(exc))
            return
        self.adversary_level = level
        self.detail = replace(
            self.detail,
            adversary_level=level,
            difficulty=difficulty,
        )

    def update_finalize_field(self, field: str, value: str | None) -> None:
        if not self.finalize_form:
            return
        data = self.finalize_form
        updated = FinalizeFormData(
            result=value if field == "result" else data.result,
            dahan_alive=value if field == "dahan_alive" else data.dahan_alive,
            blight_on_island=value if field == "blight_on_island" else data.blight_on_island,
            invader_cards_remaining=(
                value if field == "invader_cards_remaining" else data.invader_cards_remaining
            ),
            invader_cards_out_of_deck=(
                value if field == "invader_cards_out_of_deck" else data.invader_cards_out_of_deck
            ),
        )
        self.finalize_form = updated

    def toggle_finalize_confirm(self, show: bool) -> None:
        self.show_finalize_confirm = show

    def _parse_int(self, value: str | None, default: int = 0) -> int | None:
        if value in (None, ""):
            return default
        try:
            return int(value)
        except ValueError:
            return None

    def finalize_incursion(self, service: FirestoreService) -> None:
        if not self.detail:
            return
        if not self.era_id or not self.period_id or not self.incursion_id:
            return
        if self.session_state == SESSION_STATE_FINALIZED:
            self.show_toast("La incursión ya está finalizada.")
            return
        result_value = self.finalize_form.result
        if not result_value:
            self.show_toast("Debes indicar el resultado.")
            return
        dahan_alive = self._parse_int(self.finalize_form.dahan_alive, 0)
        blight_on_island = self._parse_int(self.finalize_form.blight_on_island, 0)
        if None in (dahan_alive, blight_on_island):
            self.show_toast("Revisa los valores numéricos.")
            return
        invader_cards_remaining = None
        invader_cards_out_of_deck = None
        if result_value == "win":
            invader_cards_remaining = self._parse_int(
                self.finalize_form.invader_cards_remaining, None
            )
            if invader_cards_remaining is None or invader_cards_remaining < 0:
                self.show_toast("Debes indicar las cartas en el mazo (0 o más).")
                return
        if result_value == "loss":
            invader_cards_out_of_deck = self._parse_int(
                self.finalize_form.invader_cards_out_of_deck, None
            )
            if invader_cards_out_of_deck is None or invader_cards_out_of_deck < 0:
                self.show_toast(
                    "Debes indicar las cartas fuera del mazo (0 o más)."
                )
                return
        if self.open_session:
            logger.info(
                "Closing active session before finalize incursion_id=%s",
                self.incursion_id,
            )
            service.end_session(self.era_id, self.period_id, self.incursion_id)
        try:
            logger.info(
                "Firestore finalize incursion incursion_id=%s", self.incursion_id
            )
            service.finalize_incursion(
                era_id=self.era_id,
                period_id=self.period_id,
                incursion_id=self.incursion_id,
                result=result_value,
                dahan_alive=dahan_alive,
                blight_on_island=blight_on_island,
                player_count=2,
                invader_cards_remaining=invader_cards_remaining,
                invader_cards_out_of_deck=invader_cards_out_of_deck,
            )
        except ValueError as exc:
            self.show_toast(str(exc))
            return
        self.toggle_finalize_confirm(False)
        self.load_detail(service)

    def handle_session_action(self, service: FirestoreService) -> None:
        if self.session_state == SESSION_STATE_FINALIZED:
            self.show_toast("La incursión ya está finalizada.")
            return
        if not self.era_id or not self.period_id or not self.incursion_id:
            return
        if self.open_session:
            logger.info(
                "Firestore end session incursion_id=%s", self.incursion_id
            )
            service.end_session(self.era_id, self.period_id, self.incursion_id)
            self.load_detail(service)
            return
        if not self.adversary_level or self.detail.difficulty is None:
            self.show_toast("Debes seleccionar un nivel válido.")
            return
        try:
            logger.info(
                "Firestore start session incursion_id=%s", self.incursion_id
            )
            service.start_session(self.era_id, self.period_id, self.incursion_id)
        except ValueError as exc:
            logger.error("Failed to start session error=%s", exc, exc_info=True)
            self.show_toast(str(exc))
            return
        self.load_detail(service)

    def show_toast(self, text: str) -> None:
        logger.info("User message shown: %s", text)
        self.toast_message = text
        self.toast_version += 1

    def consume_toast(self) -> None:
        self.toast_message = None

    def tick_timer(self) -> None:
        if not self.timer_running:
            return
        self.timer_now = datetime.now(timezone.utc)

    def request_score_dialog(self) -> None:
        if not self.detail:
            return
        self.score_dialog_open = True
        self.score_dialog_version += 1

    def close_score_dialog(self) -> None:
        if not self.score_dialog_open:
            return
        self.score_dialog_open = False
        self.score_dialog_version += 1

    def available_adversary_levels(self) -> list[str]:
        if not self.detail:
            return []
        levels = get_adversary_levels(self.detail.adversary_id)
        return [level.level for level in levels]

    def score_preview(self) -> tuple[str, int | None]:
        if not self.detail:
            return ("—", None)
        difficulty = self.detail.difficulty or 0
        dahan_alive = self._parse_int(self.finalize_form.dahan_alive, 0) or 0
        blight_on_island = self._parse_int(self.finalize_form.blight_on_island, 0) or 0
        invader_cards_remaining = (
            self._parse_int(self.finalize_form.invader_cards_remaining, 0) or 0
        )
        invader_cards_out_of_deck = (
            self._parse_int(self.finalize_form.invader_cards_out_of_deck, 0) or 0
        )
        player_count = self.detail.player_count or 2
        return compute_score_preview(
            self.finalize_form.result,
            difficulty,
            dahan_alive,
            blight_on_island,
            player_count,
            invader_cards_remaining,
            invader_cards_out_of_deck,
        )
