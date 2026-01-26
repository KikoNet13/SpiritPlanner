from __future__ import annotations

import flet as ft


def get_era_status(era: dict) -> tuple[str, str]:
    is_active = bool(era.get("is_active"))
    return ("Activa", ft.Colors.GREEN_600) if is_active else ("Inactiva", ft.Colors.GREY_500)


def get_incursion_status(active_count: int) -> tuple[str, str]:
    if active_count == 1:
        return "Incursión activa", ft.Colors.GREEN_600
    if active_count > 1:
        return "Incursiones múltiples", ft.Colors.ORANGE_600
    return "Sin incursión activa", ft.Colors.GREY_500
