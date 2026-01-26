from __future__ import annotations

import flet as ft

from app.screens.eras.eras_components import era_card
from app.screens.eras.eras_handlers import (
    build_open_active_handler,
    build_open_periods_handler,
    count_active_incursions,
    get_active_incursion,
    handle_multiple_active_incursions,
)
from app.screens.eras.eras_state import get_era_status, get_incursion_status
from app.screens.shared_components import header_text
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def eras_view(page: ft.Page, service: FirestoreService) -> ft.Control:
    logger.debug("Entering eras_view")
    title = header_text("Eras")
    eras_list = ft.ListView(spacing=12, expand=True)

    def load_eras() -> None:
        logger.debug("Loading eras list")
        eras_list.controls.clear()
        eras = service.list_eras()
        if not eras:
            logger.info("No eras available")
            eras_list.controls.append(ft.Text("No hay Eras disponibles."))
            page.update()
            return

        for idx, era in enumerate(eras, start=1):
            era_id = era["id"]
            logger.debug("Rendering era idx=%s era_id=%s", idx, era_id)
            status_label, status_color = get_era_status(era)
            active_count = count_active_incursions(service, era_id)
            incursion_label, incursion_color = get_incursion_status(active_count)
            active_incursion = get_active_incursion(service, era_id, active_count)
            actions: list[ft.Control] = [
                ft.ElevatedButton(
                    "Ver periodos",
                    on_click=build_open_periods_handler(page, era_id),
                )
            ]
            if active_incursion:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=build_open_active_handler(page, active_incursion),
                    )
                )
            elif active_count > 1:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=lambda event: handle_multiple_active_incursions(
                            page, event
                        ),
                        disabled=True,
                    )
                )

            eras_list.controls.append(
                era_card(
                    f"Era {idx}",
                    status_label,
                    status_color,
                    incursion_label,
                    incursion_color,
                    actions,
                )
            )
        page.update()
        logger.debug("Eras list loaded. total=%s", len(eras))

    load_eras()

    logger.debug("Exiting eras_view")
    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Eras"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        eras_list,
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
