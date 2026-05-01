# backend/controllers/answer_controller.py
from flask import request, jsonify
from services.answer_service import AnswerService
from middleware.auth_middleware import token_required, role_required
from utils.validation import require_json, get_str, get_int, get_bool, get_trimmed_nonblank_str

answer_service = AnswerService()


@token_required
@role_required(['student'])
def my_answers(current_user):
    rows = answer_service.get_student_answers_with_feedback(current_user['id'])
    return jsonify(rows), 200


@token_required
@role_required(['student'])
def submit_answer(current_user):
    data = require_json(request)
    session_code = get_str(data, "session_code", required=True, min_len=1, max_len=32)
    text = get_trimmed_nonblank_str(data, "text", required=True, max_len=10000)
    device_id = get_str(
        data,
        "device_id",
        required=True,
        min_len=1,
        max_len=256,
    )

    res = answer_service.submit_answer(
        current_user["id"],
        session_code,
        text,
        device_id,
    )
    return jsonify(res), 201


@token_required
@role_required(['teacher', 'admin'])
def grade_answer(current_user, aid):
    data = require_json(request)
    score = get_int(data, "score", required=True, min_value=0, max_value=10_000)
    comment = get_str(data, "comment", required=False, max_len=10_000, strip=False) or ""
    is_correct = get_bool(data, "is_correct")
    res = answer_service.grade_answer(
        int(aid), score, comment, current_user['id'], is_correct=is_correct
    )
    return jsonify(res), 200


@token_required
@role_required(['teacher', 'admin'])
def get_session_answers(current_user, sid):
    try:
        answers = answer_service.get_answers_for_session(
            int(sid), current_user['id']
        )
        return jsonify(answers), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
