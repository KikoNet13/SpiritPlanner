from __future__ import annotations

import asyncio

import flet as ft

from app.utils.logger import get_logger
from app.utils.router import get_router

logger = get_logger(__name__)


def _resolve_page(page: ft.Page | None) -> ft.Page:
    return page or ft.context.page


async def navigate(page: ft.Page, route: str) -> None:
    resolved_page = _resolve_page(page)
    router = get_router(resolved_page)
    logger.debug(
        "Navigate push_route route=%s current_route=%s",
        route,
        router.route,
    )
    asyncio.create_task(resolved_page.push_route(route))


async def go(page: ft.Page, route: str) -> None:
    await navigate(page, route)


def go_to(page: ft.Page, route: str):
    async def handler(event: ft.ControlEvent) -> None:
        logger.debug(
            "UI navigation event route=%s control=%s", route, event.control
        )
        event_page = getattr(event, "page", None)
        await navigate(event_page or page, route)

    return handler
