from __future__ import annotations

from typing import Callable

import flet as ft

from app.core.diagnostics.debug_reporter import build_debug_report
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_report_title(context: dict[str, object]) -> str:
    screen = context.get("screen")
    action = context.get("action")
    if screen and action:
        return f"Error en {screen}: {action}"
    if screen:
        return f"Error en {screen}"
    if action:
        return f"Error en {action}"
    return "Error inesperado"


def _show_debug_dialog(page: ft.Page, report: str) -> None:
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Error"),
        content=ft.Column(
            [
                ft.Text(
                    "Se ha producido un error. Copia el informe y compártelo."
                ),
                ft.TextField(
                    value=report,
                    read_only=True,
                    multiline=True,
                    min_lines=12,
                    max_lines=18,
                ),
            ],
            tight=True,
            spacing=12,
        ),
        actions=[ft.TextButton("Cerrar")],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def handle_close(_: ft.ControlEvent) -> None:
        dialog.open = False
        page.update()

    dialog.actions[0].on_click = handle_close
    page.dialog = dialog
    dialog.open = True
    page.update()


def safe_event_handler(
    page: ft.Page,
    fn: Callable[[], None],
    context_provider: Callable[[], dict] | None = None,
) -> Callable[[ft.ControlEvent], None]:
    def handler(event: ft.ControlEvent) -> None:
        try:
            fn()
        except Exception as exc:
            context = context_provider() if context_provider else {}
            title = _build_report_title(context)
            logger.exception("Unhandled error in handler title=%s", title)
            report = build_debug_report(title=title, context=context, exc=exc)
            _show_debug_dialog(page, report)

    return handler
