# backend/controllers/group_controller.py
from flask import jsonify, request

from middleware.auth_middleware import role_required, token_required
from repositories.group_repository import GroupRepository
from services.admin_service import AdminService

group_repo = GroupRepository()
_admin = AdminService()


@token_required
@role_required(["teacher", "admin"])
def groups_endpoint(current_user):
    if request.method == "GET":
        rows = group_repo.find_by_teacher(current_user["id"])
        return (
            jsonify(
                [
                    {"id": g.id, "name": g.name, "teacher_id": g.teacher_id}
                    for g in rows
                ]
            ),
            200,
        )

    if request.method == "POST":
        if current_user.get("role") != "teacher":
            return jsonify({"error": "Создание группы доступно только преподавателю"}), 403
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Укажите название группы"}), 400
        if group_repo.find_by_name_ci(name):
            return jsonify({"error": "Группа с таким названием уже есть"}), 400
        g = group_repo.create(name, current_user["id"])
        return jsonify({"id": g.id, "name": g.name, "teacher_id": g.teacher_id}), 201

    return jsonify({"error": "Method not allowed"}), 405


@token_required
@role_required(["teacher"])
def delete_my_group(current_user, gid: int):
    try:
        ok = _admin.delete_teacher_own_group(current_user["id"], int(gid))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if not ok:
        return jsonify({"error": "Группа не найдена"}), 404
    return jsonify({"message": "deleted"}), 200
