from __future__ import annotations

import asyncio

import flet as ft

from app.screens.data_lookup import get_adversary_catalog
from app.screens.periods.periods_model import AssignmentIncursionModel, PeriodRowModel
from app.screens.periods.periods_viewmodel import PeriodsViewModel
from app.screens.shared_components import header_text, section_card
from app.services.service_registry import get_firestore_service
from app.utils.logger import get_logger
from app.utils.navigation import navigate

logger = get_logger(__name__)


def _period_card(
    title: str,
    actions: list[ft.Control],
    incursions_section: ft.Control,
    actions_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.END,
) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CALENDAR_TODAY),
                    title=ft.Text(title, weight=ft.FontWeight.BOLD),
                ),
                ft.Row(
                    actions,
                    wrap=True,
                    spacing=8,
                    alignment=actions_alignment,
                ),
                incursions_section,
            ],
            spacing=4,
        )
    )


def _incursions_preview(entries: list[ft.Control]) -> ft.Container:
    return ft.Container(
        content=ft.Column(entries, spacing=4),
        padding=ft.padding.only(left=12, right=12, bottom=4),
    )


def _assignment_card(
    incursion: AssignmentIncursionModel,
    selection: str | None,
    options: list[ft.dropdown.Option],
    show_error: bool,
    on_select,
) -> ft.Card:
    dropdown = ft.Dropdown(
        options=options,
        value=selection,
        error_text="Selecciona un adversario" if show_error else None,
        on_select=on_select,
    )
    spirits_column = ft.Column(
        [
            ft.Text(
                incursion.spirit_1_name,
                size=14,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                incursion.spirit_2_name,
                size=14,
                weight=ft.FontWeight.BOLD,
            ),
        ],
        spacing=2,
    )
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"Incursión {incursion.index}",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_700,
                    ),
                    ft.ResponsiveRow(
                        [
                            ft.Column(
                                [spirits_column],
                                col={"xs": 12, "md": 8},
                            ),
                            ft.Column(
                                [dropdown],
                                col={"xs": 12, "md": 4},
                            ),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=6,
            ),
            padding=12,
        )
    )


@ft.component
def periods_view(
    era_id: str,
) -> ft.Control:
    logger.debug("Rendering periods_view era_id=%s", era_id)
    page = ft.context.page
    service = get_firestore_service(page.session)
    view_model, _ = ft.use_state(PeriodsViewModel())
    dialog_ref = ft.use_ref(None)

    def load() -> None:
        view_model.ensure_loaded(service, era_id)

    ft.use_effect(load, [era_id])

    def show_toast() -> None:
        if not view_model.toast_message:
            return
        snack = ft.SnackBar(ft.Text(view_model.toast_message))
        page.show_dialog(snack)
        view_model.consume_toast()

    ft.use_effect(show_toast, [view_model.toast_version])

    def handle_navigation() -> None:
        if not view_model.navigate_to:
            return
        target = view_model.navigate_to

        async def do_navigation() -> None:
            try:
                await navigate(page, target)
            except Exception as exc:
                logger.exception(
                    "Navigation failed target=%s error=%s", target, exc
                )

        logger.info("Scheduling navigation target=%s", target)
        if hasattr(page, "run_task"):
            page.run_task(do_navigation)
        else:
            asyncio.create_task(do_navigation())
        view_model.consume_navigation()

    ft.use_effect(handle_navigation, [view_model.nav_version])

    options = [
        ft.dropdown.Option(item.adversary_id, item.name)
        for item in sorted(get_adversary_catalog().values(), key=lambda item: item.name)
    ]

    def build_assignment_dialog() -> ft.AlertDialog:
        dialog_width = 720
        if page.width:
            dialog_width = min(page.width * 0.9, 720)
        list_view = ft.ListView(spacing=12, expand=True)
        for incursion in view_model.assignment_incursions:
            incursion_id = incursion.incursion_id
            list_view.controls.append(
                _assignment_card(
                    incursion,
                    view_model.assignment_selections.get(incursion_id),
                    options,
                    view_model.assignment_errors.get(incursion_id, False),
                    lambda event, iid=incursion_id: view_model.set_assignment_selection(
                        iid, event.control.value
                    ),
                )
            )
        dialog = dialog_ref.current or ft.AlertDialog(modal=True)
        dialog.title = ft.Text("Asignar adversarios")
        dialog.content = ft.Container(
            content=list_view,
            width=dialog_width,
            height=420,
        )
        dialog.actions = [
            ft.TextButton(
                "Cancelar",
                on_click=lambda _: view_model.close_assignment_dialog(),
            ),
            ft.ElevatedButton(
                "Guardar",
                on_click=lambda _: view_model.save_assignment(service),
            ),
        ]
        return dialog

    def sync_dialog() -> None:
        if view_model.assignment_open:
            dialog = build_assignment_dialog()
            if dialog_ref.current is None:
                dialog_ref.current = dialog
                page.show_dialog(dialog)
            else:
                dialog.update()
        else:
            if dialog_ref.current:
                page.pop_dialog()
                dialog_ref.current = None

    ft.use_effect(sync_dialog, [view_model.assignment_open, view_model.assignment_version])

    def build_period_card(row: PeriodRowModel) -> ft.Control:
        actions: list[ft.Control] = []
        actions_alignment = (
            ft.MainAxisAlignment.CENTER
            if row.center_actions
            else ft.MainAxisAlignment.END
        )
        if row.action == "results":
            def handle_open_results(
                event: ft.ControlEvent,
                period_id: str = row.period_id,
            ) -> None:
                logger.info(
                    "UI click open results era_id=%s period_id=%s control=%s",
                    era_id,
                    period_id,
                    event.control,
                )
                try:
                    view_model.request_open_period(period_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle open results era_id=%s period_id=%s error=%s",
                        era_id,
                        period_id,
                        exc,
                    )

            actions.append(
                ft.ElevatedButton(
                    "Ver resultados",
                    on_click=handle_open_results,
                )
            )
        elif row.action == "incursions":
            def handle_open_incursions(
                event: ft.ControlEvent,
                period_id: str = row.period_id,
            ) -> None:
                logger.info(
                    "UI click open incursions era_id=%s period_id=%s control=%s",
                    era_id,
                    period_id,
                    event.control,
                )
                try:
                    view_model.request_open_period(period_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle open incursions era_id=%s period_id=%s error=%s",
                        era_id,
                        period_id,
                        exc,
                    )

            actions.append(
                ft.ElevatedButton(
                    "Ver incursiones",
                    on_click=handle_open_incursions,
                )
            )
        elif row.action == "assign":
            def handle_assign_adversaries(
                event: ft.ControlEvent,
                period_id: str = row.period_id,
            ) -> None:
                logger.info(
                    "UI click assign adversaries era_id=%s period_id=%s control=%s",
                    era_id,
                    period_id,
                    event.control,
                )
                try:
                    view_model.open_assignment_dialog(service, period_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle assign adversaries era_id=%s period_id=%s error=%s",
                        era_id,
                        period_id,
                        exc,
                    )

            actions.append(
                ft.OutlinedButton(
                    "Asignar adversarios",
                    on_click=handle_assign_adversaries,
                )
            )
        elif row.action == "reveal":
            def handle_reveal_period(
                event: ft.ControlEvent,
                period_id: str = row.period_id,
            ) -> None:
                logger.info(
                    "UI click reveal period era_id=%s period_id=%s control=%s",
                    era_id,
                    period_id,
                    event.control,
                )
                try:
                    view_model.reveal_period(service, period_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle reveal period era_id=%s period_id=%s error=%s",
                        era_id,
                        period_id,
                        exc,
                    )

            actions.append(
                ft.ElevatedButton(
                    "Revelar periodo",
                    on_click=handle_reveal_period,
                    height=48,
                    width=240,
                )
            )

        incursions_section = (
            _incursions_preview([ft.Text(entry) for entry in row.incursions_preview])
            if row.incursions_preview
            else ft.Container()
        )
        return _period_card(
            row.title,
            actions,
            incursions_section,
            actions_alignment=actions_alignment,
        )

    content_controls: list[ft.Control] = []
    if view_model.loading:
        content_controls.append(ft.ProgressRing())
    elif not view_model.rows:
        content_controls.append(ft.Text("No hay periodos disponibles."))
    else:
        content_controls.extend(build_period_card(row) for row in view_model.rows)

    periods_list = ft.ListView(spacing=12, expand=True, controls=content_controls)

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Periodos"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        header_text("Era"),
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
