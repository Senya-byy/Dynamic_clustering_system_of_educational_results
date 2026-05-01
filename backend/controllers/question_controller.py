# backend/controllers/question_controller.py
from flask import request, jsonify
from models import Topic
from services.question_service import QuestionService
from middleware.auth_middleware import token_required, role_required
from utils.validation import require_json, get_str, get_int, get_trimmed_nonblank_str

question_service = QuestionService()

_ALLOWED_DIFFICULTY = frozenset({"easy", "medium", "hard"})


def _assert_topic_access(topic_id: int, current_user: dict) -> None:
    t = Topic.query.get(topic_id)
    if not t:
        raise ValueError("Тема из каталога не найдена")
    if current_user["role"] != "admin" and t.teacher_id != current_user["id"]:
        raise ValueError("Тема не из вашего каталога")


@token_required
@role_required(['teacher', 'admin'])
def create_question(current_user):
    data = require_json(request)
    data["text"] = get_trimmed_nonblank_str(
        data, "text", required=True, max_len=20_000
    )
    data["correct_answer"] = get_trimmed_nonblank_str(
        data, "correct_answer", required=True, max_len=20_000
    )
    get_int(data, "max_score", required=True, min_value=1, max_value=10_000)

    raw_diff = data.get("difficulty")
    if raw_diff is None or raw_diff == "":
        data["difficulty"] = "medium"
    else:
        d = str(raw_diff).strip().lower()
        if d not in _ALLOWED_DIFFICULTY:
            raise ValueError("Сложность: easy, medium или hard")
        data["difficulty"] = d

    topic_id = get_int(data, "topic_id", required=False, min_value=1)
    topic_free = get_str(data, "topic", required=False, max_len=100)
    if topic_id:
        _assert_topic_access(topic_id, current_user)
        data["topic_id"] = topic_id
    else:
        data.pop("topic_id", None)
    if topic_free:
        data["topic"] = topic_free
    else:
        data.pop("topic", None)

    if not topic_id and not topic_free:
        raise ValueError("Укажите тему из каталога или краткое название темы (поле «Тема (текст)»)")

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
        data["text"] = get_trimmed_nonblank_str(
            data, "text", required=True, max_len=20_000
        )
    if "max_score" in data:
        get_int(data, "max_score", required=True, min_value=1, max_value=10_000)
    if "difficulty" in data:
        raw_diff = data.get("difficulty")
        if raw_diff is None or raw_diff == "":
            data["difficulty"] = None
        else:
            d = str(raw_diff).strip().lower()
            if d not in _ALLOWED_DIFFICULTY:
                raise ValueError("Сложность: easy, medium или hard")
            data["difficulty"] = d
    if "topic" in data:
        topic_free = get_str(data, "topic", required=False, max_len=100)
        data["topic"] = topic_free if topic_free else None
    if "topic_id" in data:
        tid = data.get("topic_id")
        if tid is None or tid == "":
            data["topic_id"] = None
        else:
            topic_id = int(tid)
            _assert_topic_access(topic_id, current_user)
            data["topic_id"] = topic_id
    if "correct_answer" in data:
        data["correct_answer"] = get_trimmed_nonblank_str(
            data, "correct_answer", required=True, max_len=20_000
        )
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
