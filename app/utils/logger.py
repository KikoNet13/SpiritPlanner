from __future__ import annotations

from collections import deque
from datetime import datetime
from functools import wraps
import logging
import platform
import sys
from typing import Callable, Deque, TypeVar

_NOISY_PREFIXES = (
    "flet",
    "flet_core",
    "flet_runtime",
    "flet_socket_server",
    "base_control",
)

_LOGGING_CONFIGURED = False
_DEBUG_ENABLED = False
_RING_BUFFER: Deque[str] = deque(maxlen=200)

_FORMATTER = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    "%Y-%m-%d %H:%M:%S",
)


class _NoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        return not record.name.startswith(_NOISY_PREFIXES)


class _RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = _FORMATTER.format(record)
        except Exception:
            message = record.getMessage()
        _RING_BUFFER.append(message)


def configure_logging(debug: bool = False) -> None:
    global _DEBUG_ENABLED, _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    _DEBUG_ENABLED = debug
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    ring_handler = _RingBufferHandler()
    ring_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(ring_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)
    console_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
    console_handler.addFilter(_NoiseFilter())
    root_logger.addHandler(console_handler)

    for noisy_logger in _NOISY_PREFIXES:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    _LOGGING_CONFIGURED = True
    root_logger.debug("Logging configured debug=%s", debug)


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)


def get_debug_report() -> str:
    header = [
        "SpiritPlanner debug report",
        f"timestamp: {datetime.now().isoformat()}",
        f"python: {sys.version.replace(chr(10), ' ')}",
        f"platform: {platform.platform()}",
        f"debug: {_DEBUG_ENABLED}",
        "",
        "Recent logs:",
    ]
    if not _RING_BUFFER:
        return "\n".join(header + ["(no logs captured)"])
    return "\n".join(header + list(_RING_BUFFER))


EventHandler = TypeVar("EventHandler", bound=Callable[..., object])


def safe_event_handler(handler: EventHandler) -> EventHandler:
    @wraps(handler)
    def wrapper(*args: object, **kwargs: object) -> object:
        try:
            return handler(*args, **kwargs)
        except Exception:
            logging.getLogger(handler.__module__).exception(
                "Unhandled exception in event handler %s", handler.__name__
            )
            raise

    return wrapper  # type: ignore[return-value]
