# backend/controllers/session_controller.py
from flask import request, jsonify
from utils.lan_hosts import resolve_public_frontend_base
from services.session_service import SessionService
from repositories.group_repository import GroupRepository
from repositories.course_repository import CourseRepository
from repositories.question_repository import QuestionRepository
from middleware.auth_middleware import token_required, role_required
from utils.validation import require_json, get_int, get_str, get_trimmed_nonblank_str

session_service = SessionService()
group_repo = GroupRepository()
course_repo = CourseRepository()
question_repo = QuestionRepository()


@token_required
@role_required(['teacher', 'admin'])
def create_session(current_user):
    data = require_json(request)
    course_id = get_int(data, "course_id", required=False, min_value=1)
    c = None
    if course_id:
        c = course_repo.find_by_id(int(course_id))
        if not c:
            return jsonify({'error': 'Предмет не найден'}), 404
        if current_user['role'] != 'admin' and int(c.teacher_id) != int(current_user['id']):
            return jsonify({'error': 'Нет доступа к предмету'}), 403
        if getattr(c, 'archived', False):
            return jsonify({'error': 'Предмет в архиве'}), 400

    # Legacy: group_id -> group_ids=[group_id]
    group_ids = data.get("group_ids")
    if group_ids is None:
        gid = get_int(data, "group_id", required=True, min_value=1)
        group_ids = [gid]
    if not isinstance(group_ids, list) or not group_ids:
        return jsonify({'error': 'group_ids должен быть непустым массивом'}), 400
    try:
        group_ids = [int(x) for x in group_ids if x is not None and x != ""]
    except (TypeError, ValueError):
        return jsonify({'error': 'group_ids должен содержать только числа'}), 400
    group_ids = [gid for gid in group_ids if gid > 0]
    if not group_ids:
        return jsonify({'error': 'group_ids должен быть непустым массивом'}), 400
    # Уникализируем, сохраняя порядок.
    seen = set()
    uniq_group_ids = []
    for gid in group_ids:
        if gid in seen:
            continue
        seen.add(gid)
        uniq_group_ids.append(gid)
    group_ids = uniq_group_ids

    # Группы должны существовать, а преподаватель должен быть к ним привязан.
    allowed_course_groups = set(course_repo.list_group_ids(c.id)) if c else set()
    for gid in group_ids:
        g = group_repo.find_by_id(gid)
        if not g:
            return jsonify({'error': f'Группа {gid} не найдена'}), 404
        if current_user['role'] == 'teacher' and not group_repo.teacher_has_group(current_user['id'], gid):
            return jsonify({'error': 'Можно создавать сессии только для своих групп'}), 403
        if allowed_course_groups and int(gid) not in allowed_course_groups:
            return jsonify({'error': 'Группа не привязана к выбранному предмету'}), 400

    # Simplified UX: only one fixed question per session.
    if data.get('topic_id') or data.get('topic_ids') or data.get('question_ids'):
        return jsonify({'error': 'Пулы и темы отключены. Передайте только question_id.'}), 400
    qid = get_int(data, 'question_id', required=True, min_value=1)

    # Backward compatible: infer course_id from question_id for legacy clients/tests.
    qrow = question_repo.find_by_id(int(qid))
    if not qrow:
        return jsonify({'error': 'Вопрос не найден'}), 404
    if not c and qrow and getattr(qrow, 'course_id', None):
        c = course_repo.find_by_id(int(qrow.course_id))
        if qrow and getattr(qrow, 'course_id', None):
            c = course_repo.find_by_id(int(qrow.course_id))
            if c and current_user['role'] != 'admin' and int(c.teacher_id) != int(current_user['id']):
                return jsonify({'error': 'Нет доступа к предмету'}), 403
    if c and getattr(c, 'archived', False):
        return jsonify({'error': 'Предмет в архиве'}), 400
    if c and getattr(qrow, 'course_id', None) and int(qrow.course_id) != int(c.id):
        return jsonify({'error': 'Вопрос не из выбранного предмета'}), 400

    data['group_ids'] = group_ids
    if c:
        data['course_id'] = int(c.id)
    data['created_by'] = current_user['id']
    # Validate optional fields early (keep keys/shape for service).
    if "timer_seconds" in data and data.get("timer_seconds") not in (None, ""):
        get_int(data, "timer_seconds", required=False, min_value=1, max_value=24 * 60 * 60)
    if "title" in data:
        raw_title = data.get("title")
        if raw_title is not None:
            get_str(data, "title", required=False, max_len=250, strip=False)

    sess = session_service.create_session(data)
    return jsonify(sess), 201


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
@role_required(['teacher', 'admin'])
def freeze_live_qr(current_user, sid):
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
        out = session_service.freeze_live_qr(
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
    data = require_json(request)
    code = get_str(data, "code", required=True, min_len=1, max_len=32)
    nonce = get_str(data, "nonce", required=True, min_len=1, max_len=128)
    device_id = get_str(
        data,
        "device_id",
        required=True,
        min_len=1,
        max_len=256,
    )

    payload = session_service.verify_join_ticket(
        code,
        nonce,
        current_user["id"],
        device_id,
    )
    return jsonify(payload), 200


@token_required
@role_required(['student'])
def verify_session_pin(current_user):
    data = require_json(request)
    code = get_trimmed_nonblank_str(data, 'code', required=True, max_len=32)
    join_pin = get_trimmed_nonblank_str(data, 'join_pin', required=True, max_len=12)
    device_id = get_str(
        data,
        'device_id',
        required=True,
        min_len=1,
        max_len=256,
    )
    payload = session_service.verify_session_pin(
        code,
        join_pin,
        current_user['id'],
        device_id,
    )
    return jsonify(payload), 200


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
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Ожидается JSON-объект'}), 400
    if 'title' not in data:
        return jsonify({'error': 'Передайте поле title (строка, пустая строка или null — сброс к названию по умолчанию)'}), 400
    raw = data.get('title')
    if raw is None:
        title = None
    else:
        s = str(raw).strip()
        title = None if not s else s[:250]
    try:
        out = session_service.rename_session_title(int(sid), current_user['id'], title)
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    if out is None:
        return jsonify({'error': 'Сессия не найдена'}), 404
    return jsonify(out), 200
