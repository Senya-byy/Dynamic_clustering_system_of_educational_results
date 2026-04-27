from __future__ import annotations

from typing import Any, Mapping

from flask import Request


def require_json(request: Request) -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Тело запроса должно быть JSON-объектом")
    return data


def get_str(
    payload: Mapping[str, Any],
    key: str,
    *,
    required: bool = False,
    min_len: int | None = None,
    max_len: int | None = None,
    strip: bool = True,
) -> str | None:
    raw = payload.get(key)
    if raw is None:
        if required:
            raise ValueError(f"{key} обязателен")
        return None
    s = str(raw)
    if strip:
        s = s.strip()
    if required and s == "":
        raise ValueError(f"{key} обязателен")
    if min_len is not None and len(s) < min_len:
        raise ValueError(f"{key} слишком короткий")
    if max_len is not None and len(s) > max_len:
        raise ValueError(f"{key} слишком длинный")
    return s


def get_int(
    payload: Mapping[str, Any],
    key: str,
    *,
    required: bool = False,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int | None:
    raw = payload.get(key)
    if raw is None or raw == "":
        if required:
            raise ValueError(f"{key} обязателен")
        return None
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{key} должен быть целым числом")
    if min_value is not None and v < min_value:
        raise ValueError(f"{key} должен быть >= {min_value}")
    if max_value is not None and v > max_value:
        raise ValueError(f"{key} должен быть <= {max_value}")
    return v


def get_bool(payload: Mapping[str, Any], key: str) -> bool | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    s = str(raw).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    raise ValueError(f"{key} должен быть boolean")

