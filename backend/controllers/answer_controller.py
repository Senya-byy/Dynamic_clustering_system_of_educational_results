# backend/controllers/answer_controller.py
from flask import request, jsonify
from services.answer_service import AnswerService
from middleware.auth_middleware import token_required, role_required

answer_service = AnswerService()


@token_required
@role_required(['student'])
def my_answers(current_user):
    rows = answer_service.get_student_answers_with_feedback(current_user['id'])
    return jsonify(rows), 200


@token_required
@role_required(['student'])
def submit_answer(current_user):
    data = request.get_json()
    if not data.get('session_code') or not data.get('text'):
        return jsonify({'error': 'session_code and text required'}), 400
    try:
        res = answer_service.submit_answer(
            current_user['id'], data['session_code'], data['text']
        )
        return jsonify(res), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 403


@token_required
@role_required(['teacher', 'admin'])
def grade_answer(current_user, aid):
    data = request.get_json()
    if 'score' not in data:
        return jsonify({'error': 'score required'}), 400
    score = data['score']
    comment = data.get('comment', '')
    is_correct = data.get('is_correct')
    if is_correct is not None:
        is_correct = bool(is_correct)
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
