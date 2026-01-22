from __future__ import annotations


def calculate_score(
    difficulty: int,
    result: str,
    invader_cards_remaining: int,
    invader_cards_out_of_deck: int,
    player_count: int,
    dahan_alive: int,
    blight_on_island: int,
) -> int:
    base = player_count * dahan_alive - player_count * blight_on_island
    if result == "win":
        return (
            5 * difficulty
            + 10
            + 2 * invader_cards_remaining
            + base
        )
    return 2 * difficulty + invader_cards_out_of_deck + base
