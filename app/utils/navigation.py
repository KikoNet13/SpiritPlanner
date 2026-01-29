from __future__ import annotations

import flet as ft

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def navigate(page: ft.Page, route: str) -> None:
    overlay = list(getattr(page, "overlay", []) or [])
    overlay_types = [type(item).__name__ for item in overlay]
    view_routes = [view.route for view in page.views] if page.views else []
    logger.info(
        "Navigate start route=%s current_route=%s views=%s overlay_count=%s overlay_types=%s",
        route,
        page.route,
        view_routes,
        len(overlay),
        overlay_types,
    )
    await page.push_route(route)
    overlay_after = list(getattr(page, "overlay", []) or [])
    overlay_types_after = [type(item).__name__ for item in overlay_after]
    view_routes_after = [view.route for view in page.views] if page.views else []
    logger.info(
        "Navigate complete route=%s current_route=%s views=%s overlay_count=%s overlay_types=%s",
        route,
        page.route,
        view_routes_after,
        len(overlay_after),
        overlay_types_after,
    )


async def go(page: ft.Page, route: str) -> None:
    await navigate(page, route)


def go_to(page: ft.Page, route: str):
    async def handler(event: ft.ControlEvent) -> None:
        logger.info(
            "UI navigation event route=%s control=%s", route, event.control
        )
        await navigate(page, route)

    return handler
