# backend/controllers/session_controller.py
from flask import request, jsonify
from utils.lan_hosts import resolve_public_frontend_base
from services.session_service import SessionService
from repositories.group_repository import GroupRepository
from middleware.auth_middleware import token_required, role_required

session_service = SessionService()
group_repo = GroupRepository()


def _topic_ids_from_payload(payload: dict) -> list:
    ids = []
    raw_single = payload.get('topic_id')
    if raw_single is not None and raw_single != '':
        try:
            ids.append(int(raw_single))
        except (TypeError, ValueError):
            pass
    raw_list = payload.get('topic_ids')
    if isinstance(raw_list, list):
        for x in raw_list:
            try:
                ids.append(int(x))
            except (TypeError, ValueError):
                pass
    seen = set()
    out = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


@token_required
@role_required(['teacher', 'admin'])
def create_session(current_user):
    data = request.get_json() or {}
    if not data.get('group_id'):
        return jsonify({'error': 'group_id обязателен'}), 400
    gid = int(data['group_id'])
    g = group_repo.find_by_id(gid)
    if not g:
        return jsonify({'error': 'Группа не найдена'}), 404
    if current_user['role'] == 'teacher' and g.teacher_id != current_user['id']:
        return jsonify({'error': 'Можно создавать сессии только для своих групп'}), 403

    topic_ids = _topic_ids_from_payload(data)
    if topic_ids:
        if data.get('question_ids'):
            return jsonify({'error': 'Нельзя одновременно передавать topic_ids и question_ids'}), 400
        owner = g.teacher_id if current_user['role'] == 'admin' else current_user['id']
        try:
            data['question_ids'] = session_service.question_ids_from_topic_ids(topic_ids, owner)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    data.pop('topic_id', None)
    data.pop('topic_ids', None)

    if not data.get('question_id') and not data.get('question_ids'):
        return jsonify(
            {
                'error': 'Нужен один вопрос (question_id), пул по темам (topic_ids) или явный список question_ids'
            }
        ), 400
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
    fp = request.args.get('port', type=int)
    default_port = fp if fp and 1 <= fp <= 65535 else 5173
    try:
        base = resolve_public_frontend_base(
            request.headers.get('X-Frontend-Origin'),
            request.headers.get('Referer'),
            default_port=default_port,
        )
        if not base:
            base = (request.host_url or '').rstrip('/')
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
    device_id = data.get('device_id')
    if not code or not nonce:
        return jsonify({'error': 'code и nonce обязательны'}), 400
    if device_id is None or str(device_id).strip() == '':
        return jsonify({'error': 'device_id обязателен. Обновите страницу (кэш браузера).'}), 400
    try:
        payload = session_service.verify_join_ticket(
            str(code).strip(),
            str(nonce).strip(),
            current_user['id'],
            str(device_id).strip(),
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


@token_required
@role_required(['teacher', 'admin'])
def patch_session_title(current_user, sid):
    data = request.get_json() or {}
    raw = data.get('title')
    title = None if raw is None else str(raw)
    try:
        out = session_service.rename_session_title(int(sid), current_user['id'], title)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    if out is None:
        return jsonify({'error': 'Сессия не найдена'}), 404
    return jsonify(out), 200
