# backend/controllers/register_controller.py
from flask import Blueprint, jsonify, request

from services.registration_service import RegistrationService
from utils.validation import get_int, get_trimmed_nonblank_str, require_json

register_bp = Blueprint("register", __name__)
_registration = RegistrationService()


@register_bp.route("/groups", methods=["GET"])
def register_list_groups():
    return jsonify(_registration.list_groups_public()), 200


@register_bp.route("/student", methods=["POST"])
def register_student():
    try:
        data = require_json(request)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        login = get_trimmed_nonblank_str(data, "login", required=True, max_len=80)
        password = data.get("password")
        full_name = get_trimmed_nonblank_str(data, "full_name", required=True, max_len=200)
        group_id = get_int(data, "group_id", required=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        out = _registration.register_student(login, password, full_name, group_id)
        return jsonify(out), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@register_bp.route("/teacher", methods=["POST"])
def register_teacher():
    try:
        data = require_json(request)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        login = get_trimmed_nonblank_str(data, "login", required=True, max_len=80)
        password = data.get("password")
        full_name = get_trimmed_nonblank_str(data, "full_name", required=True, max_len=200)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    raw_ids = data.get("group_ids")
    if raw_ids is None:
        raw_ids = []
    raw_names = data.get("new_group_names")
    if raw_names is None:
        raw_names = []
    try:
        if raw_names:
            return jsonify({"error": "Новые группы может добавлять только администратор"}), 400
        out = _registration.register_teacher(login, password, full_name, raw_ids, raw_names)
        return jsonify(out), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
