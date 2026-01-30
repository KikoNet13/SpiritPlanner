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
    set_firestore_service(page.session, service)

    def _overlay_snapshot() -> tuple[int, list[str]]:
        overlay = list(getattr(page, "overlay", []) or [])
        return len(overlay), [type(item).__name__ for item in overlay]

    def _view_routes() -> list[str]:
        return [view.route for view in page.views] if page.views else []

    def _close_overlays(reason: str) -> None:
        overlay_count, overlay_types = _overlay_snapshot()
        if overlay_count == 0:
            return
        logger.info(
            "Closing overlays reason=%s count=%s types=%s",
            reason,
            overlay_count,
            overlay_types,
        )
        for _ in range(overlay_count):
            try:
                page.pop_dialog()
            except Exception as exc:
                logger.warning(
                    "Failed to pop dialog reason=%s error=%s", reason, exc
                )
                break
        overlay_count_after, overlay_types_after = _overlay_snapshot()
        logger.info(
            "Overlay state after close reason=%s count=%s types=%s",
            reason,
            overlay_count_after,
            overlay_types_after,
        )

    def build_views() -> list[ft.View]:
        # Routing declarativo: render_views recompone el stack a partir de page.route.
        # Para añadir rutas, extender este builder con un nuevo ft.View.
        current_route = page.route or "/eras"
        parts = [part for part in current_route.split("/") if part]
        views: list[ft.View] = [ft.View(route="/eras", controls=[eras_view()])]

        if len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            logger.debug("Building periods view era_id=%s", era_id)
            views.append(
                ft.View(
                    route=f"/eras/{era_id}",
                    controls=[periods_view(era_id)],
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
                            incursions_view(era_id, period_id)
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
                                    era_id,
                                    period_id,
                                    incursion_id,
                                )
                            ],
                        )
                    )

        return views

    async def handle_route_change(event: ft.RouteChangeEvent) -> None:
        overlay_count, overlay_types = _overlay_snapshot()
        logger.debug(
            "Route change event route=%s current_route=%s views=%s overlay_count=%s overlay_types=%s",
            event.route,
            page.route,
            _view_routes(),
            overlay_count,
            overlay_types,
        )
        built_routes = [view.route for view in build_views()]
        page.render_views(build_views)
        overlay_count, overlay_types = _overlay_snapshot()
        top_route = page.views[-1].route if page.views else None
        logger.info(
            "Route change handled route=%s top_route=%s views=%s built_routes=%s overlay_count=%s overlay_types=%s",
            page.route,
            top_route,
            _view_routes(),
            built_routes,
            overlay_count,
            overlay_types,
        )
        if top_route and top_route != page.route:
            logger.warning(
                "Route/view mismatch route=%s top_route=%s",
                page.route,
                top_route,
            )
        if built_routes:
            built_top = built_routes[-1]
            if built_top != page.route or (top_route and built_top != top_route):
                logger.warning(
                    "Route/build mismatch route=%s top_route=%s built_top=%s",
                    page.route,
                    top_route,
                    built_top,
                )

    async def handle_view_pop(event: ft.ViewPopEvent) -> None:
        overlay_count, overlay_types = _overlay_snapshot()
        logger.info(
            "View pop event view_route=%s views=%s overlay_count=%s overlay_types=%s",
            getattr(event.view, "route", None),
            _view_routes(),
            overlay_count,
            overlay_types,
        )
        if len(page.views) > 1:
            page.views.pop()
            logger.info("View popped from stack views=%s", _view_routes())
        _close_overlays("view_pop")
        if not page.views:
            logger.debug("No views left, navigating to /eras")
            page.go("/eras")
            return
        top_view = page.views[-1]
        logger.info(
            "View pop, navigating back route=%s current_route=%s",
            top_view.route,
            page.route,
        )
        if top_view.route != page.route:
            logger.warning(
                "Route/view mismatch on back route=%s top_route=%s",
                page.route,
                top_view.route,
            )
        page.go(top_view.route)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    logger.info("Initial navigation to /eras")
    page.render_views(build_views)
    await navigate(page, "/eras")
    logger.debug("Exiting main")


if __name__ == "__main__":
    logger.info("Starting SpiritPlanner application")
    ft.run(main)
