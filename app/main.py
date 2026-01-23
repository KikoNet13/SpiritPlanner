from __future__ import annotations

import flet as ft

from app.screens.eras_screen import eras_view
from app.screens.incursion_detail_screen import incursion_detail_view
from app.screens.incursions_screen import incursions_view
from app.screens.periods_screen import periods_view
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go

logger = get_logger(__name__)


async def main(page: ft.Page) -> None:
    logger.debug("Entering main(page=%s)", page)
    page.title = "SpiritPlanner"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    logger.debug("Initializing FirestoreService")
    service = FirestoreService()

    def add_view(route: str, content: ft.Control) -> None:
        logger.debug("Adding view route=%s content=%s", route, type(content).__name__)
        page.views.append(ft.View(route=route, controls=[content]))

    async def handle_route_change(event: ft.RouteChangeEvent) -> None:
        logger.info("Route change event route=%s", event.route)
        page.views.clear()
        parts = [part for part in event.route.split("/") if part]

        add_view("/eras", eras_view(page, service))

        if len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            logger.debug("Building periods view era_id=%s", era_id)
            add_view(f"/eras/{era_id}", periods_view(page, service, era_id))

            if len(parts) >= 4 and parts[2] == "periods":
                period_id = parts[3]
                logger.debug(
                    "Building incursions view era_id=%s period_id=%s",
                    era_id,
                    period_id,
                )
                add_view(
                    f"/eras/{era_id}/periods/{period_id}",
                    incursions_view(page, service, era_id, period_id),
                )

                if len(parts) >= 6 and parts[4] == "incursions":
                    incursion_id = parts[5]
                    logger.debug(
                        "Building incursion detail view era_id=%s period_id=%s incursion_id=%s",
                        era_id,
                        period_id,
                        incursion_id,
                    )
                    add_view(
                        f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
                        incursion_detail_view(
                            page, service, era_id, period_id, incursion_id
                        ),
                    )

        page.update()
        logger.debug("Route change handled. views_count=%s", len(page.views))

    async def handle_view_pop(event: ft.ViewPopEvent) -> None:
        logger.info("View pop event")
        if page.views:
            page.views.pop()
        if not page.views:
            logger.debug("No views left, navigating to /eras")
            await go(page, "/eras")
            return
        top_view = page.views[-1]
        logger.debug("Popped view, navigating to %s", top_view.route)
        await go(page, top_view.route)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    logger.info("Initial navigation to /eras")
    await go(page, "/eras")
    logger.debug("Exiting main")


if __name__ == "__main__":
    logger.info("Starting SpiritPlanner application")
    ft.run(main)
