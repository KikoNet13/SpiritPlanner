from __future__ import annotations

import flet as ft

from screens.incursions.incursions_model import (
    IncursionCardModel,
    get_adversary_info,
    get_board_info,
    get_incursion_status,
    get_layout_info,
    get_spirit_info,
)
from services.firestore_service import FirestoreService
from utils.logger import get_logger

logger = get_logger(__name__)


@ft.observable
class IncursionsViewModel:
    def __init__(self) -> None:
        self.era_id: str | None = None
        self.period_id: str | None = None
        self.loading = False
        self.error: str | None = None
        self.incursions: list[IncursionCardModel] = []
        self.toast_message: str | None = None
        self.toast_version = 0
        self.navigate_to: str | None = None
        self.nav_version = 0

    def ensure_loaded(
        self, service: FirestoreService, era_id: str, period_id: str
    ) -> None:
        self.era_id = era_id
        self.period_id = period_id
        self.load_incursions(service)

    def load_incursions(self, service: FirestoreService) -> None:
        if not self.era_id or not self.period_id:
            return
        logger.info(
            "Firestore list incursions era_id=%s period_id=%s",
            self.era_id,
            self.period_id,
        )
        self.loading = True
        self.error = None
        try:
            incursions = service.list_incursions(self.era_id, self.period_id)
            cards: list[IncursionCardModel] = []
            for incursion in incursions:
                status_label, status_color = get_incursion_status(incursion)
                cards.append(
                    IncursionCardModel(
                        incursion_id=incursion["id"],
                        title=f"Incursión {incursion.get('index', 0)}",
                        spirit_info=get_spirit_info(incursion),
                        board_info=get_board_info(incursion),
                        layout_info=get_layout_info(incursion),
                        adversary_info=get_adversary_info(incursion),
                        status_label=status_label,
                        status_color=status_color,
                    )
                )
            self.incursions = cards
        except Exception as exc:
            logger.error(
                "Failed to load incursions era_id=%s period_id=%s error=%s",
                self.era_id,
                self.period_id,
                exc,
                exc_info=True,
            )
            self.error = "load_failed"
            self.incursions = []
        finally:
            self.loading = False

    def request_open_incursion(self, incursion_id: str) -> None:
        if not self.era_id or not self.period_id:
            return
        logger.info(
            "UI open incursion era_id=%s period_id=%s incursion_id=%s",
            self.era_id,
            self.period_id,
            incursion_id,
        )
        self.navigate_to = (
            f"/eras/{self.era_id}/periods/{self.period_id}/incursions/{incursion_id}"
        )
        self.nav_version += 1

    def show_toast(self, message: str) -> None:
        logger.info("User message shown: %s", message)
        self.toast_message = message
        self.toast_version += 1

    def consume_toast(self) -> None:
        self.toast_message = None

    def consume_navigation(self) -> None:
        self.navigate_to = None
