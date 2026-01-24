from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

from tzlocal import get_localzone

DATETIME_UI_FORMAT = "%d/%m/%y %H:%M"
try:
    _LOCAL_TZ = get_localzone()
except Exception:
    _LOCAL_TZ = timezone.utc


def _parse_datetime(value: Union[datetime, str, None]) -> Optional[datetime]:
    """Parse a datetime or ISO string into an aware UTC datetime."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    elif isinstance(value, datetime):
        parsed = value
    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed


def format_datetime_local(value: Union[datetime, str, None]) -> str:
    """Format a UTC datetime into local time for UI as dd/mm/yy HH:MM."""
    utc_dt = _parse_datetime(value)
    if not utc_dt:
        return "—"

    local_dt = utc_dt.astimezone(_LOCAL_TZ or timezone.utc)
    return local_dt.strftime(DATETIME_UI_FORMAT)
