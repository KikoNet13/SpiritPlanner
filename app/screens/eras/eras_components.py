from __future__ import annotations

import flet as ft

from app.screens.shared_components import section_card, status_chip


def era_card(
    era_label: str,
    status_label: str,
    status_color: str,
    incursion_label: str,
    incursion_color: str,
    actions: list[ft.Control],
) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.STARS),
                    title=ft.Text(era_label, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Column(
                        [
                            ft.Row(
                                [
                                    status_chip(status_label, status_color),
                                    status_chip(incursion_label, incursion_color),
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
