from flask import jsonify

from middleware.auth_middleware import token_required, role_required
from models import Course, CourseGroup
from repositories.user_repository import UserRepository

users = UserRepository()


@token_required
@role_required(["student"])
def my_courses(current_user):
    u = users.find_by_id(current_user["id"])
    if not u or not u.group_id:
        return jsonify([]), 200
    rows = (
        Course.query.join(CourseGroup, CourseGroup.course_id == Course.id)
        .filter(
            CourseGroup.group_id == int(u.group_id),
            Course.archived.is_(False),
        )
        .order_by(Course.name)
        .all()
    )
    return jsonify([{"id": c.id, "name": c.name, "teacher_id": c.teacher_id} for c in rows]), 200

