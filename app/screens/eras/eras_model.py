from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from services.firestore_service import ActiveIncursion


@dataclass(frozen=True)
class EraCardModel:
    era_id: str
    index: int
    status_label: str
    status_color: str
    incursion_label: str
    incursion_color: str
    score_total: int
    completed_incursions: int
    score_average: float | None
    active_incursion: ActiveIncursion | None


def get_era_status(era: dict) -> tuple[str, str]:
    is_active = bool(era.get("is_active"))
    return (
        "Activa",
        ft.Colors.GREEN_600,
    ) if is_active else ("Inactiva", ft.Colors.GREY_500)


def get_incursion_status(has_active_incursion: bool) -> tuple[str, str]:
    if has_active_incursion:
        return "Incursión activa", ft.Colors.GREEN_600
    return "Sin incursión activa", ft.Colors.GREY_500


def compute_era_score_summary(
    incursions_by_period: dict[str, list[dict]],
) -> tuple[int, int, float | None]:
    score_total = 0
    completed_incursions = 0
    for incursions in incursions_by_period.values():
        for incursion in incursions:
            score = incursion.get("score")
            if isinstance(score, bool):
                continue
            if isinstance(score, (int, float)):
                score_total += int(score)
                completed_incursions += 1
    score_average = (
        score_total / completed_incursions if completed_incursions else None
    )
    return score_total, completed_incursions, score_average


def format_score_average(score_average: float | None) -> str:
    if score_average is None:
        return "—"
    return f"{score_average:.2f}"
