from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def show_message(page: ft.Page, text: str) -> None:
    logger.info("User message shown: %s", text)
    page.snack_bar = ft.SnackBar(ft.Text(text))
    page.snack_bar.open = True
    page.update()


def close_dialog(page: ft.Page, dialog: ft.AlertDialog) -> None:
    logger.debug("Closing dialog title=%s", dialog.title)
    dialog.open = False
    page.update()


def assign_period_adversaries(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
    period_id: str,
    selections: dict[str, str | None],
) -> bool:
    logger.info("Saving adversary assignments period_id=%s", period_id)
    try:
        service.assign_period_adversaries(era_id, period_id, selections)
    except ValueError as exc:
        logger.warning(
            "Failed to assign adversaries period_id=%s error=%s",
            period_id,
            exc,
        )
        show_message(page, str(exc))
        return False
    return True


def reveal_period(
    page: ft.Page, service: FirestoreService, era_id: str, period_id: str
) -> bool:
    logger.info("Reveal period requested period_id=%s", period_id)
    try:
        service.reveal_period(era_id, period_id)
    except ValueError:
        logger.warning("Reveal period failed period_id=%s", period_id)
        return False
    logger.debug("Reveal period completed period_id=%s", period_id)
    return True
