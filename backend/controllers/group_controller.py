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
        return (
            jsonify({"error": "Создание групп доступно только администратору (через админ-панель)"}),
            403,
        )

    return jsonify({"error": "Method not allowed"}), 405


@token_required
@role_required(["teacher"])
def delete_my_group(current_user, gid: int):
    return (
        jsonify({"error": "Удаление групп доступно только администратору"}),
        403,
    )
