from __future__ import annotations

import asyncio

import flet as ft

from app.screens.incursions.incursions_model import IncursionCardModel
from app.screens.incursions.incursions_viewmodel import IncursionsViewModel
from app.screens.shared_components import header_text, section_card, status_chip
from app.utils.logger import get_logger
from app.utils.navigation import navigate

logger = get_logger(__name__)


def _incursion_card(
    model: IncursionCardModel,
    on_open,
) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.EXPLORE),
                    title=ft.Text(model.title, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Column(
                        [
                            ft.Text(f"Espíritus: {model.spirit_info}"),
                            ft.Text(f"Tableros: {model.board_info}"),
                            ft.Text(f"Distribución: {model.layout_info}"),
                            ft.Text(f"Adversario: {model.adversary_info}"),
                            status_chip(model.status_label, model.status_color),
                        ],
                        spacing=4,
                    ),
                ),
                ft.Row(
                    [
                        ft.ElevatedButton("Abrir", on_click=on_open),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=4,
        )
    )


@ft.component
def incursions_view(
    era_id: str,
    period_id: str,
) -> ft.Control:
    logger.debug("Rendering incursions_view era_id=%s period_id=%s", era_id, period_id)
    page = ft.context.page
    service = page.session.get("firestore_service")
    view_model, _ = ft.use_state(IncursionsViewModel())

    def load() -> None:
        view_model.ensure_loaded(service, era_id, period_id)

    ft.use_effect(load, [era_id, period_id])

    def show_toast() -> None:
        if not view_model.toast_message:
            return
        page.show_dialog(ft.SnackBar(ft.Text(view_model.toast_message)))
        view_model.consume_toast()

    ft.use_effect(show_toast, [view_model.toast_version])

    def handle_navigation() -> None:
        if not view_model.navigate_to:
            return
        target = view_model.navigate_to

        async def do_navigation() -> None:
            await navigate(page, target)

        if hasattr(page, "run_task"):
            page.run_task(do_navigation)
        else:
            asyncio.create_task(do_navigation())
        view_model.consume_navigation()

    ft.use_effect(handle_navigation, [view_model.nav_version])

    content_controls: list[ft.Control] = []
    if view_model.loading:
        content_controls.append(ft.ProgressRing())
    elif not view_model.incursions:
        content_controls.append(ft.Text("No hay incursiones disponibles."))
    else:
        for incursion in view_model.incursions:
            content_controls.append(
                _incursion_card(
                    incursion,
                    lambda _: view_model.request_open_incursion(
                        incursion.incursion_id
                    ),
                )
            )

    incursions_list = ft.ListView(spacing=12, expand=True, controls=content_controls)

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Incursiones"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        header_text("Incursiones"),
                        incursions_list,
                    ],
                    expand=True,
                ),
                padding=16,
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )
