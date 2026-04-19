# backend/controllers/group_controller.py
from flask import jsonify
from repositories.group_repository import GroupRepository
from middleware.auth_middleware import token_required, role_required

group_repo = GroupRepository()


@token_required
@role_required(['teacher', 'admin'])
def list_my_groups(current_user):
    rows = group_repo.find_by_teacher(current_user['id'])
    return jsonify([
        {'id': g.id, 'name': g.name, 'teacher_id': g.teacher_id}
        for g in rows
    ]), 200
