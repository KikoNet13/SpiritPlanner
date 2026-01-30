from __future__ import annotations

import os

import flet as ft

DEBUG_HUD = os.getenv("SPIRITPLANNER_DEBUG") == "1"


def debug_hud(page: ft.Page, screen_name: str) -> ft.Control:
    if not DEBUG_HUD:
        return ft.Container()
    top_route = page.views[-1].route if page.views else "-"
    content = (
        f"Ruta: {page.route} | Top: {top_route} | Vistas: {len(page.views)} "
        f"| Pantalla: {screen_name}"
    )
    return ft.Container(
        content=ft.Text(content, size=11, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_700,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )
