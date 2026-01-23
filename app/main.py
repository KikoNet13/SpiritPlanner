from __future__ import annotations

import flet as ft

from app.navigation.navigator import Navigator
from app.screens.eras_screen import eras_view
from app.screens.incursion_detail_screen import incursion_detail_view
from app.screens.incursions_screen import incursions_view
from app.screens.periods_screen import periods_view
from app.services.firestore_service import FirestoreService


async def main(page: ft.Page) -> None:
    page.title = "SpiritPlanner"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    service = FirestoreService()
    navigator = Navigator(page)

    def add_view(route: str, content: ft.Control) -> None:
        page.views.append(ft.View(route=route, controls=[content]))

    async def handle_route_change(event: ft.RouteChangeEvent) -> None:
        page.views.clear()
        parts = [part for part in event.route.split("/") if part]

        add_view("/eras", eras_view(page, service, navigator))

        if len(parts) >= 2 and parts[0] == "eras":
            era_id = parts[1]
            add_view(f"/eras/{era_id}", periods_view(page, service, navigator, era_id))

            if len(parts) >= 4 and parts[2] == "periods":
                period_id = parts[3]
                add_view(
                    f"/eras/{era_id}/periods/{period_id}",
                    incursions_view(page, service, navigator, era_id, period_id),
                )

                if len(parts) >= 6 and parts[4] == "incursions":
                    incursion_id = parts[5]
                    add_view(
                        f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
                        incursion_detail_view(
                            page, service, era_id, period_id, incursion_id
                        ),
                    )

        page.update()

    async def handle_view_pop(event: ft.ViewPopEvent) -> None:
        if page.views:
            page.views.pop()
        if not page.views:
            await navigator.go("/eras")
            return
        top_view = page.views[-1]
        await navigator.go(top_view.route)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    await navigator.go("/eras")


if __name__ == "__main__":
    ft.run(main)
