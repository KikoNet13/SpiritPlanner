from __future__ import annotations

import flet as ft

from app.screens.eras_screen import eras_view
from app.screens.incursion_detail_screen import incursion_detail_view
from app.screens.incursions_screen import incursions_view
from app.screens.periods_screen import periods_view
from app.services.firestore_service import FirestoreService


def main(page: ft.Page) -> None:
    page.title = "SpiritPlanner"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    service = FirestoreService()

    def handle_route_change(route: ft.RouteChangeEvent) -> None:
        page.views.clear()
        page.views.append(eras_view(page, service))

        parts = [part for part in route.route.split("/") if part]
        if len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            page.views.append(periods_view(page, service, era_id))
        if len(parts) >= 4 and parts[0] == "eras" and parts[2] == "periods":
            era_id = parts[1]
            period_id = parts[3]
            page.views.append(incursions_view(page, service, era_id, period_id))
        if (
            len(parts) >= 6
            and parts[0] == "eras"
            and parts[2] == "periods"
            and parts[4] == "incursions"
        ):
            era_id = parts[1]
            period_id = parts[3]
            incursion_id = parts[5]
            page.views.append(
                incursion_detail_view(page, service, era_id, period_id, incursion_id)
            )
        page.update()

    def handle_view_pop(view: ft.ViewPopEvent) -> None:
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop
    page.go("/eras")


if __name__ == "__main__":
    ft.app(target=main)
