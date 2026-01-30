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

    def _resolve_route(route: str) -> dict[str, str | None]:
        parts = [part for part in route.split("/") if part]
        era_id = None
        period_id = None
        incursion_id = None
        resolved_screen = "eras"
        if (
            len(parts) >= 6
            and parts[0] == "eras"
            and parts[2] == "periods"
            and parts[4] == "incursions"
        ):
            era_id = parts[1]
            period_id = parts[3]
            incursion_id = parts[5]
            resolved_screen = "incursion_detail"
        elif len(parts) >= 4 and parts[0] == "eras" and parts[2] == "periods":
            era_id = parts[1]
            period_id = parts[3]
            resolved_screen = "incursions"
        elif len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            resolved_screen = "periods"
        return {
            "era_id": era_id,
            "period_id": period_id,
            "incursion_id": incursion_id,
            "resolved_screen": resolved_screen,
        }

    def _build_route_stack(route: str) -> list[str]:
        info = _resolve_route(route)
        routes = ["/eras"]
        era_id = info["era_id"]
        period_id = info["period_id"]
        incursion_id = info["incursion_id"]
        if era_id:
            routes.append(f"/eras/{era_id}")
        if era_id and period_id:
            routes.append(f"/eras/{era_id}/periods/{period_id}")
        if era_id and period_id and incursion_id:
            routes.append(
                f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}"
            )
        return routes

    def _build_view(route: str, screen: str, control: ft.Control) -> ft.View:
        view = ft.View(route=route, controls=[control])
        view.data = {"screen": screen}
        if debug_mode:
            logger.debug(
                "Created view route=%s screen=%s control_root=%s",
                route,
                screen,
                type(control).__name__,
            )
        return view

    def build_views() -> list[ft.View]:
        # Routing declarativo: render_views recompone el stack a partir de page.route.
        # Para añadir rutas, extender este builder con un nuevo ft.View.
        current_route = page.route or "/eras"
        info = _resolve_route(current_route)
        era_id = info["era_id"]
        period_id = info["period_id"]
        incursion_id = info["incursion_id"]
        views: list[ft.View] = [
            _build_view("/eras", "eras", eras_view())
        ]

        if era_id:
            logger.debug("Building periods view era_id=%s", era_id)
            views.append(
                _build_view(
                    f"/eras/{era_id}",
                    "periods",
                    periods_view(era_id),
                )
            )
        if era_id and period_id:
            logger.debug(
                "Building incursions view era_id=%s period_id=%s",
                era_id,
                period_id,
            )
            views.append(
                _build_view(
                    f"/eras/{era_id}/periods/{period_id}",
                    "incursions",
                    incursions_view(era_id, period_id),
                )
            )
        if era_id and period_id and incursion_id:
            logger.debug(
                "Building incursion detail view era_id=%s period_id=%s incursion_id=%s",
                era_id,
                period_id,
                incursion_id,
            )
            views.append(
                _build_view(
                    f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
                    "incursion_detail",
                    incursion_detail_view(
                        era_id,
                        period_id,
                        incursion_id,
                    ),
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
        current_route = page.route or "/eras"
        built_routes = _build_route_stack(current_route)
        resolved_screen = _resolve_route(current_route)["resolved_screen"]
        before_routes = _view_routes()
        page.render_views(build_views)
        overlay_count, overlay_types = _overlay_snapshot()
        top_route = page.views[-1].route if page.views else None
        top_view = page.views[-1] if page.views else None
        top_screen = None
        if top_view and isinstance(getattr(top_view, "data", None), dict):
            top_screen = top_view.data.get("screen")
        logger.info(
            "Route change handled route=%s top_route=%s top_screen=%s resolved_screen=%s built_routes=%s views=%s",
            page.route,
            top_route,
            top_screen,
            resolved_screen,
            built_routes,
            _view_routes(),
        )
        after_routes = _view_routes()
        if before_routes != after_routes:
            page.update()
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
        if top_route == page.route and top_screen and top_screen != resolved_screen:
            logger.warning(
                "Route/screen mismatch route=%s resolved_screen=%s top_screen=%s",
                page.route,
                resolved_screen,
                top_screen,
            )

    async def handle_view_pop(event: ft.ViewPopEvent) -> None:
        overlay_count, overlay_types = _overlay_snapshot()
        logger.debug(
            "View pop event view_route=%s views=%s overlay_count=%s overlay_types=%s",
            getattr(event.view, "route", None),
            _view_routes(),
            overlay_count,
            overlay_types,
        )
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    logger.info("Initial navigation to /eras")
    await navigate(page, "/eras")
    logger.debug("Exiting main")


if __name__ == "__main__":
    logger.info("Starting SpiritPlanner application")
    ft.run(main)
