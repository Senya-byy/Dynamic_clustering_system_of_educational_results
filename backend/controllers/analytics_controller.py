# backend/controllers/analytics_controller.py
from flask import request, jsonify
from services.analytics_service import AnalyticsService
from middleware.auth_middleware import token_required, role_required

analytics_service = AnalyticsService()


@token_required
@role_required(['teacher', 'admin'])
def get_group_stat(current_user):
    gid = request.args.get('group_id', type=int)
    if not gid:
        return jsonify({'error': 'group_id required'}), 400
    try:
        data = analytics_service.get_group_stat(
            gid, current_user['id'], current_user['role']
        )
        return jsonify(data), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403


@token_required
def get_student_stat(current_user, student_id):
    try:
        data = analytics_service.get_student_stat(
            int(student_id), current_user['id'], current_user['role']
        )
        return jsonify(data), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
