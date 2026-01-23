from __future__ import annotations

import flet as ft


async def go(page: ft.Page, route: str) -> None:
    await page.push_route(route)


def go_to(page: ft.Page, route: str):
    async def handler(event: ft.ControlEvent) -> None:
        await go(page, route)

    return handler
