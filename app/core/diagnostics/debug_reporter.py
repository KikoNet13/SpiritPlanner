from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import traceback
from typing import Any

from app.core.diagnostics.ring_buffer_handler import get_recent_logs


def _try_get_commit_hash() -> str | None:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return None
    value = result.stdout.strip()
    return value or None


def build_debug_report(
    title: str, context: dict[str, Any], exc: BaseException | None
) -> str:
    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
    commit_hash = _try_get_commit_hash()
    context_lines = []
    for key, value in sorted(context.items()):
        context_lines.append(f"- {key}: {value}")
    context_block = "\n".join(context_lines) if context_lines else "- (sin contexto)"

    if exc is None:
        stacktrace = "No hay stacktrace disponible."
    else:
        stacktrace = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ).strip()

    report_parts = [
        "DEBUG REPORT",
        f"Titulo: {title}",
        f"Timestamp: {timestamp}",
    ]
    if commit_hash:
        report_parts.append(f"Commit: {commit_hash}")
    report_parts.extend(
        [
            "",
            "Contexto:",
            context_block,
            "",
            "Stacktrace:",
            stacktrace,
            "",
            "Ultimas lineas de log:",
            get_recent_logs() or "(sin logs recientes)",
        ]
    )
    return "\n".join(report_parts)
