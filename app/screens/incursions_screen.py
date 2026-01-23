from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.screens.data_lookup import (
    get_adversary_name,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)
from app.utils.navigation import go_to


def incursions_view(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
    period_id: str,
) -> ft.Control:
    title = ft.Text("Incursiones", size=22, weight=ft.FontWeight.BOLD)
    incursions_list = ft.ListView(spacing=12, expand=True)

    def status_chip(label: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=12, color=ft.Colors.WHITE),
            bgcolor=color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

    def build_open_incursion_handler(incursion_id: str):
        return go_to(
            page,
            f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
        )

    def load_incursions() -> None:
        incursions_list.controls.clear()
        incursions = service.list_incursions(era_id, period_id)
        if not incursions:
            incursions_list.controls.append(ft.Text("No hay incursiones disponibles."))
            page.update()
            return
        for incursion in incursions:
            incursion_id = incursion["id"]
            status = "No iniciado"
            status_color = ft.Colors.GREY_500
            if incursion.get("ended_at"):
                status = "Finalizado"
                status_color = ft.Colors.BLUE_600
            elif incursion.get("started_at"):
                status = "Activo"
                status_color = ft.Colors.GREEN_600
            spirit_info = (
                f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
                f"{get_spirit_name(incursion.get('spirit_2_id'))}"
            )
            board_info = (
                f"{get_board_name(incursion.get('board_1'))} + "
                f"{get_board_name(incursion.get('board_2'))}"
            )
            layout_info = get_layout_name(incursion.get("board_layout"))
            adversary_info = get_adversary_name(incursion.get("adversary_id"))

            incursions_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.EXPLORE),
                                title=ft.Text(
                                    f"Incursión {incursion.get('index', 0)}",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                subtitle=ft.Column(
                                    [
                                        ft.Text(f"Espíritus: {spirit_info}"),
                                        ft.Text(f"Tableros: {board_info}"),
                                        ft.Text(f"Distribución: {layout_info}"),
                                        ft.Text(f"Adversario: {adversary_info}"),
                                        status_chip(status, status_color),
                                    ],
                                    spacing=4,
                                ),
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Abrir",
                                        on_click=build_open_incursion_handler(
                                            incursion_id
                                        ),
                                    )
                                ],
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

    load_incursions()

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
