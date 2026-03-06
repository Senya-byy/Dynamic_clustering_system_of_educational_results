# backend/services/schedule_service.py
from datetime import datetime
from typing import Dict, List, Optional
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
        if role == 'teacher' and g.teacher_id == user_id:
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
        if not self._can_access_group(group_id, user_id, role) or role == 'student':
            raise PermissionError('Только преподаватель может менять расписание')
        g = self.group_repo.find_by_id(group_id)
        row = self.repo.create({
            'group_id': group_id,
            'teacher_id': g.teacher_id,
            'weekday': int(data['weekday']),
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'title': data.get('title'),
        })
        return self._serialize(row)

    def delete_slot(self, slot_id: int, user_id: int, role: str) -> bool:
        from models import ScheduleSlot
        row = ScheduleSlot.query.get(slot_id)
        if not row:
            return False
        if role not in ('teacher', 'admin'):
            raise PermissionError('Запрещено')
        g = self.group_repo.find_by_id(row.group_id)
        is_admin = role == 'admin'
        if not is_admin and g.teacher_id != user_id:
            raise PermissionError('Нет доступа')
        return self.repo.delete(slot_id)

    def update_slot(self, slot_id: int, data: dict, user_id: int, role: str) -> Optional[dict]:
        from models import ScheduleSlot
        row = ScheduleSlot.query.get(slot_id)
        if not row:
            return None
        if role not in ('teacher', 'admin'):
            raise PermissionError('Запрещено')
        g = self.group_repo.find_by_id(row.group_id)
        is_admin = role == 'admin'
        if not is_admin and g.teacher_id != user_id:
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
