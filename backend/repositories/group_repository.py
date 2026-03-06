# backend/repositories/group_repository.py
from models import db, Group
from typing import List, Optional


class GroupRepository:
    @staticmethod
    def find_by_teacher(teacher_id: int) -> List[Group]:
        return Group.query.filter_by(teacher_id=teacher_id).order_by(Group.name).all()

    @staticmethod
    def find_by_id(gid: int) -> Optional[Group]:
        return Group.query.get(gid)

    @staticmethod
    def find_all() -> List[Group]:
        return Group.query.order_by(Group.name).all()

    @staticmethod
    def create(name: str, teacher_id: int) -> Group:
        g = Group(name=name.strip(), teacher_id=teacher_id)
        db.session.add(g)
        db.session.commit()
        return g
