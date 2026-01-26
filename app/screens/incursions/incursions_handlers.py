from __future__ import annotations

import flet as ft

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger
from app.utils.navigation import go_to

logger = get_logger(__name__)


def build_open_incursion_handler(
    page: ft.Page,
    era_id: str,
    period_id: str,
    incursion_id: str,
):
    logger.debug("Binding open incursion handler incursion_id=%s", incursion_id)
    return go_to(
        page,
        f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
    )


def list_incursions(
    service: FirestoreService, era_id: str, period_id: str
) -> list[dict]:
    logger.debug("Loading incursions era_id=%s period_id=%s", era_id, period_id)
    return service.list_incursions(era_id, period_id)
