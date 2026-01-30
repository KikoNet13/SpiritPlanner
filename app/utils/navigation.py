from __future__ import annotations

import flet as ft

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def navigate(page: ft.Page, route: str) -> None:
    logger.debug(
        "Navigate go route=%s current_route=%s",
        route,
        page.route,
    )
    page.go(route)


async def go(page: ft.Page, route: str) -> None:
    await navigate(page, route)


def go_to(page: ft.Page, route: str):
    async def handler(event: ft.ControlEvent) -> None:
        logger.debug(
            "UI navigation event route=%s control=%s", route, event.control
        )
        await navigate(page, route)

    return handler
