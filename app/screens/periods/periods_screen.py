from __future__ import annotations

import flet as ft

from app.screens.data_lookup import get_adversary_catalog, get_spirit_name
from app.screens.periods.periods_components import incursions_preview, period_card
from app.screens.periods.periods_handlers import (
    assign_period_adversaries,
    close_dialog,
    reveal_period,
)
from app.screens.periods.periods_state import can_reveal, get_period_action
from app.screens.shared_components import header_text
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


def periods_view(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
) -> ft.Control:
    logger.debug("Entering periods_view era_id=%s", era_id)
    title = header_text("Era")
    periods_list = ft.ListView(spacing=12, expand=True)

    def build_open_period_handler(period_id: str):
        logger.debug("Binding open period handler period_id=%s", period_id)
        return go_to(page, f"/eras/{era_id}/periods/{period_id}")

    def open_assignment_dialog(period_id: str, incursions: list[dict]) -> None:
        logger.info(
            "Opening assignment dialog period_id=%s incursions_count=%s",
            period_id,
            len(incursions),
        )
        selections: dict[str, str | None] = {
            incursion["id"]: incursion.get("adversary_id") for incursion in incursions
        }
        selectors: dict[str, ft.Dropdown] = {}
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
            selectors[incursion["id"]] = selector

            def handle_select(event: ft.ControlEvent) -> None:
                logger.info(
                    "Adversary selection changed incursion_id=%s selection=%s",
                    incursion["id"],
                    selector.value,
                )
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
            logger.info("Saving adversary assignments period_id=%s", period_id)
            for incursion_id, selector in selectors.items():
                selections[incursion_id] = selector.value
            success = assign_period_adversaries(
                page,
                service,
                era_id,
                period_id,
                selections,
            )
            if not success:
                return
            close_dialog(page, dialog)
            load_periods()

        def handle_cancel_click(event: ft.ControlEvent) -> None:
            logger.info("Assignment dialog cancelled period_id=%s", period_id)
            close_dialog(page, dialog)

        def handle_save_click(event: ft.ControlEvent) -> None:
            handle_save(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Asignar adversarios"),
            content=list_view,
            actions=[
                ft.TextButton("Cancelar", on_click=handle_cancel_click),
                ft.ElevatedButton(
                    "Guardar",
                    on_click=handle_save_click,
                ),
            ],
        )
        page.show_dialog(dialog)
        logger.debug("Assignment dialog shown period_id=%s", period_id)

    def build_open_assignment_handler(period_id: str):
        def handler(event: ft.ControlEvent) -> None:
            logger.info("Open assignment dialog clicked period_id=%s", period_id)
            open_assignment_dialog(
                period_id, service.list_incursions(era_id, period_id)
            )

        return handler

    def build_reveal_period_handler(period_id: str):
        def handler(event: ft.ControlEvent) -> None:
            logger.info("Reveal period clicked period_id=%s", period_id)
            if reveal_period(page, service, era_id, period_id):
                load_periods()
                page.update()

        return handler

    def build_incursions_section(period_id: str) -> ft.Control:
        logger.debug("Building incursions section period_id=%s", period_id)
        incursions = service.list_incursions(era_id, period_id)
        if not incursions:
            return ft.Container()
        entries: list[ft.Control] = []
        for incursion in incursions:
            spirit_1 = get_spirit_name(incursion.get("spirit_1_id"))
            spirit_2 = get_spirit_name(incursion.get("spirit_2_id"))
            entries.append(
                ft.Text(
                    f"Incursión {incursion.get('index', 0)}: "
                    f"{spirit_1} / {spirit_2}"
                )
            )
        return incursions_preview(entries)

    def load_periods() -> None:
        logger.debug("Loading periods for era_id=%s", era_id)
        periods_list.controls.clear()
        periods = service.list_periods(era_id)
        if not periods:
            logger.info("No periods available era_id=%s", era_id)
            periods_list.controls.append(ft.Text("No hay periodos disponibles."))
            page.update()
            return
        for idx, period in enumerate(periods):
            period_id = period["id"]
            logger.debug("Rendering period idx=%s period_id=%s", idx, period_id)
            actions: list[ft.Control] = []
            actions_alignment = ft.MainAxisAlignment.END
            action = get_period_action(period, can_reveal(periods, idx))
            if action == "results":
                actions.append(
                    ft.ElevatedButton(
                        "Ver resultados",
                        on_click=build_open_period_handler(period_id),
                    )
                )
            elif action == "incursions":
                actions.append(
                    ft.ElevatedButton(
                        "Ver incursiones",
                        on_click=build_open_period_handler(period_id),
                    )
                )
            elif action == "assign":
                actions.append(
                    ft.OutlinedButton(
                        "Asignar adversarios",
                        on_click=build_open_assignment_handler(period_id),
                    )
                )
            elif action == "reveal":
                actions_alignment = ft.MainAxisAlignment.CENTER
                actions.append(
                    ft.ElevatedButton(
                        "Revelar periodo",
                        on_click=build_reveal_period_handler(period_id),
                        height=48,
                        width=240,
                    )
                )

            incursions_section = (
                build_incursions_section(period_id)
                if period.get("revealed_at")
                else ft.Container()
            )
            periods_list.controls.append(
                period_card(
                    f"Periodo {period.get('index', 0)}",
                    actions,
                    incursions_section,
                    actions_alignment=actions_alignment,
                )
            )
        page.update()
        logger.debug("Periods loaded total=%s", len(periods))

    load_periods()

    logger.debug("Exiting periods_view era_id=%s", era_id)
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
