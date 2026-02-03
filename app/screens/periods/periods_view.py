from __future__ import annotations

import asyncio
import re
from pathlib import Path

import flet as ft

from app.screens.data_lookup import get_adversary_catalog
from app.screens.periods.periods_model import AssignmentIncursionModel, PeriodRowModel
from app.screens.periods.periods_viewmodel import PeriodsViewModel
from app.screens.shared_components import section_card, status_chip
from app.services.service_registry import get_firestore_service
from app.utils.logger import get_logger
from app.utils.navigation import navigate
from app.utils.router import register_route_loader

logger = get_logger(__name__)
ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
LAYOUTS_DIR = ASSETS_DIR / "layouts"


def _period_card(
    row: PeriodRowModel,
    action: ft.Control | None,
    preview_lines: list[ft.Control],
) -> ft.Container:
    body_controls: list[ft.Control] = []
    if preview_lines:
        body_controls.extend(preview_lines)
    action_row = None
    if action:
        action_row = ft.Row(
            [action],
            alignment=ft.MainAxisAlignment.END,
            expand=True,
        )
    return section_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.CALENDAR_TODAY),
                                ft.Text(row.title, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=8,
                        ),
                        status_chip(row.status_label, row.status_color),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(body_controls, spacing=4),
                ft.Container(expand=True),
                action_row or ft.Container(),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )


def _incursions_preview(entries: list[str]) -> list[ft.Control]:
    return [
        ft.Text(
            entry,
            size=12,
            color=ft.Colors.BLUE_GREY_600,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        for entry in entries[:4]
    ]


def _extract_index(value: str) -> str | None:
    match = re.search(r"(\d+)$", value)
    return match.group(1) if match else None


def _assignment_card(
    incursion: AssignmentIncursionModel,
    selection: str | None,
    options: list[ft.dropdown.Option],
    show_error: bool,
    on_select,
) -> ft.Card:
    layout_image_path = LAYOUTS_DIR / f"{incursion.layout_id}.png"
    preview_size = ft.Size(96, 72)
    if incursion.layout_id and layout_image_path.exists():
        layout_preview: ft.Control = ft.Container(
            width=preview_size.width,
            height=preview_size.height,
            alignment=ft.Alignment.CENTER,
            content=ft.Image(
                src=f"layouts/{incursion.layout_id}.png",
                fit=ft.BoxFit.CONTAIN,
                width=preview_size.width,
                height=preview_size.height,
            ),
        )
    else:
        layout_preview = ft.Container(
            width=preview_size.width,
            height=preview_size.height,
            border=ft.Border.all(1, ft.Colors.BLUE_GREY_200),
            border_radius=10,
            alignment=ft.Alignment.CENTER,
            padding=6,
            content=ft.Text(
                incursion.layout_name,
                size=10,
                color=ft.Colors.BLUE_GREY_600,
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        )
    dropdown = ft.Dropdown(
        options=options,
        value=selection,
        error_text="Selecciona un adversario" if show_error else None,
        on_select=on_select,
        height=40,
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
        spacing=1,
    )
    layout_info = ft.Column(
        [
            ft.Text(
                f"Boards {incursion.board_1_name} + {incursion.board_2_name}",
                size=11,
                color=ft.Colors.BLUE_GREY_600,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Text(
                f"Layout {incursion.layout_name}",
                size=11,
                color=ft.Colors.BLUE_GREY_600,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ],
        spacing=1,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    right_column = ft.Column(
        [
            layout_preview,
            layout_info,
        ],
        spacing=4,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"Incursión {incursion.index}",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.BLUE_GREY_700,
                    ),
                    ft.ResponsiveRow(
                        [
                            ft.Column(
                                [
                                    spirits_column,
                                    dropdown,
                                ],
                                col={"xs": 12, "md": 8},
                                spacing=6,
                            ),
                            ft.Column(
                                [right_column],
                                col={"xs": 12, "md": 4},
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=10,
                        run_spacing=6,
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
    dialog_ref: ft.Ref[ft.AlertDialog | None] = ft.use_ref(None)

    def load() -> None:
        view_model.ensure_loaded(service, era_id)

    ft.use_effect(load, [era_id])

    def register_loader() -> None:
        def loader(params: dict[str, str]) -> None:
            resolved_era_id = params.get("era_id", era_id)
            view_model.ensure_loaded(service, resolved_era_id)

        register_route_loader(page, "/eras/{era_id}", loader)

    ft.use_effect(register_loader, [era_id])

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

    def close_assignment_dialog_ui(_: ft.ControlEvent | None = None) -> None:
        view_model.close_assignment_dialog()
        dialog = dialog_ref.current
        if dialog and dialog.open:
            page.pop_dialog()

    def handle_assignment_dialog_dismiss(_: ft.ControlEvent) -> None:
        view_model.close_assignment_dialog()

    def handle_save_assignment(_: ft.ControlEvent | None = None) -> None:
        view_model.save_assignment(service)
        dialog = dialog_ref.current
        if not dialog:
            return
        if view_model.assignment_open:
            configure_assignment_dialog(dialog)
            dialog.update()
            return
        if dialog.open:
            page.pop_dialog()

    def ensure_assignment_dialog() -> ft.AlertDialog:
        dialog = dialog_ref.current
        if dialog is None:
            dialog = ft.AlertDialog(
                modal=True,
                inset_padding=ft.padding.symmetric(horizontal=12, vertical=16),
                on_dismiss=handle_assignment_dialog_dismiss,
            )
            dialog_ref.current = dialog
        return dialog

    def configure_assignment_dialog(dialog: ft.AlertDialog) -> None:
        page_width = float(
            view_model.assignment_viewport_width
            or page.width
            or getattr(getattr(page, "window", None), "width", 0)
            or 900.0
        )
        page_height = float(
            view_model.assignment_viewport_height
            or page.height
            or getattr(getattr(page, "window", None), "height", 0)
            or 700.0
        )
        dialog_width = min(960.0, max(320.0, page_width - 48.0))
        dialog_height = max(360.0, page_height * 0.9)
        list_view = ft.ListView(spacing=10, expand=True)
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
        dialog.title = ft.Text("Asignar adversarios")
        dialog.content = ft.Container(
            content=list_view,
            width=dialog_width,
            height=dialog_height,
        )
        dialog.actions = [
            ft.TextButton(
                "Cancelar",
                on_click=close_assignment_dialog_ui,
            ),
            ft.Button(
                "Guardar",
                on_click=handle_save_assignment,
            ),
        ]

    def refresh_assignment_dialog() -> None:
        dialog = dialog_ref.current
        if dialog is None or not view_model.assignment_open or not dialog.open:
            return
        configure_assignment_dialog(dialog)
        dialog.update()

    ft.use_effect(refresh_assignment_dialog, [view_model.assignment_version])

    def register_resize_handler():
        def update_viewport(
            width: float | None,
            height: float | None,
        ) -> None:
            resolved_width = float(
                width
                or page.width
                or getattr(getattr(page, "window", None), "width", 0)
                or 900.0
            )
            resolved_height = float(
                height
                or page.height
                or getattr(getattr(page, "window", None), "height", 0)
                or 700.0
            )
            view_model.set_assignment_viewport(resolved_width, resolved_height)

        def on_resize(event: ft.ControlEvent) -> None:
            update_viewport(
                getattr(event, "width", None),
                getattr(event, "height", None),
            )

        page.on_resize = on_resize
        update_viewport(page.width, page.height)

        def cleanup() -> None:
            if page.on_resize == on_resize:
                page.on_resize = None

        return cleanup

    ft.use_effect(register_resize_handler, [])

    def build_period_card(row: PeriodRowModel) -> ft.Control:
        action = None
        if row.action in {"results", "incursions"}:
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

            action = ft.Button(
                "Ver incursiones",
                on_click=handle_open_incursions,
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
                    if not view_model.assignment_open:
                        return
                    dialog = ensure_assignment_dialog()
                    configure_assignment_dialog(dialog)
                    if dialog.open:
                        return
                    page.show_dialog(dialog)
                except RuntimeError as exc:
                    if "already opened" in str(exc).lower():
                        logger.warning("Assignment dialog already open; skipping reopen")
                        return
                    raise
                except Exception as exc:
                    logger.exception(
                        "Failed to handle assign adversaries era_id=%s period_id=%s error=%s",
                        era_id,
                        period_id,
                        exc,
                    )

            action = ft.Button(
                "Asignar adversarios",
                on_click=handle_assign_adversaries,
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

            action = ft.Button(
                "Revelar",
                on_click=handle_reveal_period,
            )
        elif row.status_label == "Pendiente":
            def handle_reveal_pending_period(
                event: ft.ControlEvent,
                period_id: str = row.period_id,
            ) -> None:
                logger.info(
                    "UI click reveal pending period era_id=%s period_id=%s control=%s",
                    era_id,
                    period_id,
                    event.control,
                )
                try:
                    view_model.reveal_period(service, period_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle reveal pending period era_id=%s period_id=%s error=%s",
                        era_id,
                        period_id,
                        exc,
                    )

            action = ft.Button(
                "Revelar",
                on_click=handle_reveal_pending_period,
            )

        preview_lines = (
            _incursions_preview(list(row.incursions_preview))
            if row.incursions_preview
            else []
        )
        return _period_card(row, action, preview_lines)

    content_controls: list[ft.Control] = []
    if view_model.loading:
        content_controls.append(ft.ProgressRing())
    elif not view_model.rows:
        content_controls.append(ft.Text("No hay períodos disponibles."))
    else:
        content_controls.extend(build_period_card(row) for row in view_model.rows)

    periods_list = ft.ListView(spacing=8, expand=True, controls=content_controls)
    era_label = _extract_index(era_id) or era_id
    context_header = ft.Text(
        f"Era {era_label}",
        size=16,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.BLUE_GREY_700,
    )
    max_content_width = min(
        960.0,
        max(320.0, float(page.width or 960.0) - 32.0),
    )

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Períodos"), center_title=False),
            ft.Container(
                content=ft.Container(
                    content=ft.Column(
                        [
                            context_header,
                            periods_list,
                        ],
                        expand=True,
                        spacing=8,
                    ),
                    width=max_content_width,
                    expand=True,
                ),
                padding=16,
                alignment=ft.Alignment.TOP_CENTER,
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )
