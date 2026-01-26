from __future__ import annotations


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
