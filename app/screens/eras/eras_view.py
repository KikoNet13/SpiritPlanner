from __future__ import annotations

import asyncio
import re

import flet as ft

from app.screens.eras.eras_model import EraCardModel
from app.screens.eras.eras_viewmodel import ErasViewModel
from app.screens.shared_components import section_card, status_chip
from app.services.service_registry import get_firestore_service
from app.utils.logger import get_logger
from app.utils.navigation import navigate
from app.utils.router import register_route_loader

logger = get_logger(__name__)


def _extract_index(value: str) -> str | None:
    match = re.search(r"(\d+)$", value)
    return match.group(1) if match else None


def _active_incursion_line(model: EraCardModel) -> str:
    if not model.active_incursion:
        return "Sin incursión activa"
    active = model.active_incursion
    period_index = _extract_index(str(active.period_id))
    incursion_index = _extract_index(str(active.incursion_id))
    if period_index and incursion_index:
        return (
            f"Incursión activa: Período {period_index} · "
            f"Incursión {incursion_index}"
        )
    return "Incursión activa"


def _era_card(
    model: EraCardModel,
    action_row: ft.Control,
) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.STARS),
                                ft.Text(
                                    f"Era {model.index}",
                                    weight=ft.FontWeight.BOLD,
                                ),
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
                        ft.Text(_active_incursion_line(model)),
                    ],
                    spacing=4,
                ),
                action_row,
            ],
            spacing=8,
        )
    )


@ft.component
def eras_view() -> ft.Control:
    logger.debug("Rendering eras_view")
    page = ft.context.page
    service = get_firestore_service(page.session)
    view_model, _ = ft.use_state(ErasViewModel())

    def load() -> None:
        view_model.ensure_loaded(service)

    ft.use_effect(load, [])

    def register_loader() -> None:
        register_route_loader(page, "/eras", lambda _: view_model.load_eras(service))

    ft.use_effect(register_loader, [])

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
    elif not view_model.eras:
        content_controls.append(ft.Text("No hay Eras disponibles."))
    else:
        for era in view_model.eras:
            def handle_open_periods(
                event: ft.ControlEvent,
                era_id: str = era.era_id,
            ) -> None:
                logger.info(
                    "UI click open periods era_id=%s control=%s",
                    era_id,
                    event.control,
                )
                try:
                    view_model.request_open_periods(era_id)
                except Exception as exc:
                    logger.exception(
                        "Failed to handle open periods era_id=%s error=%s",
                        era_id,
                        exc,
                    )

            secondary_action = ft.OutlinedButton(
                "Ver períodos",
                on_click=handle_open_periods,
            )
            primary_action = None
            if era.active_incursion:
                def handle_open_active_incursion(
                    event: ft.ControlEvent,
                    active_incursion=era.active_incursion,
                ) -> None:
                    logger.info(
                        "UI click open active incursion era_id=%s period_id=%s incursion_id=%s control=%s",
                        active_incursion.era_id,
                        active_incursion.period_id,
                        active_incursion.incursion_id,
                        event.control,
                    )
                    try:
                        view_model.request_open_active_incursion(active_incursion)
                    except Exception as exc:
                        logger.exception(
                            "Failed to handle open active incursion era_id=%s period_id=%s incursion_id=%s error=%s",
                            active_incursion.era_id,
                            active_incursion.period_id,
                            active_incursion.incursion_id,
                            exc,
                        )

                primary_action = ft.Button(
                    "Continuar",
                    on_click=handle_open_active_incursion,
                )
            if primary_action:
                action_row = ft.Row(
                    [secondary_action, primary_action],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            else:
                action_row = ft.Row(
                    [secondary_action],
                    alignment=ft.MainAxisAlignment.START,
                )
            content_controls.append(_era_card(era, action_row))

    eras_list = ft.ListView(spacing=8, expand=True, controls=content_controls)
    max_content_width = min(
        960.0,
        max(320.0, float(page.width or 960.0) - 32.0),
    )

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Eras"), center_title=False),
            ft.Container(
                content=ft.Container(
                    content=ft.Column(
                        [
                            eras_list,
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
