# backend/services/schedule_service.py
import re
from datetime import datetime
from typing import Dict, List, Optional

_HHMM_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")


def _parse_hhmm(raw, label: str) -> str:
    s = "" if raw is None else str(raw)
    m = _HHMM_RE.match(s)
    if not m:
        raise ValueError(f"{label}: укажите время как ЧЧ:ММ (например 09:00)")
    h, mi = int(m.group(1)), int(m.group(2))
    if h < 0 or h > 23 or mi < 0 or mi > 59:
        raise ValueError(f"{label}: некорректное время")
    return f"{h:02d}:{mi:02d}"
from repositories.schedule_repository import ScheduleRepository
from repositories.group_repository import GroupRepository
from repositories.user_repository import UserRepository


class ScheduleService:
    def __init__(self):
        self.repo = ScheduleRepository()
        self.group_repo = GroupRepository()
        self.user_repo = UserRepository()

    def _can_access_group(self, group_id: int, user_id: int, role: str) -> bool:
        g = self.group_repo.find_by_id(group_id)
        if not g:
            return False
        if role == 'admin':
            return True
        if role == 'teacher' and self.group_repo.teacher_has_group(user_id, group_id):
            return True
        if role == 'student':
            u = self.user_repo.find_by_id(user_id)
            return u and u.group_id == group_id
        return False

    def get_schedule(self, group_id: int, user_id: int, role: str) -> List[dict]:
        if not self._can_access_group(group_id, user_id, role):
            raise PermissionError('Нет доступа к расписанию')
        rows = self.repo.find_by_group_id(group_id)
        return [self._serialize(r) for r in rows]

    def create_slot(self, data: dict, user_id: int, role: str) -> dict:
        group_id = data.get('group_id')
        if group_id is None or group_id == "":
            raise ValueError("Укажите group_id")
        try:
            group_id = int(group_id)
        except (TypeError, ValueError):
            raise ValueError("group_id должен быть числом")
        if not self._can_access_group(group_id, user_id, role) or role == 'student':
            raise PermissionError('Только преподаватель может менять расписание')
        g = self.group_repo.find_by_id(group_id)
        if not g:
            raise ValueError("Группа не найдена")
        if 'weekday' not in data:
            raise ValueError("Укажите день недели (0 — понедельник … 6 — воскресенье)")
        wd = int(data['weekday'])
        if wd < 0 or wd > 6:
            raise ValueError("День недели должен быть от 0 до 6")
        start_t = _parse_hhmm(data.get('start_time'), "Начало")
        end_t = _parse_hhmm(data.get('end_time'), 'Конец')
        if start_t >= end_t:
            raise ValueError("Время окончания должно быть позже начала")
        raw_title = data.get('title')
        title = None
        if raw_title is not None and str(raw_title).strip():
            title = str(raw_title).strip()[:200]
        row = self.repo.create({
            'group_id': group_id,
            'teacher_id': user_id,
            'weekday': wd,
            'start_time': start_t,
            'end_time': end_t,
            'title': title,
        })
        return self._serialize(row)

    def delete_slot(self, slot_id: int, user_id: int, role: str) -> bool:
        from models import ScheduleSlot
        row = ScheduleSlot.query.get(slot_id)
        if not row:
            return False
        if role not in ('teacher', 'admin'):
            raise PermissionError('Запрещено')
        is_admin = role == 'admin'
        if not is_admin and not self.group_repo.teacher_has_group(user_id, row.group_id):
            raise PermissionError('Нет доступа')
        return self.repo.delete(slot_id)

    def update_slot(self, slot_id: int, data: dict, user_id: int, role: str) -> Optional[dict]:
        from models import ScheduleSlot
        row = ScheduleSlot.query.get(slot_id)
        if not row:
            return None
        if role not in ('teacher', 'admin'):
            raise PermissionError('Запрещено')
        is_admin = role == 'admin'
        if not is_admin and not self.group_repo.teacher_has_group(user_id, row.group_id):
            raise PermissionError('Нет доступа')
        allowed = {'weekday', 'start_time', 'end_time', 'title'}
        patch = {k: v for k, v in data.items() if k in allowed}
        updated = self.repo.update(slot_id, patch)
        return self._serialize(updated) if updated else None

    def current_slot(self, group_id: int, user_id: int, role: str) -> Optional[dict]:
        """Текущая пара по времени (Should have MoSCoW)."""
        if not self._can_access_group(group_id, user_id, role):
            raise PermissionError('Нет доступа')
        now = datetime.now()
        wd = (now.weekday()) % 7
        hm = now.strftime('%H:%M')
        rows = self.repo.find_by_group_id(group_id)
        for r in rows:
            if r.weekday != wd:
                continue
            if r.start_time <= hm <= r.end_time:
                return {**self._serialize(r), 'is_now': True}
        return {'is_now': False, 'message': 'Сейчас нет пары по расписанию'}

    @staticmethod
    def _serialize(r) -> dict:
        return {
            'id': r.id,
            'group_id': r.group_id,
            'weekday': r.weekday,
            'start_time': r.start_time,
            'end_time': r.end_time,
            'title': r.title,
        }
