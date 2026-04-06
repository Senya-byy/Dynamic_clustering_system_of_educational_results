# backend/repositories/question_repository.py
from models import db, Question
from typing import Optional, List


class QuestionRepository:
    @staticmethod
    def create(data: dict) -> Question:
        allowed = {
            'text', 'topic', 'topic_id', 'difficulty', 'max_score',
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
    def find_by_topic_id(topic_id: int) -> List[Question]:
        return Question.query.filter_by(topic_id=topic_id).all()

    @staticmethod
    def update(qid: int, data: dict) -> Question:
        q = Question.query.get(qid)
        allowed = {'text', 'topic', 'topic_id', 'difficulty', 'max_score', 'correct_answer'}
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
