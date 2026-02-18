from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


SESSION_STATE_NOT_STARTED = "NOT_STARTED"
SESSION_STATE_IN_SESSION = "IN_SESSION"
SESSION_STATE_BETWEEN_SESSIONS = "BETWEEN_SESSIONS"
SESSION_STATE_FINALIZED = "FINALIZED"


@dataclass(frozen=True)
class IncursionDetailModel:
    incursion_id: str
    index: int
    spirit_1_name: str
    spirit_2_name: str
    layout_id: str
    board_1_name: str
    board_2_name: str
    layout_name: str
    board_1_id: str
    board_2_id: str
    adversary_id: str | None
    adversary_name: str
    adversary_level: str | None
    difficulty: int | None
    period_label: str
    result: str | None
    score: int | None
    dahan_alive: int | None
    blight_on_island: int | None
    player_count: int | None
    invader_cards_remaining: int | None
    invader_cards_out_of_deck: int | None


@dataclass(frozen=True)
class SessionEntryModel:
    started_at: datetime | None
    ended_at: datetime | None


@dataclass
class FinalizeFormData:
    result: str | None
    dahan_alive: str
    blight_on_island: str
    invader_cards_remaining: str
    invader_cards_out_of_deck: str


def resolve_session_state(
    incursion: dict, has_sessions: bool, open_session: bool
) -> str:
    if incursion.get("ended_at") or incursion.get("result"):
        return SESSION_STATE_FINALIZED
    if has_sessions:
        return SESSION_STATE_IN_SESSION if open_session else SESSION_STATE_BETWEEN_SESSIONS
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
            "5 × dificultad + 10 + 2 × cartas en mazo + 2 × dahan vivos − 2 × plaga"
        )
    if result_value == "loss":
        return (
            "2 × dificultad + 1 × cartas fuera del mazo + 2 × dahan vivos − 2 × plaga"
        )
    return "—"


def compute_score_preview(
    result_value: str | None,
    difficulty: int,
    dahan_alive: int,
    blight_on_island: int,
    player_count: int,
    invader_cards_remaining: int,
    invader_cards_out_of_deck: int,
) -> tuple[str, int | None]:
    base = player_count * (dahan_alive - blight_on_island)
    if result_value == "win":
        return (
            get_score_formula(result_value),
            (
                5 * difficulty
                + 10
                + 2 * invader_cards_remaining
                + base
            ),
        )
    if result_value == "loss":
        return (
            get_score_formula(result_value),
            (
                2 * difficulty
                + invader_cards_out_of_deck
                + base
            ),
        )
    return ("—", None)


def _to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def compute_total_seconds(
    sessions: list[SessionEntryModel], reference: datetime | None = None
) -> int:
    ref = reference or datetime.now(timezone.utc)
    total_seconds = 0
    for session in sessions:
        started_at = _to_utc(session.started_at)
        ended_at = _to_utc(session.ended_at) or ref
        if started_at and ended_at:
            total_seconds += int((ended_at - started_at).total_seconds())
    return max(total_seconds, 0)


def format_duration_hhmmss(total_seconds: int) -> str:
    normalized_seconds = max(int(total_seconds), 0)
    hours, remainder = divmod(normalized_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
