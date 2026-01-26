from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


def show_message(page: ft.Page, text: str) -> None:
    logger.info("User message shown: %s", text)
    page.snack_bar = ft.SnackBar(ft.Text(text))
    page.snack_bar.open = True
    page.update()


def build_open_periods_handler(page: ft.Page, era_id: str):
    logger.debug("Binding open periods handler era_id=%s", era_id)
    return go_to(page, f"/eras/{era_id}")


def build_open_active_handler(page: ft.Page, active_incursion):
    logger.debug(
        "Binding open active incursion handler active_incursion=%s",
        active_incursion,
    )
    return go_to(
        page,
        (
            f"/eras/{active_incursion.era_id}/periods/{active_incursion.period_id}"
            f"/incursions/{active_incursion.incursion_id}"
        ),
    )


def handle_multiple_active_incursions(page: ft.Page, event: ft.ControlEvent) -> None:
    logger.warning("Multiple active incursions detected for era list.")
    show_message(page, "Hay más de una incursión activa.")


def count_active_incursions(service: FirestoreService, era_id: str) -> int:
    logger.debug("Counting active incursions era_id=%s", era_id)
    total = 0
    for period in service.list_periods(era_id):
        for incursion in service.list_incursions(era_id, period["id"]):
            if incursion.get("started_at") and not incursion.get("ended_at"):
                total += 1
    logger.debug("Active incursions count=%s era_id=%s", total, era_id)
    return total


def get_active_incursion(service: FirestoreService, era_id: str, active_count: int):
    if active_count == 1:
        return service.get_active_incursion(era_id)
    return None
