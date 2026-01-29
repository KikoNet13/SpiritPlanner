from __future__ import annotations

import flet as ft

from app.screens.eras.eras_model import (
    EraCardModel,
    get_era_status,
    get_incursion_status,
)
from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


@ft.observable
class ErasViewModel:
    def __init__(self, page: ft.Page, service: FirestoreService) -> None:
        self.page = page
        self.service = service
        self.eras: list[EraCardModel] = []
        self.loading = False
        self.error: str | None = None

    def load_eras(self) -> None:
        logger.info("Firestore list eras")
        self.loading = True
        self.error = None
        try:
            eras = self.service.list_eras()
            cards: list[EraCardModel] = []
            for idx, era in enumerate(eras, start=1):
                era_id = era["id"]
                active_incursion = self.service.get_active_incursion(era_id)
                status_label, status_color = get_era_status(era)
                incursion_label, incursion_color = get_incursion_status(
                    active_incursion is not None
                )
                cards.append(
                    EraCardModel(
                        era_id=era_id,
                        index=idx,
                        status_label=status_label,
                        status_color=status_color,
                        incursion_label=incursion_label,
                        incursion_color=incursion_color,
                        active_incursion=active_incursion,
                    )
                )
            self.eras = cards
        except Exception as exc:
            logger.error("Failed to load eras error=%s", exc, exc_info=True)
            self.error = "load_failed"
            self.eras = []
        finally:
            self.loading = False

    def open_periods_handler(self, era_id: str):
        logger.info("UI open periods era_id=%s", era_id)
        return go_to(self.page, f"/eras/{era_id}")

    def open_active_incursion_handler(self, active_incursion):
        logger.info(
            "UI open active incursion era_id=%s period_id=%s incursion_id=%s",
            active_incursion.era_id,
            active_incursion.period_id,
            active_incursion.incursion_id,
        )
        return go_to(
            self.page,
            (
                f"/eras/{active_incursion.era_id}/periods/{active_incursion.period_id}"
                f"/incursions/{active_incursion.incursion_id}"
            ),
        )
