from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService


def periods_view(page: ft.Page, service: FirestoreService, era_id: str) -> ft.View:
    title = ft.Text(f"Era {era_id}", size=22, weight=ft.FontWeight.BOLD)
    periods_column = ft.Column(spacing=10)

    def can_reveal(periods: list[dict], index: int) -> bool:
        if index == 0:
            return True
        previous = periods[index - 1]
        return bool(previous.get("ended_at"))

    def handle_reveal(period_id: str, dialog: ft.AlertDialog, field: ft.TextField) -> None:
        if not field.value:
            field.error_text = "Debes indicar el adversario."
            page.update()
            return
        service.reveal_period(era_id, period_id, field.value)
        dialog.open = False
        page.update()
        load_periods()

    def open_reveal_dialog(period_id: str) -> None:
        adversary_field = ft.TextField(label="Adversario", hint_text="Ej. Brandenburgo")
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Revelar periodo"),
            content=adversary_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda event: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Revelar",
                    on_click=lambda event: handle_reveal(period_id, dialog, adversary_field),
                ),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def close_dialog(dialog: ft.AlertDialog) -> None:
        dialog.open = False
        page.update()

    def load_periods() -> None:
        periods_column.controls.clear()
        periods = service.list_periods(era_id)
        if not periods:
            periods_column.controls.append(ft.Text("No hay periodos disponibles."))
            page.update()
            return
        for idx, period in enumerate(periods):
            period_id = period["id"]
            status = "No revelado"
            if period.get("ended_at"):
                status = "Finalizado"
            elif period.get("started_at"):
                status = "Activo"
            elif period.get("revealed_at"):
                status = "Revelado"

            actions = [
                ft.ElevatedButton(
                    text="Ver incursiones",
                    on_click=lambda event, pid=period_id: page.go(
                        f"/eras/{era_id}/periods/{pid}"
                    ),
                )
            ]
            if not period.get("revealed_at") and can_reveal(periods, idx):
                actions.append(
                    ft.OutlinedButton(
                        text="Revelar periodo",
                        on_click=lambda event, pid=period_id: open_reveal_dialog(pid),
                    )
                )

            periods_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"Periodo {period.get('index', 0)}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(f"Estado: {status}"),
                            ft.Row(actions, wrap=True),
                        ]
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=6,
                )
            )
        page.update()

    load_periods()

    return ft.View(
        route=f"/eras/{era_id}",
        controls=[
            ft.AppBar(title=ft.Text("Periodos")),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        periods_column,
                    ],
                    expand=True,
                ),
                padding=16,
            ),
        ],
    )
