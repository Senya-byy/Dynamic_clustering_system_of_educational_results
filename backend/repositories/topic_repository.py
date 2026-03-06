# backend/repositories/topic_repository.py
from models import db, Topic
from typing import List, Optional


class TopicRepository:
    @staticmethod
    def create(name: str, teacher_id: int) -> Topic:
        t = Topic(name=name.strip(), teacher_id=teacher_id)
        db.session.add(t)
        db.session.commit()
        return t

    @staticmethod
    def find_by_teacher(teacher_id: int) -> List[Topic]:
        return Topic.query.filter_by(teacher_id=teacher_id).order_by(Topic.name).all()

    @staticmethod
    def find_by_id(tid: int) -> Optional[Topic]:
        return Topic.query.get(tid)

    @staticmethod
    def delete(tid: int) -> bool:
        t = Topic.query.get(tid)
        if not t:
            return False
        db.session.delete(t)
        db.session.commit()
        return True
