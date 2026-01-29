from __future__ import annotations

import flet as ft

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def navigate(page: ft.Page, route: str) -> None:
    logger.debug("Navigating to route=%s", route)
    await page.push_route(route)
    logger.debug("Navigation complete route=%s", route)


async def go(page: ft.Page, route: str) -> None:
    await navigate(page, route)


def go_to(page: ft.Page, route: str):
    async def handler(event: ft.ControlEvent) -> None:
        logger.info(
            "UI navigation event route=%s control=%s", route, event.control
        )
        await navigate(page, route)

    return handler
