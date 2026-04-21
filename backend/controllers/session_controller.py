# backend/controllers/session_controller.py
from flask import request, jsonify
from services.session_service import SessionService
from repositories.group_repository import GroupRepository
from middleware.auth_middleware import token_required, role_required

session_service = SessionService()
group_repo = GroupRepository()


@token_required
@role_required(['teacher', 'admin'])
def create_session(current_user):
    data = request.get_json() or {}
    if not data.get('group_id'):
        return jsonify({'error': 'group_id обязателен'}), 400
    if not data.get('question_id') and not data.get('question_ids'):
        return jsonify({'error': 'Нужен question_id или question_ids (пул)'}), 400
    gid = int(data['group_id'])
    g = group_repo.find_by_id(gid)
    if not g:
        return jsonify({'error': 'Группа не найдена'}), 404
    if current_user['role'] == 'teacher' and g.teacher_id != current_user['id']:
        return jsonify({'error': 'Можно создавать сессии только для своих групп'}), 403
    data['created_by'] = current_user['id']
    if data.get('question_ids'):
        data.pop('question_id', None)
    try:
        sess = session_service.create_session(data)
        return jsonify(sess), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@token_required
def get_session_by_code(current_user, code):
    if current_user['role'] not in ('teacher', 'admin'):
        return jsonify({'error': 'Используйте вход по QR (verify-ticket)'}), 403
    sess = session_service.get_session_by_code(code, current_user['role'])
    if not sess:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(sess), 200


@token_required
@role_required(['teacher', 'admin'])
def get_live_qr(current_user, sid):
    try:
        base = request.headers.get('X-Frontend-Origin') or request.host_url or ''
        out = session_service.issue_live_qr(
            int(sid), current_user['id'], base.rstrip('/')
        )
        return jsonify(out), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@token_required
@role_required(['student'])
def verify_join_ticket(current_user):
    data = request.get_json() or {}
    code, nonce = data.get('code'), data.get('nonce')
    if not code or not nonce:
        return jsonify({'error': 'code и nonce обязательны'}), 400
    try:
        payload = session_service.verify_join_ticket(
            str(code).strip(), str(nonce).strip(), current_user['id']
        )
        return jsonify(payload), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@token_required
@role_required(['teacher', 'admin'])
def list_teacher_sessions(current_user):
    data = session_service.list_for_teacher(current_user['id'])
    return jsonify(data), 200


@token_required
@role_required(['teacher', 'admin'])
def close_session(current_user, sid):
    if session_service.close_session(int(sid), current_user['id']):
        return jsonify({'message': 'closed'}), 200
    return jsonify({'error': 'not found'}), 404
