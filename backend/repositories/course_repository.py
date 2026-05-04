from typing import List, Optional

from models import Course, CourseGroup, db


class CourseRepository:
    @staticmethod
    def list_for_teacher(teacher_id: int, include_archived: bool = False) -> List[Course]:
        q = Course.query.filter_by(teacher_id=int(teacher_id))
        if not include_archived:
            q = q.filter(Course.archived.is_(False))
        return q.order_by(Course.name).all()

    @staticmethod
    def find_by_id(course_id: int) -> Optional[Course]:
        return Course.query.get(int(course_id))

    @staticmethod
    def create(teacher_id: int, name: str) -> Course:
        row = Course(teacher_id=int(teacher_id), name=str(name).strip(), archived=False)
        db.session.add(row)
        db.session.commit()
        return row

    @staticmethod
    def update(course_id: int, data: dict) -> Optional[Course]:
        c = Course.query.get(int(course_id))
        if not c:
            return None
        for k, v in dict(data).items():
            setattr(c, k, v)
        db.session.commit()
        return c

    @staticmethod
    def list_group_ids(course_id: int) -> List[int]:
        rows = CourseGroup.query.filter_by(course_id=int(course_id)).all()
        return [int(r.group_id) for r in rows]

    @staticmethod
    def replace_groups(course_id: int, group_ids: List[int]) -> None:
        cid = int(course_id)
        CourseGroup.query.filter_by(course_id=cid).delete()
        for gid in [int(x) for x in group_ids]:
            db.session.add(CourseGroup(course_id=cid, group_id=int(gid)))
        db.session.commit()

