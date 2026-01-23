from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


def eras_view(page: ft.Page, service: FirestoreService) -> ft.Control:
    logger.debug("Entering eras_view")
    title = ft.Text("Eras", size=22, weight=ft.FontWeight.BOLD)
    eras_list = ft.ListView(spacing=12, expand=True)

    def status_chip(label: str, color: str) -> ft.Container:
        logger.debug("Building status_chip label=%s color=%s", label, color)
        return ft.Container(
            content=ft.Text(label, size=12, color=ft.Colors.WHITE),
            bgcolor=color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

    def build_open_periods_handler(era_id: str):
        logger.debug("Binding open periods handler era_id=%s", era_id)
        return go_to(page, f"/eras/{era_id}")

    def build_open_active_handler(active_incursion):
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

    def show_message(text: str) -> None:
        logger.info("User message shown: %s", text)
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def handle_multiple_active_incursions(event: ft.ControlEvent) -> None:
        logger.warning("Multiple active incursions detected for era list.")
        show_message("Hay más de una incursión activa.")

    def count_active_incursions(era_id: str) -> int:
        logger.debug("Counting active incursions era_id=%s", era_id)
        total = 0
        for period in service.list_periods(era_id):
            for incursion in service.list_incursions(era_id, period["id"]):
                if incursion.get("started_at") and not incursion.get("ended_at"):
                    total += 1
        logger.debug("Active incursions count=%s era_id=%s", total, era_id)
        return total

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
            is_active = era.get("is_active")
            subtitle = "Activa" if is_active else "Inactiva"
            status_color = (
                ft.Colors.GREEN_600 if is_active else ft.Colors.GREY_500
            )
            active_count = count_active_incursions(era_id)
            active_incursion = (
                service.get_active_incursion(era_id) if active_count == 1 else None
            )
            actions = [
                ft.ElevatedButton(
                    "Ver periodos",
                    on_click=build_open_periods_handler(era_id),
                )
            ]
            if active_incursion:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=build_open_active_handler(active_incursion),
                    )
                )
            elif active_count > 1:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=handle_multiple_active_incursions,
                        disabled=True,
                    )
                )

            eras_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.STARS),
                                title=ft.Text(
                                    f"Era {idx}", weight=ft.FontWeight.BOLD
                                ),
                                subtitle=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                status_chip(subtitle, status_color),
                                                ft.Text(
                                                    f"Incursiones activas: {active_count}"
                                                ),
                                            ],
                                            spacing=8,
                                        )
                                    ],
                                    spacing=4,
                                ),
                            ),
                            ft.Row(
                                actions,
                                wrap=True,
                                spacing=8,
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
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
