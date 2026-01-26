from __future__ import annotations

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


def build_open_periods_handler(page: ft.Page, era_id: str):
    logger.debug("Binding open periods handler era_id=%s", era_id)
    return go_to(page, f"/eras/{era_id}")


def build_open_active_handler(page: ft.Page, active_incursion):
    logger.debug(
        "Binding open active incursion handler active_incursion=%s",
        active_incursion,
    )
    return go_to(
        page,
        (
            f"/eras/{active_incursion.era_id}/periods/{active_incursion.period_id}"
            f"/incursions/{active_incursion.incursion_id}"
        ),
    )


def get_active_incursion(service: FirestoreService, era_id: str):
    return service.get_active_incursion(era_id)
