# backend/utils/device_key.py
import re

_DEVICE_RE = re.compile(r'^[a-zA-Z0-9_-]{8,128}$')


def normalize_device_key(raw: str) -> str:
    s = (raw or '').strip()
    if not _DEVICE_RE.match(s):
        raise ValueError(
            'Некорректный device_id. Обновите страницу или откройте сайт в актуальной вкладке.'
        )
    return s
