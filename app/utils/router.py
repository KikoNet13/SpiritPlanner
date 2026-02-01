from __future__ import annotations

from dataclasses import dataclass
from weakref import WeakKeyDictionary

import flet as ft

_ROUTER_REGISTRY: WeakKeyDictionary[ft.Page, "RouterCoordinator"] = WeakKeyDictionary()


def normalize_route(route: str | None) -> str:
    if not route or route == "/":
        return "/eras"
    normalized = route
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if normalized.endswith("/") and normalized != "/":
        normalized = normalized.rstrip("/")
    if not normalized:
        return "/eras"
    return normalized


def build_route_stack(route: str) -> list[str]:
    normalized = normalize_route(route)
    parts = [part for part in normalized.split("/") if part]
    if not parts or parts[0] != "eras":
        return ["/eras"]

    routes = ["/eras"]
    if len(parts) < 2:
        return routes

    era_id = parts[1]
    routes.append(f"/eras/{era_id}")

    if len(parts) == 2:
        return routes

    if len(parts) < 4 or parts[2] != "periods":
        return ["/eras"]

    period_id = parts[3]
    routes.append(f"/eras/{era_id}/periods/{period_id}")

    if len(parts) == 4:
        return routes

    if len(parts) < 5 or parts[4] != "incursions":
        return ["/eras"]

    routes.append(f"/eras/{era_id}/periods/{period_id}/incursions")

    if len(parts) == 5:
        return routes

    if len(parts) == 6:
        incursion_id = parts[5]
        routes.append(
            f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}"
        )
        return routes

    return ["/eras"]


@ft.observable
@dataclass
class RouterCoordinator:
    route: str

    def on_route_change(self, e: ft.RouteChangeEvent) -> None:
        self.route = normalize_route(e.route)

    async def on_view_pop(self, e: ft.ViewPopEvent) -> None:
        page = e.page
        views = [
            view
            for view in (
                ft.unwrap_component(view) for view in (page.views or [])
            )
            if isinstance(view, ft.View)
        ]
        if len(views) > 1:
            await page.push_route(views[-2].route)
        else:
            await page.push_route("/eras")


def get_router(page: ft.Page) -> RouterCoordinator:
    router = _ROUTER_REGISTRY.get(page)
    if router is None:
        router = RouterCoordinator(route=normalize_route(page.route))
        _ROUTER_REGISTRY[page] = router
    return router
