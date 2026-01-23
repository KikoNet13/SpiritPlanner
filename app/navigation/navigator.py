from __future__ import annotations

import flet as ft


class Navigator:
    def __init__(self, page: ft.Page):
        self.page = page

    async def go(self, route: str) -> None:
        await self.page.push_route(route)
