from __future__ import annotations

import os

import flet as ft

from app.screens.eras.eras_view import eras_view
from app.screens.incursion_detail.incursion_detail_view import incursion_detail_view
from app.screens.incursions.incursions_view import incursions_view
from app.screens.periods.periods_view import periods_view
from app.services.firestore_service import FirestoreService
from app.services.service_registry import set_firestore_service
from app.utils.logger import configure_logging, get_logger
from app.utils.router import build_route_stack, get_router

debug_mode = os.getenv("SPIRITPLANNER_DEBUG") == "1"
configure_logging(debug=debug_mode)

logger = get_logger(__name__)


def build_view(route: str) -> ft.View:
    parts = [part for part in route.split("/") if part]
    control: ft.Control

    if parts == ["eras"]:
        control = eras_view()
    elif len(parts) == 2 and parts[0] == "eras":
        control = periods_view(parts[1])
    elif (
        len(parts) == 4
        and parts[0] == "eras"
        and parts[2] == "periods"
    ):
        control = incursions_view(parts[1], parts[3])
    elif (
        len(parts) == 5
        and parts[0] == "eras"
        and parts[2] == "periods"
        and parts[4] == "incursions"
    ):
        control = incursions_view(parts[1], parts[3])
    elif (
        len(parts) == 6
        and parts[0] == "eras"
        and parts[2] == "periods"
        and parts[4] == "incursions"
    ):
        control = incursion_detail_view(parts[1], parts[3], parts[5])
    else:
        control = eras_view()
        route = "/eras"

    return ft.View(route=route, controls=[control])


@ft.component
def App() -> list[ft.View]:
    router, _ = ft.use_state(get_router(ft.context.page))
    page = ft.context.page
    page.on_route_change = router.on_route_change
    page.on_view_pop = router.on_view_pop

    stack = build_route_stack(router.route)
    return [build_view(route) for route in stack]


async def main(page: ft.Page) -> None:
    logger.debug("Entering main(page=%s)", page)
    page.title = "SpiritPlanner"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    logger.debug("Initializing FirestoreService")
    service = FirestoreService()
    set_firestore_service(page.session, service)

    page.render_views(App)
    logger.debug("Exiting main")


if __name__ == "__main__":
    logger.info("Starting SpiritPlanner application")
    ft.run(main)
