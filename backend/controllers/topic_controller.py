# backend/controllers/topic_controller.py
from flask import request, jsonify
from models import db, Question
from repositories.topic_repository import TopicRepository
from repositories.course_repository import CourseRepository
from middleware.auth_middleware import token_required, role_required
from utils.validation import require_json, get_str, get_int

topic_repo = TopicRepository()
course_repo = CourseRepository()


@token_required
@role_required(['teacher', 'admin'])
def list_topics(current_user):
    course_id = request.args.get('course_id', type=int)
    if not course_id:
        return jsonify({'error': 'course_id required'}), 400
    c = course_repo.find_by_id(int(course_id))
    if not c:
        return jsonify({'error': 'Предмет не найден'}), 404
    if current_user['role'] != 'admin' and int(c.teacher_id) != int(current_user['id']):
        return jsonify({'error': 'forbidden'}), 403
    if getattr(c, 'archived', False):
        return jsonify({'error': 'Предмет в архиве'}), 400
    rows = topic_repo.find_by_course(c.id, c.teacher_id)
    return jsonify([{'id': t.id, 'name': t.name, 'course_id': t.course_id} for t in rows]), 200


@token_required
@role_required(['teacher', 'admin'])
def create_topic(current_user):
    data = require_json(request)
    name = get_str(data, "name", required=True, min_len=1, max_len=200)
    course_id = get_int(data, "course_id", required=True, min_value=1)
    c = course_repo.find_by_id(int(course_id))
    if not c:
        return jsonify({'error': 'Предмет не найден'}), 404
    if current_user['role'] != 'admin' and int(c.teacher_id) != int(current_user['id']):
        return jsonify({'error': 'forbidden'}), 403
    if getattr(c, 'archived', False):
        return jsonify({'error': 'Предмет в архиве'}), 400
    t = topic_repo.create(name, c.teacher_id, c.id)
    return jsonify({'id': t.id, 'name': t.name, 'course_id': t.course_id}), 201


@token_required
@role_required(['teacher', 'admin'])
def delete_topic(current_user, tid):
    t = topic_repo.find_by_id(int(tid))
    if not t:
        return jsonify({'error': 'not found'}), 404
    if current_user['role'] != 'admin' and t.teacher_id != current_user['id']:
        return jsonify({'error': 'forbidden'}), 403
    Question.query.filter_by(topic_id=t.id).update({Question.topic_id: None})
    db.session.commit()
    if topic_repo.delete(t.id):
        return jsonify({'message': 'deleted'}), 200
    return jsonify({'error': 'not found'}), 404
