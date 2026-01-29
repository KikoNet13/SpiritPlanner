from __future__ import annotations

import flet as ft

from app.screens.eras.eras_model import EraCardModel
from app.screens.eras.eras_viewmodel import ErasViewModel
from app.screens.shared_components import header_text, section_card, status_chip
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

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
def eras_view(page: ft.Page, service: FirestoreService) -> ft.Control:
    logger.debug("Rendering eras_view")
    view_model = ft.use_state(lambda: ErasViewModel(page, service))[0]

    def load() -> None:
        view_model.load_eras()

    ft.use_effect(load, [])

    title = header_text("Eras")
    content_controls: list[ft.Control] = []

    if view_model.loading:
        content_controls.append(ft.ProgressRing())
    elif not view_model.eras:
        content_controls.append(ft.Text("No hay Eras disponibles."))
    else:
        for era in view_model.eras:
            actions: list[ft.Control] = [
                ft.ElevatedButton(
                    "Ver periodos",
                    on_click=view_model.open_periods_handler(era.era_id),
                )
            ]
            if era.active_incursion:
                actions.append(
                    ft.OutlinedButton(
                        "Ir a incursión activa",
                        on_click=view_model.open_active_incursion_handler(
                            era.active_incursion
                        ),
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
