from __future__ import annotations

import flet as ft

from app.screens.shared_components import section_card, status_chip


def incursion_card(
    title: str,
    spirit_info: str,
    board_info: str,
    layout_info: str,
    adversary_info: str,
    status_label: str,
    status_color: str,
    on_open,
) -> ft.Container:
    return section_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.EXPLORE),
                    title=ft.Text(title, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Column(
                        [
                            ft.Text(f"Espíritus: {spirit_info}"),
                            ft.Text(f"Tableros: {board_info}"),
                            ft.Text(f"Distribución: {layout_info}"),
                            ft.Text(f"Adversario: {adversary_info}"),
                            status_chip(status_label, status_color),
                        ],
                        spacing=4,
                    ),
                ),
                ft.Row(
                    [
                        ft.ElevatedButton("Abrir", on_click=on_open),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=4,
        )
    )
