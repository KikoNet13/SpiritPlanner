from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.diagnostics.ring_buffer_handler import RingBufferHandler

_LOGGING_CONFIGURED = False


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


def _handler_exists(
    root_logger: logging.Logger, handler_type: type[logging.Handler]
) -> bool:
    return any(isinstance(handler, handler_type) for handler in root_logger.handlers)


def configure_logging(debug: bool) -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    logs_dir = Path(__file__).resolve().parents[3] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s | %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if not _handler_exists(root_logger, logging.StreamHandler):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(_NoiseFilter())
        root_logger.addHandler(console_handler)

    if not _handler_exists(root_logger, RotatingFileHandler):
        file_handler = RotatingFileHandler(
            logs_dir / "spiritplanner.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if not _handler_exists(root_logger, RingBufferHandler):
        ring_handler = RingBufferHandler()
        ring_handler.setLevel(logging.DEBUG)
        ring_handler.setFormatter(formatter)
        root_logger.addHandler(ring_handler)

    for noisy_logger in _NoiseFilter._NOISY_PREFIXES:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    _LOGGING_CONFIGURED = True
    root_logger.debug("Diagnostics logging configured. debug=%s", debug)
