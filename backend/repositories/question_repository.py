# backend/repositories/question_repository.py
from sqlalchemy import or_, func

from models import db, Question
from typing import Optional, List


class QuestionRepository:
    @staticmethod
    def create(data: dict) -> Question:
        allowed = {
            'text', 'topic', 'topic_id', 'course_id', 'difficulty', 'max_score',
            'correct_answer', 'created_by',
        }
        row = {k: v for k, v in data.items() if k in allowed}
        q = Question(**row)
        db.session.add(q)
        db.session.commit()
        return q

    @staticmethod
    def find_by_id(qid: int) -> Optional[Question]:
        return Question.query.get(qid)

    @staticmethod
    def find_by_teacher(teacher_id: int) -> List[Question]:
        return Question.query.filter_by(created_by=teacher_id).all()

    @staticmethod
    def search(
        teacher_id: int,
        course_id: int,
        q: str = '',
        topic_id: int | None = None,
        difficulty: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Question]:
        limit = max(1, min(int(limit or 50), 200))
        offset = max(0, int(offset or 0))
        query = Question.query.filter(
            Question.created_by == int(teacher_id),
            Question.course_id == int(course_id),
        )
        if topic_id:
            query = query.filter(Question.topic_id == int(topic_id))
        if difficulty:
            query = query.filter(func.lower(Question.difficulty) == str(difficulty).lower())
        if q:
            like = f"%{q.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Question.text).like(like),
                    func.lower(Question.correct_answer).like(like),
                    func.lower(Question.topic).like(like),
                )
            )
        return query.order_by(Question.id.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def find_by_topic_id(topic_id: int) -> List[Question]:
        return Question.query.filter_by(topic_id=topic_id).all()

    @staticmethod
    def update(qid: int, data: dict) -> Question:
        q = Question.query.get(qid)
        allowed = {'text', 'topic', 'topic_id', 'course_id', 'difficulty', 'max_score', 'correct_answer'}
        for k, v in data.items():
            if k in allowed:
                setattr(q, k, v)
        db.session.commit()
        return q

    @staticmethod
    def delete(qid: int) -> bool:
        q = Question.query.get(qid)
        if q:
            db.session.delete(q)
            db.session.commit()
            return True
        return False
