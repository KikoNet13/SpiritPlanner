from __future__ import annotations

import os

import flet as ft

from app.utils.router import build_route_stack

DEBUG_HUD = os.getenv("SPIRITPLANNER_DEBUG") == "1"


def debug_hud(page: ft.Page, screen_name: str) -> ft.Control:
    if not DEBUG_HUD:
        return ft.Container()
    route_stack = build_route_stack(page.route)
    top_route = route_stack[-1] if route_stack else "-"
    content = (
        f"Ruta: {page.route or '-'} | Top: {top_route} | Vistas: {len(route_stack)} "
        f"| Pantalla: {screen_name}"
    )
    return ft.Container(
        content=ft.Text(content, size=11, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_700,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )
