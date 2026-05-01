# backend/controllers/schedule_controller.py
from flask import request, jsonify
from services.schedule_service import ScheduleService
from middleware.auth_middleware import token_required, role_required

schedule_service = ScheduleService()


@token_required
def get_schedule(current_user, group_id):
    try:
        rows = schedule_service.get_schedule(
            int(group_id), current_user['id'], current_user['role']
        )
        return jsonify(rows), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403


@token_required
def get_current_slot(current_user, group_id):
    try:
        row = schedule_service.current_slot(
            int(group_id), current_user['id'], current_user['role']
        )
        return jsonify(row), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403


@token_required
@role_required(['teacher', 'admin'])
def post_schedule(current_user):
    data = request.get_json() or {}
    try:
        row = schedule_service.create_slot(data, current_user['id'], current_user['role'])
        return jsonify(row), 201
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except KeyError as e:
        return jsonify({'error': f'missing field {e}'}), 400


@token_required
@role_required(['teacher', 'admin'])
def schedule_slot(current_user, sid):
    if request.method == 'DELETE':
        try:
            if schedule_service.delete_slot(
                int(sid), current_user['id'], current_user['role']
            ):
                return jsonify({'message': 'deleted'}), 200
            return jsonify({'error': 'not found'}), 404
        except PermissionError as e:
            return jsonify({'error': str(e)}), 403
    data = request.get_json() or {}
    try:
        row = schedule_service.update_slot(
            int(sid), data, current_user['id'], current_user['role']
        )
        if not row:
            return jsonify({'error': 'not found'}), 404
        return jsonify(row), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
