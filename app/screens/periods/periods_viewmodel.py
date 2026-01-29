from __future__ import annotations

import flet as ft

from app.screens.periods.periods_model import (
    AssignmentIncursionModel,
    PeriodRowModel,
    build_assignment_incursions,
    build_period_rows,
)
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


@ft.observable
class PeriodsViewModel:
    def __init__(
        self, page: ft.Page, service: FirestoreService, era_id: str
    ) -> None:
        self.page = page
        self.service = service
        self.era_id = era_id
        self.rows: list[PeriodRowModel] = []
        self.loading = False
        self.error: str | None = None
        self.assignment_period_id: str | None = None
        self.assignment_incursions: list[AssignmentIncursionModel] = []
        self.assignment_selections: dict[str, str | None] = {}
        self.assignment_errors: dict[str, bool] = {}
        self.assignment_open = False
        self.assignment_version = 0
        self.message_text: str | None = None
        self.message_version = 0

    def load_periods(self) -> None:
        logger.info("Firestore list periods era_id=%s", self.era_id)
        self.loading = True
        self.error = None
        try:
            periods = self.service.list_periods(self.era_id)
            incursions_by_period: dict[str, list[dict]] = {}
            for period in periods:
                if period.get("revealed_at"):
                    incursions_by_period[period["id"]] = self.service.list_incursions(
                        self.era_id, period["id"]
                    )
            self.rows = build_period_rows(periods, incursions_by_period)
        except Exception as exc:
            logger.error(
                "Failed to load periods era_id=%s error=%s",
                self.era_id,
                exc,
                exc_info=True,
            )
            self.error = "load_failed"
            self.rows = []
            self.show_message("No se pudieron cargar los periodos.")
        finally:
            self.loading = False

    def open_period_handler(self, period_id: str):
        logger.info("UI open period era_id=%s period_id=%s", self.era_id, period_id)
        return go_to(self.page, f"/eras/{self.era_id}/periods/{period_id}")

    def open_assignment_dialog(self, period_id: str) -> None:
        logger.info("UI open assignment dialog period_id=%s", period_id)
        incursions = self.service.list_incursions(self.era_id, period_id)
        pending = [item for item in incursions if not item.get("adversary_id")]
        if not pending:
            self.show_message("No hay incursiones pendientes de asignar.")
            return
        self.assignment_period_id = period_id
        self.assignment_incursions = build_assignment_incursions(pending)
        self.assignment_selections = {
            incursion["id"]: incursion.get("adversary_id") for incursion in pending
        }
        self.assignment_errors = {}
        self.assignment_open = True
        self.assignment_version += 1

    def reveal_period(self, period_id: str) -> None:
        logger.info("UI reveal period period_id=%s", period_id)
        try:
            logger.info(
                "Firestore reveal period era_id=%s period_id=%s",
                self.era_id,
                period_id,
            )
            self.service.reveal_period(self.era_id, period_id)
        except Exception as exc:
            logger.error(
                "Failed to reveal period era_id=%s period_id=%s error=%s",
                self.era_id,
                period_id,
                exc,
                exc_info=True,
            )
            self.show_message("No se pudo revelar el periodo.")
            return
        self.load_periods()

    def close_assignment_dialog(self) -> None:
        if not self.assignment_open:
            return
        logger.info(
            "UI close assignment dialog period_id=%s", self.assignment_period_id
        )
        self.assignment_open = False
        self.assignment_version += 1

    def set_assignment_selection(
        self, incursion_id: str, adversary_id: str | None
    ) -> None:
        self.assignment_selections[incursion_id] = adversary_id
        if incursion_id in self.assignment_errors:
            self.assignment_errors.pop(incursion_id, None)
        self.assignment_version += 1

    def validate_assignments(self) -> bool:
        missing = [
            incursion_id
            for incursion_id, value in self.assignment_selections.items()
            if not value
        ]
        if not missing:
            return True
        self.assignment_errors = {incursion_id: True for incursion_id in missing}
        self.assignment_version += 1
        self.show_message("Selecciona un adversario para cada incursión.")
        return False

    def save_assignment(self) -> None:
        if not self.assignment_period_id:
            return
        logger.info(
            "UI save assignment period_id=%s",
            self.assignment_period_id,
        )
        if not self.validate_assignments():
            return
        try:
            logger.info(
                "Firestore assign period adversaries era_id=%s period_id=%s",
                self.era_id,
                self.assignment_period_id,
            )
            self.service.assign_period_adversaries(
                self.era_id,
                self.assignment_period_id,
                self.assignment_selections,
            )
        except Exception as exc:
            logger.error(
                "Failed to assign adversaries era_id=%s period_id=%s error=%s",
                self.era_id,
                self.assignment_period_id,
                exc,
                exc_info=True,
            )
            self.show_message("No se pudieron asignar los adversarios.")
            return
        self.assignment_open = False
        self.assignment_version += 1
        self.load_periods()

    def show_message(self, text: str) -> None:
        logger.info("User message shown: %s", text)
        self.message_text = text
        self.message_version += 1

    def clear_message(self) -> None:
        self.message_text = None
