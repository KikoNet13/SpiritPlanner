from __future__ import annotations

from collections import deque
from datetime import datetime
import json
import logging
from pathlib import Path
import traceback
from typing import Callable, Deque, Iterable

import flet as ft

_DEFAULT_BUFFER_SIZE = 300


class _NoiseFilter(logging.Filter):
    _NOISY_PREFIXES: tuple[str, ...] = (
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


class _RingBufferHandler(logging.Handler):
    def __init__(self, buffer: Deque[str], formatter: logging.Formatter) -> None:
        super().__init__()
        self._buffer = buffer
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self._buffer.append(message)


_LOGGER_CONFIGURED = False
_RING_BUFFER: Deque[str] = deque(maxlen=_DEFAULT_BUFFER_SIZE)
_QUIET_LOGGERS: tuple[str, ...] = (
    "screens.data_lookup",
    "google",
    "google.api_core",
    "google.cloud",
    "urllib3",
)


def configure_logging(debug: bool = False) -> None:
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    log_level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_NoiseFilter())
    root_logger.addHandler(console_handler)

    ring_handler = _RingBufferHandler(_RING_BUFFER, formatter)
    ring_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(ring_handler)

    _configure_quiet_loggers()

    _configure_file_handler(root_logger, formatter)

    _LOGGER_CONFIGURED = True
    root_logger.debug("Logging configured debug=%s", debug)


def _configure_quiet_loggers() -> None:
    for logger_name in _QUIET_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def _configure_file_handler(
    logger: logging.Logger, formatter: logging.Formatter
) -> None:
    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = logs_dir / f"spiritplanner-{timestamp}.log"
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
    except OSError:
        logger.warning(
            "Logging file handler disabled: unable to open log file in %s",
            logs_dir,
        )
        return

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_NoiseFilter())
    logger.addHandler(file_handler)
    _cleanup_old_logs(logs_dir)


def _cleanup_old_logs(logs_dir: Path, keep: int = 10) -> None:
    try:
        log_files = sorted(
            logs_dir.glob("spiritplanner-*.log"),
            key=lambda path: path.stat().st_mtime,
        )
    except OSError:
        return
    excess = log_files[:-keep]
    for path in excess:
        try:
            path.unlink()
        except OSError:
            continue


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)


def get_debug_report(
    title: str,
    context: dict | None = None,
    exc: BaseException | None = None,
) -> str:
    timestamp = datetime.now().isoformat(timespec="seconds")
    lines = [title, f"Timestamp: {timestamp}"]

    if context:
        try:
            context_payload = json.dumps(context, ensure_ascii=False, indent=2)
        except TypeError:
            context_payload = str(context)
        lines.extend(["", "Context:", context_payload])

    if exc is not None:
        lines.extend(["", "Exception:"])
        lines.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))

    lines.extend(["", "Recent logs:"])
    lines.extend(_format_ring_buffer(_RING_BUFFER))

    return "\n".join(lines).strip() + "\n"


def _format_ring_buffer(buffer: Iterable[str]) -> list[str]:
    entries = list(buffer)
    if not entries:
        return ["(no log entries)"]
    return entries


def safe_event_handler(
    page: ft.Page,
    fn: Callable[[], None],
    context: dict | Callable[[], dict] | None = None,
) -> None:
    logger = get_logger(__name__)
    try:
        fn()
    except Exception as exc:
        ctx = context() if callable(context) else context
        logger.exception("Unhandled UI exception", extra={"context": ctx})
        report = get_debug_report(
            "Error inesperado", context=ctx, exc=exc
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Se produjo un error inesperado"),
            content=ft.Column(
                [
                    ft.Text(
                        "Copia este informe y envíalo al equipo de soporte.",
                        size=12,
                    ),
                    ft.TextField(
                        value=report,
                        multiline=True,
                        read_only=True,
                        min_lines=8,
                        max_lines=16,
                    ),
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: _close_dialog(page)),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()


def _close_dialog(page: ft.Page) -> None:
    if not page.dialog:
        return
    page.dialog.open = False
    page.update()
