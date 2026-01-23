from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path

_LOGGER_CONFIGURED = False
_LOG_FILE_PATH: Path | None = None


def _configure_logging() -> None:
    global _LOGGER_CONFIGURED, _LOG_FILE_PATH
    if _LOGGER_CONFIGURED:
        return

    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _LOG_FILE_PATH = logs_dir / f"spiritplanner_{timestamp}.log"

    handler = logging.FileHandler(_LOG_FILE_PATH, encoding="utf-8")
    formatter = logging.Formatter(
        "%(levelname)s %(filename)s %(funcName)s %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    _LOGGER_CONFIGURED = True
    root_logger.debug("Logging initialized. log_file=%s", _LOG_FILE_PATH)


def get_logger(name: str | None = None) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)
