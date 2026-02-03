from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from weakref import WeakKeyDictionary

import flet as ft

from app.utils.logger import get_logger

_ROUTER_REGISTRY: WeakKeyDictionary[ft.Page, "RouterCoordinator"] = WeakKeyDictionary()
_ROUTE_LOADERS: WeakKeyDictionary[
    ft.Page, dict[str, "RouteLoader"]
] = WeakKeyDictionary()

logger = get_logger(__name__)

RouteParams = dict[str, str]
RouteLoader = Callable[[RouteParams], None]


def normalize_route(route: str | None) -> str:
    if not route:
        return "/eras"
    normalized = route.strip()
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if normalized.endswith("/") and normalized != "/":
        normalized = normalized.rstrip("/")
    if not normalized or normalized == "/":
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

    if len(parts) == 6 and parts[4] == "incursions":
        incursion_id = parts[5]
        routes.append(
            f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}"
        )
        return routes

    return ["/eras"]


def resolve_route_target(route: str) -> tuple[str, RouteParams]:
    normalized = normalize_route(route)
    parts = [part for part in normalized.split("/") if part]
    if not parts or parts[0] != "eras":
        return "/eras", {}
    if len(parts) == 1:
        return "/eras", {}
    if len(parts) == 2:
        return "/eras/{era_id}", {"era_id": parts[1]}
    if len(parts) >= 4 and parts[2] == "periods":
        if len(parts) == 4:
            return "/eras/{era_id}/periods/{period_id}", {
                "era_id": parts[1],
                "period_id": parts[3],
            }
        if len(parts) == 6 and parts[4] == "incursions":
            return "/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}", {
                "era_id": parts[1],
                "period_id": parts[3],
                "incursion_id": parts[5],
            }
    return "/eras", {}


def register_route_loader(
    page: ft.Page, base_route: str, loader: "RouteLoader"
) -> None:
    loaders = _ROUTE_LOADERS.setdefault(page, {})
    loaders[normalize_route(base_route)] = loader


def refresh_route(page: ft.Page, route: str) -> None:
    base_route, params = resolve_route_target(route)
    loaders = _ROUTE_LOADERS.get(page, {})
    loader = loaders.get(normalize_route(base_route))
    if loader is None:
        logger.debug("No loader registered for route=%s base=%s", route, base_route)
        return
    logger.info("Refreshing route=%s base=%s params=%s", route, base_route, params)
    loader(params)


@ft.observable
@dataclass
class RouterCoordinator:
    route: str
    pending_refresh: str | None = field(default=None, init=False)

    def on_route_change(self, e: ft.RouteChangeEvent) -> None:
        self.route = normalize_route(e.route)
        page = e.page or ft.context.page
        if self.pending_refresh == self.route:
            self.pending_refresh = None
            return
        refresh_route(page, self.route)

    async def on_view_pop(self, e: ft.ViewPopEvent) -> None:
        page = e.page or ft.context.page
        popped_route = None
        if e.view is not None:
            popped_route = e.view.route
        elif e.route:
            popped_route = e.route
        current_route = normalize_route(popped_route or page.route)
        stack = build_route_stack(current_route)
        if len(stack) > 1:
            target_route = stack[-2]
            refresh_route(page, target_route)
            self.pending_refresh = normalize_route(target_route)
            await page.push_route(stack[-2])
            return
        refresh_route(page, "/eras")
        self.pending_refresh = "/eras"
        await page.push_route("/eras")


def get_router(page: ft.Page) -> RouterCoordinator:
    router = _ROUTER_REGISTRY.get(page)
    if router is None:
        router = RouterCoordinator(route=normalize_route(page.route))
        _ROUTER_REGISTRY[page] = router
    return router
