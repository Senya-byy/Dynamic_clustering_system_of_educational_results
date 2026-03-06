# backend/repositories/attendance_repository.py
from models import db, Attendance
from datetime import datetime
from typing import List, Optional

class AttendanceRepository:
    @staticmethod
    def mark_present(student_id: int, session_id: int, status='present') -> Attendance:
        # если уже есть запись, обновляем статус
        att = Attendance.query.filter_by(student_id=student_id, session_id=session_id).first()
        if att:
            att.status = status
            att.timestamp = datetime.utcnow()
        else:
            att = Attendance(student_id=student_id, session_id=session_id, status=status)
            db.session.add(att)
        db.session.commit()
        return att

    @staticmethod
    def get_absences(student_id: int, since: datetime = None) -> List[Attendance]:
        query = Attendance.query.filter(Attendance.student_id == student_id, Attendance.status == 'absent')
        if since:
            query = query.filter(Attendance.timestamp >= since)
        return query.all()