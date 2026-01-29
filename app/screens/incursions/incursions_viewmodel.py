from __future__ import annotations

import flet as ft

from app.screens.incursions.incursions_model import (
    IncursionCardModel,
    get_adversary_info,
    get_board_info,
    get_incursion_status,
    get_layout_info,
    get_spirit_info,
)
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


@ft.observable
class IncursionsViewModel:
    def __init__(
        self,
        page: ft.Page,
        service: FirestoreService,
        era_id: str,
        period_id: str,
    ) -> None:
        self.page = page
        self.service = service
        self.era_id = era_id
        self.period_id = period_id
        self.loading = False
        self.error: str | None = None
        self.incursions: list[IncursionCardModel] = []

    def load_incursions(self) -> None:
        logger.info(
            "Firestore list incursions era_id=%s period_id=%s",
            self.era_id,
            self.period_id,
        )
        self.loading = True
        self.error = None
        try:
            incursions = self.service.list_incursions(self.era_id, self.period_id)
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

    def open_incursion_handler(self, incursion_id: str):
        logger.info(
            "UI open incursion era_id=%s period_id=%s incursion_id=%s",
            self.era_id,
            self.period_id,
            incursion_id,
        )
        return go_to(
            self.page,
            f"/eras/{self.era_id}/periods/{self.period_id}/incursions/{incursion_id}",
        )
