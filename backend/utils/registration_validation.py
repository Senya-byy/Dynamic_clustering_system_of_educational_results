# backend/utils/registration_validation.py
from __future__ import annotations

import re

_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁё]")
_DIGIT_RE = re.compile(r"\d")
_LOGIN_RE = re.compile(r"^[a-zA-Z0-9._-]{3,50}$")


def normalize_login(login: str) -> str:
    return (login or "").strip().lower()


def validate_login(login: str) -> str:
    ln = normalize_login(login)
    if not ln:
        raise ValueError("Укажите логин")
    if not _LOGIN_RE.match(ln):
        raise ValueError(
            "Логин: 3–50 символов, только латиница, цифры и символы . _ -"
        )
    return ln


def validate_password(password: str) -> str:
    p = password if isinstance(password, str) else str(password)
    if len(p) < 8:
        raise ValueError("Пароль: не короче 8 символов")
    if len(p) > 128:
        raise ValueError("Пароль: не длиннее 128 символов")
    if not _LETTER_RE.search(p):
        raise ValueError("Пароль: нужна хотя бы одна буква (латиница или кириллица)")
    if not _DIGIT_RE.search(p):
        raise ValueError("Пароль: нужна хотя бы одна цифра")
    return p


def validate_full_name(full_name: str) -> str:
    s = (full_name or "").strip()
    if len(s) < 8:
        raise ValueError("ФИО: не короче 8 символов")
    if len(s) > 200:
        raise ValueError("ФИО: не длиннее 200 символов")
    parts = [p for p in re.split(r"\s+", s) if p]
    if len(parts) < 2:
        raise ValueError("ФИО: укажите фамилию и имя (желательно с отчеством), через пробел")
    for p in parts:
        if len(p) < 2:
            raise ValueError("ФИО: каждое слово не короче 2 символов")
    return s


def parse_new_group_names(raw: list | None) -> list[str]:
    if not raw:
        return []
    if not isinstance(raw, list):
        raise ValueError("new_group_names должен быть массивом строк")
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        name = str(item).strip()
        if not name:
            continue
        if len(name) > 100:
            raise ValueError("Название группы не длиннее 100 символов")
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out
