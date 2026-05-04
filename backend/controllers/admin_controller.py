# backend/controllers/admin_controller.py
import os

from flask import abort, request, jsonify
from services.admin_service import AdminService
from middleware.auth_middleware import token_required, role_required
from utils.validation import require_json, get_str

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


@token_required
@role_required(['admin'])
def admin_delete_user(current_user, uid):
    try:
        admin_service.delete_user(current_user['id'], int(uid))
        return jsonify({'message': 'deleted'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@token_required
@role_required(['admin'])
def admin_delete_group(current_user, gid):
    if admin_service.delete_group(int(gid)):
        return jsonify({'message': 'deleted'}), 200
    return jsonify({'error': 'Группа не найдена'}), 404


@token_required
@role_required(['admin'])
def admin_patch_group_status(current_user, gid):
    data = request.get_json() or {}
    try:
        status = get_str(data, 'status', required=True, min_len=1, max_len=20)
        row = admin_service.set_group_status(int(gid), status)
        return jsonify(row), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


def bootstrap_admin():
    """
    One-time admin bootstrap for hosted environments without shell access.

    Enabled only when BOOTSTRAP_TOKEN env var is set.
    Requires header: X-Bootstrap-Token: <token>
    """
    token = os.environ.get("BOOTSTRAP_TOKEN")
    if not token:
        abort(404)
    provided = (request.headers.get("X-Bootstrap-Token") or "").strip()
    if provided != token:
        return jsonify({"error": "forbidden"}), 403

    data = require_json(request)
    login = get_str(data, "login", required=True, min_len=1, max_len=80)
    password = get_str(data, "password", required=True, min_len=4, max_len=200, strip=False)
    full_name = get_str(data, "full_name", required=False, max_len=200, strip=False)

    row = admin_service.bootstrap_admin(login, password, full_name=full_name)
    return jsonify(row), 201
