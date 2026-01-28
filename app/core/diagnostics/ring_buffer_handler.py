from __future__ import annotations

from collections import deque
import logging

_BUFFER: deque[str] = deque(maxlen=300)


class RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        _BUFFER.append(message)


def get_recent_logs() -> str:
    return "\n".join(_BUFFER)
