from __future__ import annotations

from app.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_score(
    difficulty: int,
    result: str,
    dahan_alive: int,
    blight_on_island: int,
) -> int:
    logger.debug(
        "Calculating score difficulty=%s result=%s dahan_alive=%s blight_on_island=%s",
        difficulty,
        result,
        dahan_alive,
        blight_on_island,
    )
    base = dahan_alive - blight_on_island
    if result == "win":
        score = 5 * difficulty + 10 + base
        logger.debug("Score calculated=%s result=win", score)
        return score
    score = 2 * difficulty + base
    logger.debug("Score calculated=%s result=loss", score)
    return score
