from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def show_message(page: ft.Page, text: str) -> None:
    logger.info("User message shown: %s", text)
    page.snack_bar = ft.SnackBar(ft.Text(text))
    page.snack_bar.open = True
    page.update()


def close_dialog(page: ft.Page, dialog: ft.AlertDialog) -> None:
    logger.debug("Closing dialog title=%s", dialog.title)
    dialog.open = False
    page.update()


def get_incursion(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> dict | None:
    incursions = service.list_incursions(era_id, period_id)
    return next((item for item in incursions if item["id"] == incursion_id), None)


def get_period(service: FirestoreService, era_id: str, period_id: str) -> dict | None:
    return next(
        (item for item in service.list_periods(era_id) if item["id"] == period_id),
        None,
    )


def list_sessions(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> list[dict]:
    return service.list_sessions(era_id, period_id, incursion_id)


def update_adversary_level(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
    adversary_id: str | None,
    adversary_level: str | None,
    difficulty: int | None,
) -> None:
    service.update_incursion_adversary_level(
        era_id=era_id,
        period_id=period_id,
        incursion_id=incursion_id,
        adversary_id=adversary_id,
        adversary_level=adversary_level,
        difficulty=difficulty,
    )


def finalize_incursion(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
    result: str,
    player_count: int,
    invader_cards_remaining: int,
    invader_cards_out_of_deck: int,
    dahan_alive: int,
    blight_on_island: int,
) -> None:
    service.finalize_incursion(
        era_id=era_id,
        period_id=period_id,
        incursion_id=incursion_id,
        result=result,
        player_count=player_count,
        invader_cards_remaining=invader_cards_remaining,
        invader_cards_out_of_deck=invader_cards_out_of_deck,
        dahan_alive=dahan_alive,
        blight_on_island=blight_on_island,
    )


def start_incursion(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> None:
    service.start_incursion(era_id, period_id, incursion_id)


def pause_incursion(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> None:
    service.pause_incursion(era_id, period_id, incursion_id)


def resume_incursion(
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> None:
    service.resume_incursion(era_id, period_id, incursion_id)
