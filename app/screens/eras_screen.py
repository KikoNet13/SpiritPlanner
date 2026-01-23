from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService


def eras_view(page: ft.Page, service: FirestoreService) -> ft.View:
    title = ft.Text("Eras", size=22, weight=ft.FontWeight.BOLD)
    eras_list = ft.ListView(spacing=12, expand=True)

    def status_chip(label: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=12, color=ft.colors.WHITE),
            bgcolor=color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

    def show_message(text: str) -> None:
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def count_active_incursions(era_id: str) -> int:
        total = 0
        for period in service.list_periods(era_id):
            for incursion in service.list_incursions(era_id, period["id"]):
                if incursion.get("started_at") and not incursion.get("ended_at"):
                    total += 1
        return total

    def load_eras() -> None:
        eras_list.controls.clear()
        eras = service.list_eras()
        if not eras:
            eras_list.controls.append(ft.Text("No hay Eras disponibles."))
            page.update()
            return

        for idx, era in enumerate(eras, start=1):
            era_id = era["id"]
            is_active = era.get("is_active")
            subtitle = "Activa" if is_active else "Inactiva"
            status_color = (
                ft.colors.GREEN_600 if is_active else ft.colors.GREY_500
            )
            active_count = count_active_incursions(era_id)
            active_incursion = (
                service.get_active_incursion(era_id) if active_count == 1 else None
            )
            actions = [
                ft.ElevatedButton(
                    "Ver periodos",
                    on_click=lambda event, era_id=era_id: page.go(f"/eras/{era_id}"),
                )
            ]
            if active_incursion:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=lambda event, active=active_incursion: page.go(
                            f"/eras/{active.era_id}/periods/{active.period_id}/incursions/{active.incursion_id}"
                        ),
                    )
                )
            elif active_count > 1:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=lambda event: show_message(
                            "Hay más de una incursión activa."
                        ),
                        disabled=True,
                    )
                )

            eras_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.AUTO_AWESOME),
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
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=12,
                )
            )
        page.update()

    load_eras()

    return ft.View(
        route="/eras",
        controls=[
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
            ),
        ],
    )
