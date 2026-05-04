from flask import jsonify, request

from middleware.auth_middleware import role_required, token_required
from repositories.group_repository import GroupRepository

group_repo = GroupRepository()


@token_required
@role_required(["teacher"])
def attach_group_to_me(current_user):
    data = request.get_json() or {}
    try:
        gid = int(data.get("group_id") or 0)
    except (TypeError, ValueError):
        gid = 0
    if gid <= 0:
        return jsonify({"error": "Передайте group_id (целое число)"}), 400

    g = group_repo.find_by_id(gid)
    if not g:
        return jsonify({"error": "Группа не найдена"}), 404

    if group_repo.teacher_has_group(current_user["id"], gid):
        return jsonify({"message": "already_attached"}), 200

    group_repo.link_teacher_group(current_user["id"], gid)
    return jsonify({"message": "attached"}), 201

