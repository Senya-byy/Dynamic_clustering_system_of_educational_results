# backend/repositories/assignment_repository.py
from models import db, SessionStudentAssignment
from typing import Optional


class AssignmentRepository:
    @staticmethod
    def find(session_id: int, student_id: int) -> Optional[SessionStudentAssignment]:
        return SessionStudentAssignment.query.filter_by(
            session_id=session_id, student_id=student_id
        ).first()

    @staticmethod
    def create(session_id: int, student_id: int, question_id: int) -> SessionStudentAssignment:
        row = SessionStudentAssignment(
            session_id=session_id,
            student_id=student_id,
            question_id=question_id,
        )
        db.session.add(row)
        db.session.commit()
        return row
