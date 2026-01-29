from __future__ import annotations

import flet as ft

from app.utils.logger import get_logger

logger = get_logger(__name__)


def show_dialog(page: ft.Page, dialog: ft.AlertDialog) -> None:
    logger.debug("Showing dialog title=%s", dialog.title)
    try:
        page.show_dialog(dialog)
    except Exception as exc:
        logger.warning("Failed to show dialog title=%s error=%s", dialog.title, exc)


def close_dialog(page: ft.Page) -> None:
    logger.debug("Closing dialog")
    try:
        page.pop_dialog()
    except Exception as exc:
        logger.warning("Failed to close dialog error=%s", exc)
