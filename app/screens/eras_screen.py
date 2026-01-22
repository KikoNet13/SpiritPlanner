from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService


def eras_view(page: ft.Page, service: FirestoreService) -> ft.View:
    title = ft.Text("Eras", size=22, weight=ft.FontWeight.BOLD)
    eras_column = ft.Column(spacing=10)

    def load_eras() -> None:
        eras_column.controls.clear()
        eras = service.list_eras()
        if not eras:
            eras_column.controls.append(ft.Text("No hay Eras disponibles."))
            page.update()
            return

        for era in eras:
            era_id = era["id"]
            is_active = era.get("is_active")
            subtitle = "Activa" if is_active else "Inactiva"
            button = ft.ElevatedButton(
                text="Ver periodos",
                on_click=lambda event, era_id=era_id: page.go(f"/eras/{era_id}"),
            )
            eras_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"Era {era_id}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"Estado: {subtitle}"),
                            button,
                        ]
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=6,
                )
            )
        page.update()

    def go_to_active_incursion() -> None:
        eras = service.list_eras()
        for era in eras:
            era_id = era["id"]
            active = service.get_active_incursion(era_id)
            if active:
                page.go(
                    f"/eras/{active.era_id}/periods/{active.period_id}/incursions/{active.incursion_id}"
                )
                return
        page.snack_bar = ft.SnackBar(ft.Text("No hay incursiones activas."))
        page.snack_bar.open = True
        page.update()

    load_eras()

    return ft.View(
        route="/eras",
        controls=[
            ft.AppBar(title=ft.Text("SpiritPlanner")),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        ft.ElevatedButton(
                            text="Ir a incursión activa",
                            on_click=lambda event: go_to_active_incursion(),
                        ),
                        eras_column,
                    ],
                    expand=True,
                ),
                padding=16,
            ),
        ],
    )
