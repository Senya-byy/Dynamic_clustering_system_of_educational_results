from flask import jsonify, request

from middleware.auth_middleware import token_required, role_required
from repositories.course_repository import CourseRepository
from repositories.group_repository import GroupRepository

courses = CourseRepository()
groups = GroupRepository()


def _parse_include_archived(default: bool) -> bool:
    raw = request.args.get("include_archived")
    if raw is None or raw == "":
        return default
    return str(raw).lower() in ("1", "true", "yes", "on")


@token_required
@role_required(["teacher", "admin"])
def list_courses(current_user):
    if current_user["role"] == "admin":
        # Admin: allow listing by teacher_id for support tools.
        tid = request.args.get("teacher_id", type=int)
        if not tid:
            return jsonify({"error": "teacher_id required for admin"}), 400
        rows = courses.list_for_teacher(tid, include_archived=_parse_include_archived(default=True))
    else:
        # По умолчанию без архива (сессии, аналитика, кластеризация). Страница «Предметы»: ?include_archived=1
        rows = courses.list_for_teacher(
            current_user["id"], include_archived=_parse_include_archived(default=False)
        )
    return (
        jsonify(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "teacher_id": c.teacher_id,
                    "archived": bool(getattr(c, "archived", False)),
                }
                for c in rows
            ]
        ),
        200,
    )


@token_required
@role_required(["teacher"])
def create_course(current_user):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Укажите название предмета"}), 400
    if len(name) > 200:
        return jsonify({"error": "Название предмета слишком длинное"}), 400
    c = courses.create(current_user["id"], name)
    return jsonify({"id": c.id, "name": c.name, "archived": bool(c.archived)}), 201


@token_required
@role_required(["teacher"])
def patch_course(current_user, cid: int):
    c = courses.find_by_id(int(cid))
    if not c or int(c.teacher_id) != int(current_user["id"]):
        return jsonify({"error": "not found"}), 404
    data = request.get_json() or {}
    out = {}
    if "name" in data:
        name = str(data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name cannot be empty"}), 400
        if len(name) > 200:
            return jsonify({"error": "Название предмета слишком длинное"}), 400
        out["name"] = name
    if "archived" in data:
        out["archived"] = bool(data.get("archived"))
    if not out:
        return jsonify({"error": "no fields to update"}), 400
    updated = courses.update(c.id, out)
    return jsonify({"id": updated.id, "name": updated.name, "archived": bool(updated.archived)}), 200


@token_required
@role_required(["teacher"])
def get_course_groups(current_user, cid: int):
    c = courses.find_by_id(int(cid))
    if not c or int(c.teacher_id) != int(current_user["id"]):
        return jsonify({"error": "not found"}), 404
    gids = set(courses.list_group_ids(c.id))
    # Provide full group list for this course (only groups teacher has access to).
    allowed_groups = groups.find_by_teacher(current_user["id"])
    items = []
    for g in allowed_groups:
        items.append(
            {
                "id": g.id,
                "name": g.name,
                "selected": int(g.id) in gids,
            }
        )
    return jsonify({"course_id": c.id, "groups": items}), 200


@token_required
@role_required(["teacher"])
def put_course_groups(current_user, cid: int):
    c = courses.find_by_id(int(cid))
    if not c or int(c.teacher_id) != int(current_user["id"]):
        return jsonify({"error": "not found"}), 404
    data = request.get_json() or {}
    raw = data.get("group_ids")
    if not isinstance(raw, list):
        return jsonify({"error": "group_ids must be a list"}), 400
    try:
        gids = [int(x) for x in raw if x is not None and x != ""]
    except (TypeError, ValueError):
        return jsonify({"error": "group_ids must contain only integers"}), 400
    gids = [x for x in gids if x > 0]
    # Teacher can only attach groups they have access to.
    allowed = {int(g.id) for g in groups.find_by_teacher(current_user["id"])}
    for gid in gids:
        if gid not in allowed:
            return jsonify({"error": "Можно привязать только свои группы"}), 403
    # Uniq
    seen = set()
    uniq = []
    for gid in gids:
        if gid in seen:
            continue
        seen.add(gid)
        uniq.append(gid)
    courses.replace_groups(c.id, uniq)
    return jsonify({"message": "saved", "course_id": c.id, "group_ids": uniq}), 200

