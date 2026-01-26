from __future__ import annotations

import flet as ft

from app.screens.data_lookup import (
    get_adversary_name,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)


def get_incursion_status(incursion: dict) -> tuple[str, str]:
    if incursion.get("ended_at") or incursion.get("result"):
        return "Finalizado", ft.Colors.BLUE_600
    if incursion.get("is_active"):
        return "Activo", ft.Colors.GREEN_600
    return "No iniciado", ft.Colors.GREY_500


def get_spirit_info(incursion: dict) -> str:
    return (
        f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
        f"{get_spirit_name(incursion.get('spirit_2_id'))}"
    )


def get_board_info(incursion: dict) -> str:
    return (
        f"{get_board_name(incursion.get('board_1'))} + "
        f"{get_board_name(incursion.get('board_2'))}"
    )


def get_layout_info(incursion: dict) -> str:
    return get_layout_name(incursion.get("board_layout"))


def get_adversary_info(incursion: dict) -> str:
    return get_adversary_name(incursion.get("adversary_id"))
