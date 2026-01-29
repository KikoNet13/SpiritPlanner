from __future__ import annotations

from dataclasses import dataclass

from app.screens.data_lookup import get_spirit_name


@dataclass(frozen=True)
class PeriodRowModel:
    period_id: str
    title: str
    action: str | None
    center_actions: bool
    incursions_preview: tuple[str, ...]


@dataclass(frozen=True)
class AssignmentIncursionModel:
    incursion_id: str
    index: int
    spirit_1_name: str
    spirit_2_name: str


def can_reveal(periods: list[dict], index: int) -> bool:
    if index == 0:
        return True
    previous = periods[index - 1]
    return bool(previous.get("ended_at"))


def get_period_action(period: dict, allow_reveal: bool) -> str | None:
    if period.get("ended_at"):
        return "results"
    if period.get("adversaries_assigned_at"):
        return "incursions"
    if period.get("revealed_at"):
        return "assign"
    if allow_reveal:
        return "reveal"
    return None


def build_period_rows(
    periods: list[dict],
    incursions_by_period: dict[str, list[dict]],
) -> list[PeriodRowModel]:
    rows: list[PeriodRowModel] = []
    for idx, period in enumerate(periods):
        period_id = period["id"]
        action = get_period_action(period, can_reveal(periods, idx))
        center_actions = action == "reveal"
        incursions = incursions_by_period.get(period_id, [])
        preview_lines: list[str] = []
        if period.get("revealed_at") and incursions:
            for incursion in incursions:
                spirit_1 = get_spirit_name(incursion.get("spirit_1_id"))
                spirit_2 = get_spirit_name(incursion.get("spirit_2_id"))
                preview_lines.append(
                    f"Incursión {incursion.get('index', 0)}: {spirit_1} / {spirit_2}"
                )
        rows.append(
            PeriodRowModel(
                period_id=period_id,
                title=f"Periodo {period.get('index', 0)}",
                action=action,
                center_actions=center_actions,
                incursions_preview=tuple(preview_lines),
            )
        )
    return rows


def build_assignment_incursions(incursions: list[dict]) -> list[AssignmentIncursionModel]:
    items: list[AssignmentIncursionModel] = []
    for incursion in incursions:
        items.append(
            AssignmentIncursionModel(
                incursion_id=incursion["id"],
                index=incursion.get("index", 0),
                spirit_1_name=get_spirit_name(incursion.get("spirit_1_id")),
                spirit_2_name=get_spirit_name(incursion.get("spirit_2_id")),
            )
        )
    return items
