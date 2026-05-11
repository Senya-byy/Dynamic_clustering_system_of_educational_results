# backend/controllers/rating_controller.py
from flask import request, jsonify
from services.rating_service import RatingService
from repositories.group_repository import GroupRepository
from repositories.user_repository import UserRepository
from repositories.course_repository import CourseRepository
from middleware.auth_middleware import token_required

rating_service = RatingService()
user_repo = UserRepository()
group_repo = GroupRepository()
course_repo = CourseRepository()


@token_required
def get_group_rating(current_user):
    group_id = request.args.get('group_id', type=int)
    if not group_id:
        return jsonify({'error': 'group_id required'}), 400
    course_id = request.args.get('course_id', type=int)
    user = user_repo.find_by_id(current_user['id'])
    role = current_user['role']
    is_teacher = role == 'teacher'
    if role == 'student':
        if not user or user.group_id != group_id:
            return jsonify({'error': 'access denied'}), 403
    elif role == 'teacher':
        g = group_repo.find_by_id(group_id)
        if not g or not group_repo.teacher_has_group(current_user['id'], group_id):
            return jsonify({'error': 'access denied'}), 403
    elif role == 'admin':
        pass
    else:
        return jsonify({'error': 'access denied'}), 403

    if course_id:
        c = course_repo.find_by_id(int(course_id))
        if not c:
            return jsonify({'error': 'course not found'}), 404
        if getattr(c, 'archived', False):
            return jsonify({'error': 'Предмет в архиве'}), 400
        if role != 'admin' and int(c.teacher_id) != int(current_user['id']) and role != 'student':
            return jsonify({'error': 'access denied'}), 403

    can_see_names = is_teacher or role == 'admin'
    rating = rating_service.get_group_rating(
        group_id, current_user['id'], can_see_names, course_id=course_id
    )
    return jsonify(rating), 200
