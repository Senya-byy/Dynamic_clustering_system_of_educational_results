# backend/repositories/group_repository.py
from typing import List, Optional

from sqlalchemy import func

from models import Group, TeacherGroup, db


class GroupRepository:
    @staticmethod
    def find_by_teacher(teacher_id: int) -> List[Group]:
        teacher_id = int(teacher_id)
        # Backward compatible: owner groups (groups.teacher_id) are implicitly attached.
        return (
            Group.query.outerjoin(TeacherGroup, TeacherGroup.group_id == Group.id)
            .filter(
                (Group.teacher_id == teacher_id)
                | (TeacherGroup.teacher_id == teacher_id)
            )
            .order_by(Group.name)
            .distinct()
            .all()
        )

    @staticmethod
    def teacher_has_group(teacher_id: int, group_id: int) -> bool:
        teacher_id = int(teacher_id)
        group_id = int(group_id)
        g = Group.query.get(group_id)
        if g and g.teacher_id is not None and int(g.teacher_id) == teacher_id:
            return True
        return (
            TeacherGroup.query.filter_by(teacher_id=teacher_id, group_id=group_id)
            .limit(1)
            .count()
            > 0
        )

    @staticmethod
    def link_teacher_group(teacher_id: int, group_id: int) -> TeacherGroup:
        row = TeacherGroup(teacher_id=int(teacher_id), group_id=int(group_id))
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def link_teacher_group_no_commit(teacher_id: int, group_id: int) -> TeacherGroup:
        """Добавляет связь в текущую транзакцию (без commit)."""
        row = TeacherGroup(teacher_id=int(teacher_id), group_id=int(group_id))
        db.session.add(row)
        return row

    @staticmethod
    def find_by_id(gid: int) -> Optional[Group]:
        return Group.query.get(gid)

    @staticmethod
    def find_all() -> List[Group]:
        return Group.query.order_by(Group.name).all()

    @staticmethod
    def find_all_ordered() -> List[Group]:
        return Group.query.order_by(func.lower(Group.name)).all()

    @staticmethod
    def find_by_name_ci(name: str) -> Optional[Group]:
        n = (name or "").strip().lower()
        if not n:
            return None
        return Group.query.filter(func.lower(Group.name) == n).first()

    @staticmethod
    def create(name: str, teacher_id: Optional[int] = None) -> Group:
        g = Group(name=name.strip(), teacher_id=teacher_id)
        db.session.add(g)
        db.session.commit()
        return g
