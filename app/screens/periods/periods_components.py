from __future__ import annotations

import flet as ft

from app.screens.shared_components import section_card


def period_card(
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


def incursions_preview(entries: list[ft.Control]) -> ft.Container:
    return ft.Container(
        content=ft.Column(entries, spacing=4),
        padding=ft.padding.only(left=12, right=12, bottom=4),
    )
