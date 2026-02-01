from __future__ import annotations

import asyncio

import flet as ft

from app.utils.logger import get_logger
from app.utils.router import normalize_route

logger = get_logger(__name__)


async def navigate(page: ft.Page, route: str) -> None:
    resolved_page = ft.context.page
    normalized_route = normalize_route(route)
    logger.debug(
        "Navigate push_route route=%s current_route=%s",
        normalized_route,
        resolved_page.route,
    )
    asyncio.create_task(resolved_page.push_route(normalized_route))


async def go(page: ft.Page, route: str) -> None:
    await navigate(page, route)


def go_to(page: ft.Page, route: str):
    async def handler(event: ft.ControlEvent) -> None:
        logger.debug(
            "UI navigation event route=%s control=%s", route, event.control
        )
        await navigate(page, route)

    return handler
