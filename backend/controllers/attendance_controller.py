# backend/controllers/attendance_controller.py
from flask import request, jsonify
from services.answer_service import AnswerService
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository
from repositories.course_repository import CourseRepository
from middleware.auth_middleware import token_required, role_required
from models import Group, Attendance

session_repo = SessionRepository()
user_repo = UserRepository()
group_repo = GroupRepository()
course_repo = CourseRepository()
answer_service = AnswerService()


@token_required
@role_required(['teacher', 'admin'])
def get_group_stats(current_user):
    group_id = request.args.get('group_id', type=int)
    if not group_id:
        return jsonify({'error': 'group_id required'}), 400
    course_id = request.args.get('course_id', type=int)
    if not course_id:
        return jsonify({'error': 'course_id required'}), 400
    group = Group.query.get(group_id)
    if not group:
        return jsonify({'error': 'not found'}), 404
    c = course_repo.find_by_id(int(course_id))
    if not c:
        return jsonify({'error': 'course not found'}), 404
    if getattr(c, 'archived', False):
        return jsonify({'error': 'Предмет в архиве'}), 400
    if current_user['role'] != 'admin' and int(c.teacher_id) != int(current_user['id']):
        return jsonify({'error': 'access denied'}), 403

    students = user_repo.find_by_group(group_id)
    sessions = [s for s in session_repo.find_by_group(group_id) if int(getattr(s, 'course_id', 0) or 0) == int(course_id)]
    stats = []
    for student in students:
        answers = answer_service.get_student_answers_with_feedback(student.id)
        total_score = sum(
            a.get('score', 0) or 0 for a in answers if a.get('score') is not None
        )
        att_rows = Attendance.query.filter_by(student_id=student.id).all()
        att_by_session = {a.session_id: a.status for a in att_rows}
        session_marks = []
        for sess in sessions:
            session_marks.append({
                'session_id': sess.id,
                'code': sess.code,
                'status': att_by_session.get(sess.id, 'absent'),
            })
        stats.append({
            'student_id': student.id,
            'name': student.full_name or student.login,
            'total_score': total_score,
            'answers_count': len(answers),
            'attendance_records': len(att_rows),
            'sessions': session_marks,
        })
    return jsonify(stats), 200
