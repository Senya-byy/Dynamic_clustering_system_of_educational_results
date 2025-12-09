# backend/controllers/topic_controller.py
from flask import request, jsonify
from models import db, Question
from repositories.topic_repository import TopicRepository
from middleware.auth_middleware import token_required, role_required

topic_repo = TopicRepository()


@token_required
@role_required(['teacher', 'admin'])
def list_topics(current_user):
    rows = topic_repo.find_by_teacher(current_user['id'])
    return jsonify([{'id': t.id, 'name': t.name} for t in rows]), 200


@token_required
@role_required(['teacher', 'admin'])
def create_topic(current_user):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    t = topic_repo.create(name, current_user['id'])
    return jsonify({'id': t.id, 'name': t.name}), 201


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
