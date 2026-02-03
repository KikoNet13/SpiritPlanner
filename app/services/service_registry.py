from __future__ import annotations

from app.services.firestore_service import FirestoreService
from app.utils.logger import get_logger

logger = get_logger(__name__)

_FIRESTORE_ATTR = "_sp_firestore_service"


def set_firestore_service(session: object, service: FirestoreService) -> None:
    setattr(session, _FIRESTORE_ATTR, service)
    logger.debug("Firestore service stored in session attr=%s", _FIRESTORE_ATTR)


def get_firestore_service(session: object) -> FirestoreService | None:
    service = getattr(session, _FIRESTORE_ATTR, None)
    if service is None:
        logger.warning("Firestore service not found in session")
    return service
