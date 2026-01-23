from __future__ import annotations

from app.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_score(
    difficulty: int,
    result: str,
    invader_cards_remaining: int,
    invader_cards_out_of_deck: int,
    player_count: int,
    dahan_alive: int,
    blight_on_island: int,
) -> int:
    logger.debug(
        "Calculating score difficulty=%s result=%s invader_cards_remaining=%s invader_cards_out_of_deck=%s player_count=%s dahan_alive=%s blight_on_island=%s",
        difficulty,
        result,
        invader_cards_remaining,
        invader_cards_out_of_deck,
        player_count,
        dahan_alive,
        blight_on_island,
    )
    base = player_count * dahan_alive - player_count * blight_on_island
    if result == "win":
        score = (
            5 * difficulty
            + 10
            + 2 * invader_cards_remaining
            + base
        )
        logger.debug("Score calculated=%s result=win", score)
        return score
    score = 2 * difficulty + invader_cards_out_of_deck + base
    logger.debug("Score calculated=%s result=loss", score)
    return score
