from __future__ import annotations

import flet as ft

from screens.eras.eras_model import (
    EraCardModel,
    get_era_status,
    get_incursion_status,
)
from services.firestore_service import FirestoreService
from utils.logger import get_logger

logger = get_logger(__name__)


@ft.observable
class ErasViewModel:
    def __init__(self) -> None:
        self.eras: list[EraCardModel] = []
        self.loading = False
        self.error: str | None = None
        self.toast_message: str | None = None
        self.toast_version = 0
        self.navigate_to: str | None = None
        self.nav_version = 0

    def ensure_loaded(self, service: FirestoreService) -> None:
        self.load_eras(service)

    def load_eras(self, service: FirestoreService) -> None:
        logger.info("Firestore list eras")
        self.loading = True
        self.error = None
        try:
            eras = service.list_eras()
            cards: list[EraCardModel] = []
            for idx, era in enumerate(eras, start=1):
                era_id = era["id"]
                active_incursion = service.get_active_incursion(era_id)
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

    def request_open_periods(self, era_id: str) -> None:
        logger.info("UI open periods era_id=%s", era_id)
        self.navigate_to = f"/eras/{era_id}"
        self.nav_version += 1

    def request_open_active_incursion(self, active_incursion) -> None:
        logger.info(
            "UI open active incursion era_id=%s period_id=%s incursion_id=%s",
            active_incursion.era_id,
            active_incursion.period_id,
            active_incursion.incursion_id,
        )
        self.navigate_to = (
            f"/eras/{active_incursion.era_id}/periods/{active_incursion.period_id}"
            f"/incursions/{active_incursion.incursion_id}"
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
