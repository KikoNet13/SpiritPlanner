from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path


class _NoiseFilter(logging.Filter):
    _NOISY_PREFIXES = (
        "flet",
        "flet_core",
        "flet_runtime",
        "flet_socket_server",
        "base_control",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        return not record.name.startswith(self._NOISY_PREFIXES)

_LOGGER_CONFIGURED = False
_LOG_FILE_PATH: Path | None = None


def _configure_logging() -> None:
    global _LOGGER_CONFIGURED, _LOG_FILE_PATH
    if _LOGGER_CONFIGURED:
        return
    root_logger = logging.getLogger()
    if root_logger.handlers:
        _LOGGER_CONFIGURED = True
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
    handler.addFilter(_NoiseFilter())

    debug_enabled = os.getenv("SPIRITPLANNER_DEBUG") == "1"
    root_logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    root_logger.addHandler(handler)
    for noisy_logger in (
        "flet",
        "flet_core",
        "flet_runtime",
        "flet_socket_server",
        "base_control",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    _LOGGER_CONFIGURED = True
    root_logger.debug("Logging initialized. log_file=%s", _LOG_FILE_PATH)


def get_logger(name: str | None = None) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)
