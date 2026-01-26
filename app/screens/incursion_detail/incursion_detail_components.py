from __future__ import annotations

import flet as ft


def dark_section(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        padding=20,
        border_radius=20,
        bgcolor=ft.Colors.BLUE_GREY_900,
    )


def light_section(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        padding=16,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.WHITE,
    )


def summary_tile(icon: str, label: str, on_click) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon),
                ft.Text(label),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=12,
        border_radius=12,
        bgcolor=ft.Colors.BLUE_GREY_50,
        on_click=on_click,
    )
