from __future__ import annotations

import asyncio
import re

import flet as ft

from app.screens.incursions.incursions_model import IncursionCardModel
from app.screens.incursions.incursions_viewmodel import IncursionsViewModel
from app.screens.shared_components import section_card, status_chip
from app.services.service_registry import get_firestore_service
from app.utils.logger import get_logger
from app.utils.navigation import navigate
from app.utils.router import register_route_loader

logger = get_logger(__name__)


def _incursion_card(
    model: IncursionCardModel,
    on_open,
) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.EXPLORE),
                                ft.Text(model.title, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=8,
                        ),
                        status_chip(model.status_label, model.status_color),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(f"Espíritus: {model.spirit_info}"),
                        ft.Text(f"Tableros: {model.board_info}"),
                        ft.Text(f"Distribución: {model.layout_info}"),
                        ft.Text(f"Adversario: {model.adversary_info}"),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Row(
                    [
                        ft.Button("Abrir", on_click=on_open),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    expand=True,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )


def _extract_index(value: str) -> str | None:
    match = re.search(r"(\d+)$", value)
    return match.group(1) if match else None


@ft.component
def incursions_view(
    era_id: str,
    period_id: str,
) -> ft.Control:
    logger.debug("Rendering incursions_view era_id=%s period_id=%s", era_id, period_id)
    page = ft.context.page
    service = get_firestore_service(page.session)
    view_model, _ = ft.use_state(IncursionsViewModel())

    def load() -> None:
        view_model.ensure_loaded(service, era_id, period_id)

    ft.use_effect(load, [era_id, period_id])

    def register_loader() -> None:
        def loader(params: dict[str, str]) -> None:
            resolved_era_id = params.get("era_id", era_id)
            resolved_period_id = params.get("period_id", period_id)
            view_model.ensure_loaded(service, resolved_era_id, resolved_period_id)

        register_route_loader(
            page, "/eras/{era_id}/periods/{period_id}", loader
        )

    ft.use_effect(register_loader, [era_id, period_id])

    def show_toast() -> None:
        if not view_model.toast_message:
            return
        page.show_dialog(ft.SnackBar(ft.Text(view_model.toast_message)))
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

    content_controls: list[ft.Control] = []
    if view_model.loading:
        content_controls.append(ft.ProgressRing())
    elif not view_model.incursions:
        content_controls.append(ft.Text("No hay incursiones disponibles."))
    else:
        for incursion in view_model.incursions:
            def handle_open_incursion(
                event: ft.ControlEvent,
                incursion_id: str = incursion.incursion_id,
            ) -> None:
                logger.info(
                    "UI click open incursion era_id=%s period_id=%s incursion_id=%s control=%s",
                    era_id,
                    period_id,
                    incursion_id,
                    event.control,
                )
                try:
                    view_model.request_open_incursion(incursion_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle open incursion era_id=%s period_id=%s incursion_id=%s error=%s",
                        era_id,
                        period_id,
                        incursion_id,
                        exc,
                    )

            content_controls.append(
                _incursion_card(
                    incursion,
                    handle_open_incursion,
                )
            )

    incursions_list = ft.ListView(spacing=8, expand=True, controls=content_controls)
    era_label = _extract_index(era_id) or era_id
    period_label = _extract_index(period_id) or period_id
    context_header = ft.Text(
        f"Era {era_label} · Período {period_label}",
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
            ft.AppBar(title=ft.Text("Incursiones"), center_title=False),
            ft.Container(
                content=ft.Container(
                    content=ft.Column(
                        [
                            context_header,
                            incursions_list,
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
