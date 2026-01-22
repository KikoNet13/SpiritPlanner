from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService


def incursions_view(
    page: ft.Page, service: FirestoreService, era_id: str, period_id: str
) -> ft.View:
    title = ft.Text("Incursiones", size=22, weight=ft.FontWeight.BOLD)
    incursions_column = ft.Column(spacing=10)

    def load_incursions() -> None:
        incursions_column.controls.clear()
        incursions = service.list_incursions(era_id, period_id)
        if not incursions:
            incursions_column.controls.append(
                ft.Text("No hay incursiones disponibles.")
            )
            page.update()
            return
        for incursion in incursions:
            incursion_id = incursion["id"]
            status = "No iniciado"
            if incursion.get("ended_at"):
                status = "Finalizado"
            elif incursion.get("started_at"):
                status = "Activo"
            spirit_info = f"{incursion.get('spirit_1_id', '')} / {incursion.get('spirit_2_id', '')}"
            board_info = (
                f"{incursion.get('board_1', '')} + {incursion.get('board_2', '')}"
            )

            incursions_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"Incursión {incursion.get('index', 0)}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(f"Espíritus: {spirit_info}"),
                            ft.Text(f"Tableros: {board_info}"),
                            ft.Text(f"Estado: {status}"),
                            ft.ElevatedButton(
                                "Abrir",
                                on_click=lambda event, iid=incursion_id: page.go(
                                    f"/eras/{era_id}/periods/{period_id}/incursions/{iid}"
                                ),
                            ),
                        ]
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=6,
                )
            )
        page.update()

    load_incursions()

    return ft.View(
        route=f"/eras/{era_id}/periods/{period_id}",
        controls=[
            ft.AppBar(title=ft.Text("Incursiones")),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        incursions_column,
                    ],
                    expand=True,
                ),
                padding=16,
            ),
        ],
    )
