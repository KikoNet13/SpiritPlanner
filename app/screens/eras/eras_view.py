from __future__ import annotations

import asyncio

import flet as ft

from app.screens.eras.eras_model import EraCardModel
from app.screens.eras.eras_viewmodel import ErasViewModel
from app.screens.shared_components import header_text, section_card, status_chip
from app.services.service_registry import get_firestore_service
from app.utils.logger import get_logger
from app.utils.navigation import navigate
from app.utils.router import register_route_loader

logger = get_logger(__name__)


def _era_card(model: EraCardModel, actions: list[ft.Control]) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.STARS),
                    title=ft.Text(f"Era {model.index}", weight=ft.FontWeight.BOLD),
                    subtitle=ft.Column(
                        [
                            ft.Row(
                                [
                                    status_chip(model.status_label, model.status_color),
                                    status_chip(
                                        model.incursion_label, model.incursion_color
                                    ),
                                ],
                                spacing=8,
                            )
                        ],
                        spacing=4,
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

    title = header_text("Eras")
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

            actions: list[ft.Control] = [
                ft.Button(
                    "Ver periodos",
                    on_click=handle_open_periods,
                )
            ]
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

                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=handle_open_active_incursion,
                    )
                )
            content_controls.append(_era_card(era, actions))

    eras_list = ft.ListView(spacing=12, expand=True, controls=content_controls)

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Eras"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        eras_list,
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
