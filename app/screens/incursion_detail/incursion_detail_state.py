from __future__ import annotations

from datetime import datetime

SESSION_STATE_NOT_STARTED = "NO_INICIADA"
SESSION_STATE_ACTIVE = "ACTIVA"
SESSION_STATE_PAUSED = "PAUSADA"
SESSION_STATE_FINALIZED = "FINALIZADA"


def resolve_session_state(incursion: dict, open_session: bool) -> str:
    if incursion.get("ended_at"):
        return SESSION_STATE_FINALIZED
    if incursion.get("started_at"):
        return SESSION_STATE_ACTIVE if open_session else SESSION_STATE_PAUSED
    return SESSION_STATE_NOT_STARTED


def can_edit_adversary_level(incursion: dict, has_sessions: bool) -> bool:
    return not incursion.get("ended_at") and not has_sessions


def build_period_label(period: dict | None) -> str:
    if not period:
        return "Periodo —"
    return f"Periodo {period.get('index', '—')}"


def get_result_label(result_value: str | None) -> str:
    return "Victoria" if result_value == "win" else "Derrota"


def get_score_formula(result_value: str | None) -> str:
    if result_value == "win":
        return (
            "5 × dificultad + 10 + 2 × cartas restantes + "
            "jugadores × dahan vivos − jugadores × plaga"
        )
    if result_value == "loss":
        return (
            "2 × dificultad + cartas fuera del mazo + "
            "jugadores × dahan vivos − jugadores × plaga"
        )
    return "—"


def total_minutes(sessions: list[dict], now: datetime) -> int:
    total_seconds = 0
    for session in sessions:
        started = session.get("started_at")
        ended = session.get("ended_at") or now
        if started is None:
            continue
        if started.tzinfo is None:
            started = started.replace(tzinfo=now.tzinfo)
        if ended.tzinfo is None:
            ended = ended.replace(tzinfo=now.tzinfo)
        total_seconds += max(0, int((ended - started).total_seconds()))
    return int(total_seconds // 60)


def compute_score_preview(
    result_value: str | None,
    difficulty: int,
    player_count: int,
    dahan_alive: int,
    blight_on_island: int,
    invader_remaining: int,
    invader_out: int,
) -> tuple[str, int | None]:
    if result_value == "win":
        return (
            get_score_formula(result_value),
            (
                5 * difficulty
                + 10
                + 2 * invader_remaining
                + player_count * dahan_alive
                - player_count * blight_on_island
            ),
        )
    if result_value == "loss":
        return (
            get_score_formula(result_value),
            (
                2 * difficulty
                + invader_out
                + player_count * dahan_alive
                - player_count * blight_on_island
            ),
        )
    return ("—", None)
