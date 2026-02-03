from __future__ import annotations

from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_score(
    difficulty: int,
    result: str,
    dahan_alive: int | None,
    blight_on_island: int | None,
    player_count: int | None = None,
    invader_cards_remaining: int | None = None,
    invader_cards_out_of_deck: int | None = None,
) -> int:
    logger.debug(
        "Calculating score difficulty=%s result=%s dahan_alive=%s blight_on_island=%s player_count=%s",
        difficulty,
        result,
        dahan_alive,
        blight_on_island,
        player_count,
    )
    player_multiplier = player_count or 0
    dahan_value = dahan_alive or 0
    blight_value = blight_on_island or 0
    base = player_multiplier * (dahan_value - blight_value)
    if result == "win":
        score = 5 * difficulty + 10 + 2 * (invader_cards_remaining or 0) + base
        logger.debug("Score calculated=%s result=win", score)
        return score
    score = 2 * difficulty + (invader_cards_out_of_deck or 0) + base
    logger.debug("Score calculated=%s result=loss", score)
    return score
