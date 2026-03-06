# backend/repositories/answer_repository.py
from models import db, Answer
from datetime import datetime
from typing import Optional, List


class AnswerRepository:
    @staticmethod
    def create(data: dict) -> Answer:
        ans = Answer(**data)
        db.session.add(ans)
        db.session.commit()
        return ans

    @staticmethod
    def find_by_session(session_id: int) -> List[Answer]:
        return Answer.query.filter_by(session_id=session_id).all()

    @staticmethod
    def find_by_session_student(session_id: int, student_id: int) -> Optional[Answer]:
        return Answer.query.filter_by(
            session_id=session_id, student_id=student_id
        ).first()

    @staticmethod
    def find_by_student(student_id: int) -> List[Answer]:
        return Answer.query.filter_by(student_id=student_id).all()

    @staticmethod
    def find_by_id(aid: int) -> Optional[Answer]:
        return Answer.query.get(aid)

    @staticmethod
    def update_score(
        aid: int,
        score: int,
        comment: str,
        checker_id: int,
        is_correct: Optional[bool] = None,
    ) -> Answer:
        ans = Answer.query.get(aid)
        ans.score = score
        ans.comment = comment
        ans.checked_by = checker_id
        ans.checked_at = datetime.utcnow()
        if is_correct is not None:
            ans.is_correct = is_correct
        db.session.commit()
        return ans

    @staticmethod
    def mark_late(aid: int) -> bool:
        ans = Answer.query.get(aid)
        ans.is_late = True
        db.session.commit()
        return True
