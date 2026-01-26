from __future__ import annotations

import flet as ft

from app.screens.incursions.incursions_components import incursion_card
from app.screens.incursions.incursions_handlers import (
    build_open_incursion_handler,
    list_incursions,
)
from app.screens.incursions.incursions_state import (
    get_adversary_info,
    get_board_info,
    get_incursion_status,
    get_layout_info,
    get_spirit_info,
)
from app.screens.shared_components import header_text
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def incursions_view(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
    period_id: str,
) -> ft.Control:
    logger.debug("Entering incursions_view era_id=%s period_id=%s", era_id, period_id)
    title = header_text("Incursiones")
    incursions_list = ft.ListView(spacing=12, expand=True)

    def load_incursions() -> None:
        incursions_list.controls.clear()
        incursions = list_incursions(service, era_id, period_id)
        if not incursions:
            logger.info("No incursions available era_id=%s period_id=%s", era_id, period_id)
            incursions_list.controls.append(ft.Text("No hay incursiones disponibles."))
            page.update()
            return
        for incursion in incursions:
            incursion_id = incursion["id"]
            status_label, status_color = get_incursion_status(incursion)
            incursions_list.controls.append(
                incursion_card(
                    f"Incursión {incursion.get('index', 0)}",
                    get_spirit_info(incursion),
                    get_board_info(incursion),
                    get_layout_info(incursion),
                    get_adversary_info(incursion),
                    status_label,
                    status_color,
                    build_open_incursion_handler(
                        page,
                        era_id,
                        period_id,
                        incursion_id,
                    ),
                )
            )
        page.update()
        logger.debug("Incursions loaded count=%s", len(incursions))

    load_incursions()

    logger.debug("Exiting incursions_view era_id=%s period_id=%s", era_id, period_id)
    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Incursiones"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        title,
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
