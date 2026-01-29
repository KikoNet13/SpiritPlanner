from __future__ import annotations

import flet as ft

from app.screens.data_lookup import get_adversary_catalog, get_spirit_name
from app.screens.periods.periods_components import incursions_preview, period_card
from app.screens.periods.periods_handlers import (
    assign_period_adversaries,
    reveal_period,
    show_message,
)
from app.screens.periods.periods_state import (
    AssignmentDialogState,
    PeriodRowState,
    PeriodsViewState,
    build_period_rows,
)
from app.screens.shared_components import header_text
from app.services.firestore_service import FirestoreService
from app.utils.dialogs import close_dialog, show_dialog
from app.utils.logger import get_logger, safe_event_handler
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
    view_state = PeriodsViewState(era_id=era_id)
    assignment_dialog = ft.AlertDialog(modal=True)

    def build_open_period_handler(period_id: str):
        logger.debug("Binding open period handler period_id=%s", period_id)
        return go_to(page, f"/eras/{era_id}/periods/{period_id}")

    def render_periods_list() -> None:
        if not view_state.rows:
            periods_list.controls = [ft.Text("No hay periodos disponibles.")]
        else:
            periods_list.controls = [build_period_card(row) for row in view_state.rows]

    def load_periods(update_list: bool = False) -> None:
        logger.debug("Loading periods for era_id=%s", era_id)
        view_state.loading = True
        view_state.error = None
        try:
            periods = service.list_periods(era_id)
            incursions_by_period: dict[str, list[dict]] = {}
            for period in periods:
                if period.get("revealed_at"):
                    incursions_by_period[period["id"]] = service.list_incursions(
                        era_id, period["id"]
                    )
            view_state.periods = periods
            view_state.rows = build_period_rows(periods, incursions_by_period)
        except Exception as exc:
            logger.error(
                "Failed to load periods era_id=%s error=%s",
                era_id,
                exc,
                exc_info=True,
            )
            view_state.error = "load_failed"
            view_state.periods = []
            view_state.rows = []
            show_message(page, "No se pudieron cargar los periodos.")
        finally:
            view_state.loading = False
        render_periods_list()
        if update_list and periods_list.page and getattr(periods_list, "uid", None):
            periods_list.update()
        logger.debug("Periods loaded total=%s", len(view_state.rows))

    def build_period_card(row: PeriodRowState) -> ft.Control:
        actions: list[ft.Control] = []
        actions_alignment = (
            ft.MainAxisAlignment.CENTER
            if row.center_actions
            else ft.MainAxisAlignment.END
        )
        if row.action == "results":
            actions.append(
                ft.ElevatedButton(
                    "Ver resultados",
                    on_click=build_open_period_handler(row.period_id),
                )
            )
        elif row.action == "incursions":
            actions.append(
                ft.ElevatedButton(
                    "Ver incursiones",
                    on_click=build_open_period_handler(row.period_id),
                )
            )
        elif row.action == "assign":
            actions.append(
                ft.OutlinedButton(
                    "Asignar adversarios",
                    on_click=build_open_assignment_handler(row.period_id),
                )
            )
        elif row.action == "reveal":
            actions.append(
                ft.ElevatedButton(
                    "Revelar periodo",
                    on_click=build_reveal_period_handler(row.period_id),
                    height=48,
                    width=240,
                )
            )

        incursions_section = (
            incursions_preview([ft.Text(entry) for entry in row.incursions_preview])
            if row.incursions_preview
            else ft.Container()
        )
        return period_card(
            row.title,
            actions,
            incursions_section,
            actions_alignment=actions_alignment,
        )

    def build_assignment_dialog_content(dialog_state: AssignmentDialogState) -> ft.Control:
        options = [
            ft.dropdown.Option(item.adversary_id, item.name)
            for item in sorted(
                get_adversary_catalog().values(), key=lambda item: item.name
            )
        ]

        def build_incursion_card(incursion: dict) -> ft.Card:
            incursion_id = incursion["id"]
            selector = ft.Dropdown(
                label="Adversario",
                options=options,
                value=dialog_state.selections.get(incursion_id),
            )

            def handle_select(event: ft.ControlEvent) -> None:
                dialog_state.selections[incursion_id] = event.control.value

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
        for incursion in dialog_state.incursions:
            list_view.controls.append(build_incursion_card(incursion))
        return list_view

    def render_assignment_dialog() -> None:
        dialog_state = view_state.dialog
        if not dialog_state or not dialog_state.is_open:
            return

        def handle_save() -> None:
            logger.info(
                "Saving adversary assignments period_id=%s", dialog_state.period_id
            )
            missing_items: list[str] = []
            for incursion in dialog_state.incursions:
                incursion_id = incursion["id"]
                adversary_id = dialog_state.selections.get(incursion_id)
                if adversary_id:
                    continue
                missing_items.extend(
                    [
                        get_spirit_name(incursion.get("spirit_1_id")),
                        get_spirit_name(incursion.get("spirit_2_id")),
                    ]
                )
            if missing_items:
                show_message(
                    page,
                    "Faltan adversarios para: "
                    f"{', '.join(missing_items)}.",
                )
                return
            success = assign_period_adversaries(
                page,
                service,
                era_id,
                dialog_state.period_id,
                dialog_state.selections,
            )
            if not success:
                return
            dialog_state.is_open = False
            close_dialog(page)
            load_periods(update_list=True)
            show_message(page, "Asignaciones guardadas")

        def handle_cancel() -> None:
            logger.info(
                "Assignment dialog cancelled period_id=%s", dialog_state.period_id
            )
            dialog_state.is_open = False
            close_dialog(page)

        assignment_dialog.title = ft.Text("Asignar adversarios")
        assignment_dialog.content = build_assignment_dialog_content(dialog_state)
        assignment_dialog.actions = [
            ft.TextButton(
                "Cancelar",
                on_click=lambda _: safe_event_handler(
                    page,
                    handle_cancel,
                    context={
                        "screen": "periods",
                        "action": "cancel_assignment",
                        "era_id": era_id,
                        "period_id": dialog_state.period_id,
                    },
                ),
            ),
            ft.ElevatedButton(
                "Guardar",
                on_click=lambda _: safe_event_handler(
                    page,
                    handle_save,
                    context={
                        "screen": "periods",
                        "action": "save_assignment",
                        "era_id": era_id,
                        "period_id": dialog_state.period_id,
                    },
                ),
            ),
        ]
        show_dialog(page, assignment_dialog)
        logger.debug(
            "Assignment dialog shown period_id=%s", dialog_state.period_id
        )

    def open_assignment_dialog(period_id: str) -> None:
        logger.info("Open assignment dialog clicked period_id=%s", period_id)
        incursions = service.list_incursions(era_id, period_id)
        view_state.dialog = AssignmentDialogState(
            period_id=period_id,
            incursions=incursions,
            selections={
                incursion["id"]: incursion.get("adversary_id")
                for incursion in incursions
            },
            is_open=True,
        )
        render_assignment_dialog()

    def build_open_assignment_handler(period_id: str):
        def handler(event: ft.ControlEvent) -> None:
            def run() -> None:
                show_message(
                    page,
                    "Debug: intentando abrir el diálogo de asignación.",
                )
                open_assignment_dialog(period_id)

            safe_event_handler(
                page,
                run,
                context={
                    "screen": "periods",
                    "action": "open_assignment_dialog",
                    "era_id": era_id,
                    "period_id": period_id,
                },
            )

        return handler

    def build_reveal_period_handler(period_id: str):
        def handler(event: ft.ControlEvent) -> None:
            safe_event_handler(
                page,
                lambda: _reveal_period(period_id),
                context={
                    "screen": "periods",
                    "action": "reveal_period",
                    "era_id": era_id,
                    "period_id": period_id,
                },
            )

        return handler

    def _reveal_period(period_id: str) -> None:
        logger.info("Reveal period clicked period_id=%s", period_id)
        if reveal_period(page, service, era_id, period_id):
            load_periods(update_list=True)

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
