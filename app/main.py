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

    def render_route(route: str) -> None:
        page.controls.clear()
        parts = [part for part in route.split("/") if part]
        if (
            len(parts) >= 6
            and parts[0] == "eras"
            and parts[2] == "periods"
            and parts[4] == "incursions"
        ):
            era_id = parts[1]
            period_id = parts[3]
            incursion_id = parts[5]
            page.controls.append(
                incursion_detail_view(page, service, era_id, period_id, incursion_id)
            )
        elif len(parts) >= 4 and parts[0] == "eras" and parts[2] == "periods":
            era_id = parts[1]
            period_id = parts[3]
            page.controls.append(incursions_view(page, service, era_id, period_id))
        elif len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            page.controls.append(periods_view(page, service, era_id))
        else:
            page.controls.append(eras_view(page, service))
        page.update()

    def handle_route_change(route: ft.RouteChangeEvent) -> None:
        render_route(route.route)

    page.on_route_change = handle_route_change

    page.push_route("/eras")


if __name__ == "__main__":
    ft.run(main)
