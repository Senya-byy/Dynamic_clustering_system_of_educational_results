# backend/controllers/question_controller.py
from flask import request, jsonify
from services.question_service import QuestionService
from middleware.auth_middleware import token_required, role_required
from utils.validation import require_json, get_str, get_int

question_service = QuestionService()


@token_required
@role_required(['teacher', 'admin'])
def create_question(current_user):
    data = require_json(request)
    # Validate, but keep payload keys for service/repo.
    get_str(data, "text", required=True, min_len=1, max_len=20_000, strip=False)
    get_int(data, "max_score", required=True, min_value=1, max_value=10_000)
    if "difficulty" in data:
        get_str(data, "difficulty", required=False, max_len=50)
    if "topic" in data:
        get_str(data, "topic", required=False, max_len=200)
    if "correct_answer" in data:
        get_str(data, "correct_answer", required=False, max_len=20_000, strip=False)

    data["created_by"] = current_user["id"]
    q = question_service.create_question(data)
    return jsonify(q), 201


@token_required
@role_required(['teacher', 'admin'])
def get_questions(current_user):
    questions = question_service.get_questions_by_teacher(current_user['id'])
    return jsonify(questions), 200


@token_required
@role_required(['teacher', 'admin'])
def get_question_by_id(current_user, qid):
    q = question_service.get_question(int(qid))
    if not q:
        return jsonify({'error': 'not found'}), 404
    if current_user['role'] != 'admin':
        from repositories.question_repository import QuestionRepository
        row = QuestionRepository.find_by_id(int(qid))
        if not row or row.created_by != current_user['id']:
            return jsonify({'error': 'forbidden'}), 403
    return jsonify(q), 200


@token_required
@role_required(['teacher', 'admin'])
def get_recommendations(current_user):
    hint = request.args.get('topic', '')
    return jsonify(question_service.get_recommendations(hint)), 200


@token_required
@role_required(['teacher', 'admin'])
def update_question(current_user, qid):
    data = require_json(request) if request.data else {}
    if current_user['role'] != 'admin':
        from repositories.question_repository import QuestionRepository
        row = QuestionRepository.find_by_id(int(qid))
        if not row or row.created_by != current_user['id']:
            return jsonify({'error': 'forbidden'}), 403
    # Validate fields if present (partial update).
    if "text" in data:
        get_str(data, "text", required=True, min_len=1, max_len=20_000, strip=False)
    if "max_score" in data:
        get_int(data, "max_score", required=True, min_value=1, max_value=10_000)
    if "difficulty" in data:
        get_str(data, "difficulty", required=False, max_len=50)
    if "topic" in data:
        get_str(data, "topic", required=False, max_len=200)
    if "correct_answer" in data:
        get_str(data, "correct_answer", required=False, max_len=20_000, strip=False)
    q = question_service.update_question(int(qid), data or {})
    return jsonify(q), 200


@token_required
@role_required(['teacher', 'admin'])
def delete_question(current_user, qid):
    if current_user['role'] != 'admin':
        from repositories.question_repository import QuestionRepository
        row = QuestionRepository.find_by_id(int(qid))
        if not row or row.created_by != current_user['id']:
            return jsonify({'error': 'forbidden'}), 403
    if question_service.delete_question(int(qid)):
        return jsonify({'message': 'deleted'}), 200
    return jsonify({'error': 'not found'}), 404
