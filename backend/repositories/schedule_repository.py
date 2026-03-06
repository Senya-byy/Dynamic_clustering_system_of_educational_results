# backend/repositories/schedule_repository.py
from models import db, ScheduleSlot
from typing import List, Optional


class ScheduleRepository:
    @staticmethod
    def find_by_group_id(group_id: int) -> List[ScheduleSlot]:
        return (
            ScheduleSlot.query.filter_by(group_id=group_id)
            .order_by(ScheduleSlot.weekday, ScheduleSlot.start_time)
            .all()
        )

    @staticmethod
    def find_by_teacher_id(teacher_id: int) -> List[ScheduleSlot]:
        return (
            ScheduleSlot.query.filter_by(teacher_id=teacher_id)
            .order_by(ScheduleSlot.group_id, ScheduleSlot.weekday, ScheduleSlot.start_time)
            .all()
        )

    @staticmethod
    def create(data: dict) -> ScheduleSlot:
        row = ScheduleSlot(**data)
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def update(sid: int, data: dict) -> Optional[ScheduleSlot]:
        row = ScheduleSlot.query.get(sid)
        if not row:
            return None
        for k, v in data.items():
            if hasattr(row, k):
                setattr(row, k, v)
        db.session.commit()
        return row

    @staticmethod
    def delete(sid: int) -> bool:
        row = ScheduleSlot.query.get(sid)
        if not row:
            return False
        db.session.delete(row)
        db.session.commit()
        return True
