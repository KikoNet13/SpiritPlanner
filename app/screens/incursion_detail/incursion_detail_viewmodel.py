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
    get_result_label,
    get_score_formula,
    resolve_session_state,
)
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)


@ft.observable
class IncursionDetailViewModel:
    def __init__(
        self,
        page: ft.Page,
        service: FirestoreService,
        era_id: str,
        period_id: str,
        incursion_id: str,
    ) -> None:
        self.page = page
        self.service = service
        self.era_id = era_id
        self.period_id = period_id
        self.incursion_id = incursion_id
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
            player_count="2",
            dahan_alive="",
            blight_on_island="",
            invader_cards_remaining="",
            invader_cards_out_of_deck="",
        )
        self.show_finalize_confirm = False
        self.message_text: str | None = None
        self.message_version = 0
        self.timer_running = False
        self.timer_now: datetime | None = None

    def load_detail(self) -> None:
        logger.info(
            "Firestore load incursion detail era_id=%s period_id=%s incursion_id=%s",
            self.era_id,
            self.period_id,
            self.incursion_id,
        )
        self.loading = True
        self.error = None
        try:
            incursions = self.service.list_incursions(self.era_id, self.period_id)
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
                    for item in self.service.list_periods(self.era_id)
                    if item["id"] == self.period_id
                ),
                None,
            )
            sessions = self.service.list_sessions(
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
                board_1_name=get_board_name(incursion.get("board_1")),
                board_2_name=get_board_name(incursion.get("board_2")),
                layout_name=get_layout_name(incursion.get("board_layout")),
                adversary_id=incursion.get("adversary_id"),
                adversary_name=get_adversary_name(incursion.get("adversary_id")),
                adversary_level=incursion.get("adversary_level"),
                difficulty=incursion.get("difficulty"),
                period_label=build_period_label(period),
                result=incursion.get("result"),
                score=incursion.get("score"),
                player_count=incursion.get("player_count"),
                dahan_alive=incursion.get("dahan_alive"),
                blight_on_island=incursion.get("blight_on_island"),
                invader_cards_remaining=incursion.get("invader_cards_remaining"),
                invader_cards_out_of_deck=incursion.get("invader_cards_out_of_deck"),
            )
            self.detail = detail
            self.adversary_level = detail.adversary_level
            self.finalize_form = FinalizeFormData(
                result=detail.result,
                player_count=str(detail.player_count or 2),
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

    def update_adversary_level(self, level: str | None) -> None:
        if not self.detail:
            return
        if self.session_state == SESSION_STATE_FINALIZED or self.has_sessions:
            return
        adversary_id = self.detail.adversary_id
        if not adversary_id:
            self.show_message("No hay adversario asignado.")
            return
        difficulty = get_adversary_difficulty(adversary_id, level)
        logger.info(
            "Firestore update adversary level incursion_id=%s level=%s",
            self.incursion_id,
            level,
        )
        try:
            self.service.update_incursion_adversary_level(
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
            self.show_message(str(exc))
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
            player_count=value if field == "player_count" else data.player_count,
            dahan_alive=value if field == "dahan_alive" else data.dahan_alive,
            blight_on_island=value if field == "blight_on_island" else data.blight_on_island,
            invader_cards_remaining=(
                value
                if field == "invader_cards_remaining"
                else data.invader_cards_remaining
            ),
            invader_cards_out_of_deck=(
                value
                if field == "invader_cards_out_of_deck"
                else data.invader_cards_out_of_deck
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

    def finalize_incursion(self) -> None:
        if not self.detail:
            return
        if self.session_state == SESSION_STATE_FINALIZED:
            self.show_message("La incursión ya está finalizada.")
            return
        result_value = self.finalize_form.result
        if not result_value:
            self.show_message("Debes indicar el resultado.")
            return
        player_count = self._parse_int(self.finalize_form.player_count, 2)
        dahan_alive = self._parse_int(self.finalize_form.dahan_alive, 0)
        blight_on_island = self._parse_int(self.finalize_form.blight_on_island, 0)
        invader_remaining = self._parse_int(
            self.finalize_form.invader_cards_remaining, 0
        )
        invader_out = self._parse_int(self.finalize_form.invader_cards_out_of_deck, 0)
        if None in (
            player_count,
            dahan_alive,
            blight_on_island,
            invader_remaining,
            invader_out,
        ):
            self.show_message("Revisa los valores numéricos.")
            return
        if self.open_session:
            logger.info(
                "Closing active session before finalize incursion_id=%s",
                self.incursion_id,
            )
            self.service.end_session(self.era_id, self.period_id, self.incursion_id)
        try:
            logger.info(
                "Firestore finalize incursion incursion_id=%s", self.incursion_id
            )
            self.service.finalize_incursion(
                era_id=self.era_id,
                period_id=self.period_id,
                incursion_id=self.incursion_id,
                result=result_value,
                player_count=player_count,
                invader_cards_remaining=invader_remaining,
                invader_cards_out_of_deck=invader_out,
                dahan_alive=dahan_alive,
                blight_on_island=blight_on_island,
            )
        except ValueError:
            self.show_message("Revisa los valores numéricos.")
            return
        self.toggle_finalize_confirm(False)
        self.load_detail()

    def handle_session_action(self) -> None:
        if self.session_state == SESSION_STATE_FINALIZED:
            self.show_message("La incursión ya está finalizada.")
            return
        if self.open_session:
            logger.info(
                "Firestore end session incursion_id=%s", self.incursion_id
            )
            self.service.end_session(self.era_id, self.period_id, self.incursion_id)
            self.load_detail()
            return
        if not self.adversary_level or self.detail.difficulty is None:
            self.show_message("Debes seleccionar un nivel válido.")
            return
        try:
            logger.info(
                "Firestore start session incursion_id=%s", self.incursion_id
            )
            self.service.start_session(self.era_id, self.period_id, self.incursion_id)
        except ValueError as exc:
            logger.error("Failed to start session error=%s", exc, exc_info=True)
            self.show_message(str(exc))
            return
        self.load_detail()

    def show_message(self, text: str) -> None:
        logger.info("User message shown: %s", text)
        self.message_text = text
        self.message_version += 1

    def clear_message(self) -> None:
        self.message_text = None

    def tick_timer(self) -> None:
        if not self.timer_running:
            return
        self.timer_now = datetime.now(timezone.utc)

    def open_score_dialog(self) -> None:
        if not self.detail:
            return
        result_label = get_result_label(self.detail.result)
        difficulty_value = self.detail.difficulty or 0
        formula = get_score_formula(self.detail.result)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalle de puntuación"),
            content=ft.Column(
                [
                    ft.Text(f"Resultado: {result_label}"),
                    ft.Text(f"Dificultad: {difficulty_value}"),
                    ft.Text(f"Jugadores: {self.detail.player_count}"),
                    ft.Text(f"Dahan vivos: {self.detail.dahan_alive}"),
                    ft.Text(f"Plaga en la isla: {self.detail.blight_on_island}"),
                    ft.Text(
                        f"Cartas restantes: {self.detail.invader_cards_remaining}"
                    ),
                    ft.Text(
                        f"Cartas fuera del mazo: {self.detail.invader_cards_out_of_deck}"
                    ),
                    ft.Text(f"Fórmula: {formula}"),
                    ft.Text(
                        f"Puntuación: {self.detail.score}",
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: self.page.pop_dialog())
            ],
        )
        self.page.show_dialog(dialog)

    def available_adversary_levels(self) -> list[str]:
        if not self.detail:
            return []
        levels = get_adversary_levels(self.detail.adversary_id)
        return [level.level for level in levels]

    def score_preview(self) -> tuple[str, int | None]:
        if not self.detail:
            return ("—", None)
        difficulty = self.detail.difficulty or 0
        player_count = self._parse_int(self.finalize_form.player_count, 2) or 2
        dahan_alive = self._parse_int(self.finalize_form.dahan_alive, 0) or 0
        blight_on_island = self._parse_int(self.finalize_form.blight_on_island, 0) or 0
        invader_remaining = (
            self._parse_int(self.finalize_form.invader_cards_remaining, 0) or 0
        )
        invader_out = (
            self._parse_int(self.finalize_form.invader_cards_out_of_deck, 0) or 0
        )
        return compute_score_preview(
            self.finalize_form.result,
            difficulty,
            player_count,
            dahan_alive,
            blight_on_island,
            invader_remaining,
            invader_out,
        )
