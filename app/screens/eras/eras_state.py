from __future__ import annotations

import flet as ft


def get_era_status(era: dict) -> tuple[str, str]:
    is_active = bool(era.get("is_active"))
    return ("Activa", ft.Colors.GREEN_600) if is_active else ("Inactiva", ft.Colors.GREY_500)


def get_incursion_status(has_active_incursion: bool) -> tuple[str, str]:
    if has_active_incursion:
        return "Incursión activa", ft.Colors.GREEN_600
    return "Sin incursión activa", ft.Colors.GREY_500
