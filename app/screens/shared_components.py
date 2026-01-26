from __future__ import annotations

import flet as ft


def header_text(text: str) -> ft.Text:
    return ft.Text(text, size=22, weight=ft.FontWeight.BOLD)


def status_chip(label: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(label, size=12, color=ft.Colors.WHITE),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )


def section_card(
    content: ft.Control,
    padding: int = 12,
    border_radius: int = 12,
    bgcolor: str | None = None,
    border_color: str = ft.Colors.GREY_300,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        border=ft.border.all(1, border_color),
        border_radius=border_radius,
        bgcolor=bgcolor,
    )


def action_button(
    label: str,
    on_click,
    variant: str = "elevated",
    icon: str | None = None,
    disabled: bool = False,
) -> ft.Control:
    if variant == "outlined":
        return ft.OutlinedButton(label, icon=icon, on_click=on_click, disabled=disabled)
    return ft.ElevatedButton(label, icon=icon, on_click=on_click, disabled=disabled)
