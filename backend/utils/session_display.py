# backend/utils/session_display.py
from datetime import datetime
from typing import Any, Optional


def format_session_default_title(start_time: datetime) -> str:
    """Шаблон по умолчанию: «Занятие - 01.01.2026 в 14:30» (дата и время старта пары)."""
    if not start_time:
        start_time = datetime.utcnow()
    return start_time.strftime('Занятие - %d.%m.%Y в %H:%M')


def session_display_title(sess: Any) -> str:
    raw = getattr(sess, 'title', None)
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    st = getattr(sess, 'start_time', None)
    if isinstance(st, datetime):
        return format_session_default_title(st)
    return 'Занятие'
