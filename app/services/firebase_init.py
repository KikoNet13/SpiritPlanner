from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Final

import firebase_admin
from firebase_admin import credentials
from utils.logger import get_logger

logger = get_logger(__name__)

_LOCK: Final[Lock] = Lock()
_ASSETS_DIR_ENV: Final[str] = "FLET_ASSETS_DIR"
_SERVICE_ACCOUNT_RELATIVE_PATH: Final[Path] = Path("secrets") / "service_account.json"


def _get_repo_assets_dir() -> Path:
    # app/services/firebase_init.py -> app/
    app_dir = Path(__file__).resolve().parents[1]
    return app_dir / "assets"


def _resolve_assets_dir() -> Path:
    env_assets_dir = os.getenv(_ASSETS_DIR_ENV, "").strip()
    if env_assets_dir:
        candidate = Path(env_assets_dir)
        if candidate.is_dir():
            return candidate
        logger.warning(
            "%s apunta a una ruta inexistente: %s", _ASSETS_DIR_ENV, candidate
        )

    repo_assets_dir = _get_repo_assets_dir()
    if repo_assets_dir.is_dir():
        return repo_assets_dir

    raise FileNotFoundError(
        f"No se encontró el directorio de assets. "
        f"{_ASSETS_DIR_ENV} no está disponible y el fallback no existe: {repo_assets_dir}"
    )


def _resolve_service_account_path() -> Path:
    assets_dir = _resolve_assets_dir()
    service_account_path = assets_dir / _SERVICE_ACCOUNT_RELATIVE_PATH
    if service_account_path.is_file():
        return service_account_path

    example_path = assets_dir / "secrets" / "service_account.json.example"
    raise FileNotFoundError(
        "No se encontró el JSON de service account para Firebase Admin SDK. "
        f"Ruta esperada: {service_account_path}. "
        f"Ejemplo: {example_path}."
    )


def ensure_firebase_initialized() -> None:
    if firebase_admin._apps:
        return

    with _LOCK:
        if firebase_admin._apps:
            return

        service_account_path = _resolve_service_account_path()
        logger.info(
            "Inicializando Firebase Admin SDK desde service account en assets: %s",
            service_account_path,
        )

        try:
            service_account_data = json.loads(
                service_account_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"El JSON de service account no es válido: {service_account_path}"
            ) from exc

        cred = credentials.Certificate(service_account_data)
        firebase_admin.initialize_app(cred)

