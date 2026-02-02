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

logger = get_logger(__name__)


@ft.observable
class PeriodsViewModel:
    def __init__(self) -> None:
        self.era_id: str | None = None
        self.rows: list[PeriodRowModel] = []
        self.loading = False
        self.error: str | None = None
        self.assignment_period_id: str | None = None
        self.assignment_incursions: list[AssignmentIncursionModel] = []
        self.assignment_selections: dict[str, str | None] = {}
        self.assignment_errors: dict[str, bool] = {}
        self.assignment_open = False
        self.assignment_version = 0
        self.toast_message: str | None = None
        self.toast_version = 0
        self.navigate_to: str | None = None
        self.nav_version = 0

    def ensure_loaded(self, service: FirestoreService, era_id: str) -> None:
        self.era_id = era_id
        self.load_periods(service)

    def load_periods(self, service: FirestoreService) -> None:
        if not self.era_id:
            return
        logger.info("Firestore list periods era_id=%s", self.era_id)
        self.loading = True
        self.error = None
        try:
            periods = service.list_periods(self.era_id)
            incursions_by_period: dict[str, list[dict]] = {}
            for period in periods:
                if period.get("revealed_at"):
                    incursions_by_period[period["id"]] = service.list_incursions(
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
            self.show_toast("No se pudieron cargar los períodos.")
        finally:
            self.loading = False

    def request_open_period(self, period_id: str) -> None:
        if not self.era_id:
            return
        logger.info("UI open period era_id=%s period_id=%s", self.era_id, period_id)
        self.navigate_to = f"/eras/{self.era_id}/periods/{period_id}"
        self.nav_version += 1

    def open_assignment_dialog(
        self, service: FirestoreService, period_id: str
    ) -> None:
        if not self.era_id:
            return
        logger.info("UI open assignment dialog period_id=%s", period_id)
        incursions = service.list_incursions(self.era_id, period_id)
        pending = [item for item in incursions if not item.get("adversary_id")]
        if not pending:
            self.show_toast("No hay incursiones pendientes de asignar.")
            return
        self.assignment_period_id = period_id
        self.assignment_incursions = build_assignment_incursions(pending)
        self.assignment_selections = {
            incursion["id"]: incursion.get("adversary_id") for incursion in pending
        }
        self.assignment_errors = {}
        self.assignment_open = True
        self.assignment_version += 1

    def reveal_period(self, service: FirestoreService, period_id: str) -> None:
        if not self.era_id:
            return
        logger.info("UI reveal period period_id=%s", period_id)
        try:
            logger.info(
                "Firestore reveal period era_id=%s period_id=%s",
                self.era_id,
                period_id,
            )
            service.reveal_period(self.era_id, period_id)
        except Exception as exc:
            logger.error(
                "Failed to reveal period era_id=%s period_id=%s error=%s",
                self.era_id,
                period_id,
                exc,
                exc_info=True,
            )
            self.show_toast("No se pudo revelar el periodo.")
            return
        self.load_periods(service)

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
        self.show_toast("Selecciona un adversario para cada incursión.")
        return False

    def save_assignment(self, service: FirestoreService) -> None:
        if not self.assignment_period_id or not self.era_id:
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
            service.assign_period_adversaries(
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
            self.show_toast("No se pudieron asignar los adversarios.")
            return
        self.assignment_open = False
        self.assignment_version += 1
        self.load_periods(service)

    def show_toast(self, text: str) -> None:
        logger.info("User message shown: %s", text)
        self.toast_message = text
        self.toast_version += 1

    def consume_toast(self) -> None:
        self.toast_message = None

    def consume_navigation(self) -> None:
        self.navigate_to = None
