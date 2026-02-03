from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from app.screens.data_lookup import get_board_name, get_layout_name, get_spirit_name


@dataclass(frozen=True)
class PeriodRowModel:
    period_id: str
    title: str
    action: str | None
    center_actions: bool
    status_label: str
    status_color: str
    incursion_count: int
    incursions_preview: tuple[str, ...]


@dataclass(frozen=True)
class AssignmentIncursionModel:
    incursion_id: str
    index: int
    spirit_1_name: str
    spirit_2_name: str
    board_1_name: str
    board_2_name: str
    layout_id: str
    layout_name: str


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


def get_period_status(period: dict) -> tuple[str, str]:
    if period.get("ended_at"):
        return "Finalizado", ft.Colors.BLUE_600
    if period.get("adversaries_assigned_at"):
        return "Preparado", ft.Colors.GREEN_600
    if period.get("revealed_at"):
        return "Revelado", ft.Colors.AMBER_700
    return "Pendiente", ft.Colors.GREY_500


def get_incursion_count(period: dict, incursions: list[dict]) -> int:
    raw_count = period.get("incursions_count")
    if raw_count is None:
        raw_count = period.get("incursions")
    if isinstance(raw_count, (list, tuple)):
        raw_count = len(raw_count)
    if isinstance(raw_count, int) and raw_count > 0:
        return raw_count
    if incursions:
        return len(incursions)
    return 4


def build_period_rows(
    periods: list[dict],
    incursions_by_period: dict[str, list[dict]],
) -> list[PeriodRowModel]:
    rows: list[PeriodRowModel] = []
    for idx, period in enumerate(periods):
        period_id = period["id"]
        action = get_period_action(period, can_reveal(periods, idx))
        status_label, status_color = get_period_status(period)
        center_actions = action == "reveal"
        incursions = incursions_by_period.get(period_id, [])
        incursion_count = get_incursion_count(period, incursions)
        preview_lines: list[str] = []
        if period.get("revealed_at") and incursions:
            for incursion in sorted(
                incursions,
                key=lambda item: item.get("index", 0),
            ):
                spirit_1 = get_spirit_name(incursion.get("spirit_1_id"))
                spirit_2 = get_spirit_name(incursion.get("spirit_2_id"))
                preview_lines.append(
                    f"Incursión {incursion.get('index', 0)}: {spirit_1} · {spirit_2}"
                )
        rows.append(
            PeriodRowModel(
                period_id=period_id,
                title=f"Período {period.get('index', 0)}",
                action=action,
                center_actions=center_actions,
                status_label=status_label,
                status_color=status_color,
                incursion_count=incursion_count,
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
                board_1_name=get_board_name(incursion.get("board_1")),
                board_2_name=get_board_name(incursion.get("board_2")),
                layout_id=incursion.get("board_layout") or "",
                layout_name=get_layout_name(incursion.get("board_layout")),
            )
        )
    return items
