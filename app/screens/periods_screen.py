from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.screens.data_lookup import (
    get_adversary_catalog,
    get_spirit_name,
)


def periods_view(page: ft.Page, service: FirestoreService, era_id: str) -> ft.Control:
    title = ft.Text("Era", size=22, weight=ft.FontWeight.BOLD)
    periods_list = ft.ListView(spacing=12, expand=True)

    def navigate_to(route: str) -> None:
        page.go(route)

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

    def open_assignment_dialog(period_id: str, incursions: list[dict]) -> None:
        selections: dict[str, str | None] = {
            incursion["id"]: incursion.get("adversary_id") for incursion in incursions
        }
        options = [
            ft.dropdown.Option(item.adversary_id, item.name)
            for item in sorted(
                get_adversary_catalog().values(), key=lambda item: item.name
            )
        ]

        def build_incursion_card(incursion: dict) -> ft.Card:
            selector = ft.Dropdown(
                label="Adversario",
                options=options,
                value=selections.get(incursion["id"]),
            )

            def handle_select(event: ft.ControlEvent) -> None:
                selections[incursion["id"]] = selector.value

            selector.on_change = handle_select
            return ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.MAP),
                                title=ft.Text(
                                    f"Incursión {incursion.get('index', 0)}",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                subtitle=ft.Text(
                                    f"Espíritus: "
                                    f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
                                    f"{get_spirit_name(incursion.get('spirit_2_id'))}"
                                ),
                            ),
                            selector,
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
            try:
                service.assign_period_adversaries(
                    era_id,
                    period_id,
                    selections,
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

        page.pop_dialog()
        load_periods()
        page.update()

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
        page.show_dialog(dialog)

    def load_periods() -> None:
        periods_list.controls.clear()
        periods = service.list_periods(era_id)
        if not periods:
            periods_list.controls.append(ft.Text("No hay periodos disponibles."))
            page.update()
            return
        for idx, period in enumerate(periods):
            period_id = period["id"]
            actions: list[ft.Control] = []
            if period.get("ended_at"):
                actions.append(
                    ft.ElevatedButton(
                        "Ver resultados",
                        on_click=lambda event, pid=period_id: navigate_to(
                            f"/eras/{era_id}/periods/{pid}"
                        ),
                    )
                )
            elif period.get("adversaries_assigned_at"):
                actions.append(
                    ft.ElevatedButton(
                        "Ver incursiones",
                        on_click=lambda event, pid=period_id: navigate_to(
                            f"/eras/{era_id}/periods/{pid}"
                        ),
                    )
                )
            elif period.get("revealed_at"):
                actions.append(
                    ft.OutlinedButton(
                        "Asignar adversarios",
                        on_click=lambda event, pid=period_id: open_assignment_dialog(
                            pid, service.list_incursions(era_id, pid)
                        ),
                    )
                )
            elif can_reveal(periods, idx):
                actions.append(
                    ft.OutlinedButton(
                        "Revelar periodo",
                        on_click=lambda event, pid=period_id: open_reveal_dialog(pid),
                    )
                )

            periods_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.CALENDAR_TODAY),
                                title=ft.Text(
                                    f"Periodo {period.get('index', 0)}",
                                    weight=ft.FontWeight.BOLD,
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

    load_periods()

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Periodos"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        periods_list,
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
