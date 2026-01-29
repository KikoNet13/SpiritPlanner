from __future__ import annotations

import os

import flet as ft

from app.screens.eras.eras_screen import eras_view
from app.screens.incursion_detail.incursion_detail_screen import (
    incursion_detail_view,
)
from app.screens.incursions.incursions_screen import incursions_view
from app.screens.periods.periods_screen import periods_view
from app.services.firestore_service import FirestoreService
from app.utils.logger import configure_logging, get_logger
from app.utils.navigation import navigate

debug_mode = os.getenv("SPIRITPLANNER_DEBUG") == "1"
configure_logging(debug=debug_mode)

logger = get_logger(__name__)


async def main(page: ft.Page) -> None:
    logger.debug("Entering main(page=%s)", page)
    page.title = "SpiritPlanner"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    logger.debug("Initializing FirestoreService")
    service = FirestoreService()

    def build_views() -> list[ft.View]:
        # Routing declarativo: render_views recompone el stack a partir de page.route.
        # Para añadir rutas, extender este builder con un nuevo ft.View.
        current_route = page.route or "/eras"
        parts = [part for part in current_route.split("/") if part]
        views: list[ft.View] = [
            ft.View(route="/eras", controls=[eras_view(page, service)])
        ]

        if len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            logger.debug("Building periods view era_id=%s", era_id)
            views.append(
                ft.View(
                    route=f"/eras/{era_id}",
                    controls=[periods_view(page, service, era_id)],
                )
            )

            if len(parts) >= 4 and parts[2] == "periods":
                period_id = parts[3]
                logger.debug(
                    "Building incursions view era_id=%s period_id=%s",
                    era_id,
                    period_id,
                )
                views.append(
                    ft.View(
                        route=f"/eras/{era_id}/periods/{period_id}",
                        controls=[
                            incursions_view(page, service, era_id, period_id)
                        ],
                    )
                )

                if len(parts) >= 6 and parts[4] == "incursions":
                    incursion_id = parts[5]
                    logger.debug(
                        "Building incursion detail view era_id=%s period_id=%s incursion_id=%s",
                        era_id,
                        period_id,
                        incursion_id,
                    )
                    views.append(
                        ft.View(
                            route=f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
                            controls=[
                                incursion_detail_view(
                                    page,
                                    service,
                                    era_id,
                                    period_id,
                                    incursion_id,
                                )
                            ],
                        )
                    )

        return views

    async def handle_route_change(event: ft.RouteChangeEvent) -> None:
        logger.info("Route change event route=%s", event.route)
        page.render_views(build_views)
        logger.debug("Route change handled. views_count=%s", len(page.views))

    async def handle_view_pop(event: ft.ViewPopEvent) -> None:
        logger.info("View pop event")
        if event.view in page.views:
            page.views.remove(event.view)
            logger.debug("View removed from stack. views_count=%s", len(page.views))
        if not page.views:
            logger.debug("No views left, navigating to /eras")
            await navigate(page, "/eras")
            return
        top_view = page.views[-1]
        logger.debug("View pop, navigating to %s", top_view.route)
        await navigate(page, top_view.route)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    logger.info("Initial navigation to /eras")
    page.render_views(build_views)
    await navigate(page, "/eras")
    logger.debug("Exiting main")


if __name__ == "__main__":
    logger.info("Starting SpiritPlanner application")
    ft.run(main)
