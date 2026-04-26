# backend/controllers/admin_controller.py
from flask import request, jsonify
from services.admin_service import AdminService
from middleware.auth_middleware import token_required, role_required

admin_service = AdminService()


@token_required
@role_required(['admin'])
def admin_list_users(current_user):
    return jsonify(admin_service.list_users()), 200


@token_required
@role_required(['admin'])
def admin_create_user(current_user):
    data = request.get_json() or {}
    try:
        row = admin_service.create_user(
            data.get('login', ''),
            data.get('password', ''),
            data.get('role', ''),
            data.get('full_name'),
            data.get('group_id'),
        )
        return jsonify(row), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@token_required
@role_required(['admin'])
def admin_list_groups(current_user):
    return jsonify(admin_service.list_groups()), 200


@token_required
@role_required(['admin'])
def admin_create_group(current_user):
    data = request.get_json() or {}
    tid = data.get('teacher_id')
    if tid is None:
        return jsonify({'error': 'teacher_id обязателен'}), 400
    try:
        row = admin_service.create_group(data.get('name', ''), int(tid))
        return jsonify(row), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@token_required
@role_required(['admin'])
def admin_list_teachers(current_user):
    from repositories.user_repository import UserRepository
    teachers = UserRepository.find_by_role('teacher')
    return jsonify([
        {'id': u.id, 'login': u.login, 'full_name': u.full_name}
        for u in teachers
    ]), 200
