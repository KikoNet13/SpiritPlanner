from __future__ import annotations

from typing import Callable

import flet as ft

from app.services.firestore_service import FirestoreService
from app.screens.data_lookup import (
    get_adversary_catalog,
    get_adversary_name,
    get_spirit_name,
)


def periods_view(page: ft.Page, service: FirestoreService, era_id: str) -> ft.View:
    title = ft.Text("Era", size=22, weight=ft.FontWeight.BOLD)
    periods_list = ft.ListView(spacing=12, expand=True)

    def can_reveal(periods: list[dict], index: int) -> bool:
        if index == 0:
            return True
        previous = periods[index - 1]
        return bool(previous.get("ended_at"))

    def show_message(text: str) -> None:
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def close_dialog(dialog: ft.AlertDialog) -> None:
        dialog.open = False
        page.update()

    def open_adversary_selector(
        incursion: dict, on_select: Callable[[str], None]
    ) -> None:
        spirit_info = (
            f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
            f"{get_spirit_name(incursion.get('spirit_2_id'))}"
        )
        options = sorted(
            get_adversary_catalog().values(), key=lambda item: item.name
        )
        list_view = ft.ListView(spacing=8, expand=True)

        def handle_select(adversary_id: str) -> None:
            on_select(adversary_id)
            close_dialog(dialog)

        for option in options:
            list_view.controls.append(
                ft.Card(
                    content=ft.ListTile(
                        title=ft.Text(option.name),
                        on_click=lambda event, aid=option.adversary_id: handle_select(
                            aid
                        ),
                    )
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seleccionar adversario"),
            content=ft.Column(
                [
                    ft.Text(f"Espíritus: {spirit_info}"),
                    list_view,
                ],
                tight=True,
                spacing=12,
            ),
            actions=[ft.TextButton("Cancelar", on_click=lambda event: close_dialog(dialog))],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def open_assignment_dialog(period_id: str, incursions: list[dict]) -> None:
        selections: dict[str, str | None] = {
            incursion["id"]: incursion.get("adversary_id") for incursion in incursions
        }

        def build_incursion_card(incursion: dict) -> ft.Card:
            adversary_label = ft.Text(
                get_adversary_name(selections.get(incursion["id"]))
            )

            def handle_select(adversary_id: str) -> None:
                selections[incursion["id"]] = adversary_id
                adversary_label.value = get_adversary_name(adversary_id)
                page.update()

            return ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"Incursión {incursion.get('index', 0)}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"Espíritus: "
                                f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
                                f"{get_spirit_name(incursion.get('spirit_2_id'))}"
                            ),
                            ft.Row(
                                [
                                    ft.Text("Adversario:"),
                                    adversary_label,
                                ],
                                wrap=True,
                                spacing=6,
                            ),
                            ft.OutlinedButton(
                                "Elegir adversario",
                                on_click=lambda event: open_adversary_selector(
                                    incursion, handle_select
                                ),
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=10,
                )
            )

        list_view = ft.ListView(spacing=12, expand=True)
        for incursion in incursions:
            list_view.controls.append(build_incursion_card(incursion))

        def handle_save(dialog: ft.AlertDialog) -> None:
            selected = list(selections.values())
            if any(not value for value in selected):
                show_message("Debes asignar adversario a todas las incursiones.")
                return
            if len(set(selected)) != len(selected):
                show_message("Los adversarios deben ser distintos en el periodo.")
                return
            try:
                for incursion in incursions:
                    service.set_incursion_adversary(
                        era_id,
                        period_id,
                        incursion["id"],
                        selections.get(incursion["id"]),
                    )
            except ValueError as exc:
                show_message(str(exc))
                return
            close_dialog(dialog)
            load_periods()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Asignar adversarios"),
            content=list_view,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda event: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Guardar",
                    on_click=lambda event: handle_save(dialog),
                ),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def handle_reveal(period_id: str, dialog: ft.AlertDialog) -> None:
        try:
            service.reveal_period(era_id, period_id)
        except ValueError as exc:
            show_message(str(exc))
            return
        close_dialog(dialog)
        incursions = service.list_incursions(era_id, period_id)
        open_assignment_dialog(period_id, incursions)

    def open_reveal_dialog(period_id: str) -> None:
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Revelar periodo"),
            content=ft.Text(
                "Se revelarán las incursiones y podrás asignar adversarios."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda event: close_dialog(dialog)),
                ft.ElevatedButton(
                    "Revelar",
                    on_click=lambda event: handle_reveal(period_id, dialog),
                ),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def load_periods() -> None:
        periods_list.controls.clear()
        periods = service.list_periods(era_id)
        if not periods:
            periods_list.controls.append(ft.Text("No hay periodos disponibles."))
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

            actions: list[ft.Control] = []
            if period.get("revealed_at"):
                actions.append(
                    ft.ElevatedButton(
                        "Ver incursiones",
                        on_click=lambda event, pid=period_id: page.go(
                            f"/eras/{era_id}/periods/{pid}"
                        ),
                    )
                )
            if not period.get("revealed_at") and can_reveal(periods, idx):
                actions.append(
                    ft.OutlinedButton(
                        "Revelar periodo",
                        on_click=lambda event, pid=period_id: open_reveal_dialog(pid),
                    )
                )

            periods_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Periodo {period.get('index', 0)}",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(f"Estado: {status}"),
                                ft.Row(actions, wrap=True),
                            ],
                            spacing=8,
                        ),
                        padding=12,
                    )
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
                        periods_list,
                    ],
                    expand=True,
                ),
                padding=16,
            ),
        ],
    )
