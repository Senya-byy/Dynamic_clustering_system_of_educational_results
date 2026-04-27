# backend/app.py
import os
from flask import Flask
from sqlalchemy.exc import OperationalError
from config import Config
from models import db


def seed_data():
    from models import User, Group, Topic, Question

    if User.query.filter_by(login='teacher').first():
        return

    teacher = User(
        login='teacher',
        role='teacher',
        full_name='Преподаватель Иванов',
        group_id=None,
    )
    teacher.set_password('teacher123')

    admin = User(
        login='admin',
        role='admin',
        full_name='Администратор',
        group_id=None,
    )
    admin.set_password('admin123')

    student = User(
        login='student',
        role='student',
        full_name='Студент Петров',
        group_id=None,
    )
    student.set_password('student123')

    db.session.add_all([teacher, admin, student])
    db.session.commit()

    grp = Group(name='ИТ-251', teacher_id=teacher.id)
    db.session.add(grp)
    db.session.commit()

    student.group_id = grp.id
    db.session.commit()

    topic = Topic(name='Технологии разработки ПО', teacher_id=teacher.id)
    db.session.add(topic)
    db.session.commit()

    q1 = Question(
        text='Опишите принципы SOLID и приведите пример.',
        topic='Технологии разработки ПО',
        topic_id=topic.id,
        difficulty='medium',
        max_score=5,
        correct_answer='SRP, OCP, LSP, ISP, DIP с краткими определениями.',
        created_by=teacher.id,
    )
    q2 = Question(
        text='Чем REST отличается от SOAP?',
        topic='Технологии разработки ПО',
        topic_id=topic.id,
        difficulty='easy',
        max_score=3,
        correct_answer='Стиль, ресурсы, HTTP-методы, обычно JSON против XML-RPC.',
        created_by=teacher.id,
    )
    db.session.add_all([q1, q2])
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    from flask_cors import CORS

    origins = os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173',
    ).split(',')
    CORS(
        app,
        origins=[o.strip() for o in origins if o.strip()],
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'X-Frontend-Origin'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()
        try:
            seed_data()
        except OperationalError:
            db.drop_all()
            db.create_all()
            seed_data()

    from controllers.auth_controller import auth_bp
    from controllers.question_controller import (
        create_question,
        get_questions,
        get_question_by_id,
        get_recommendations,
        update_question,
        delete_question,
    )
    from controllers.session_controller import (
        create_session,
        get_session_by_code,
        get_live_qr,
        verify_join_ticket,
        list_teacher_sessions,
        close_session,
    )
    from controllers.answer_controller import (
        my_answers,
        submit_answer,
        grade_answer,
        get_session_answers,
    )
    from controllers.rating_controller import get_group_rating
    from controllers.attendance_controller import get_group_stats
    from controllers.group_controller import list_my_groups
    from controllers.analytics_controller import get_group_stat, get_student_stat
    from controllers.schedule_controller import (
        get_schedule,
        get_current_slot,
        post_schedule,
        schedule_slot,
    )
    from controllers.import_controller import post_import_schedule
    from controllers.topic_controller import list_topics, create_topic
    from controllers.admin_controller import (
        admin_list_users,
        admin_create_user,
        admin_list_groups,
        admin_create_group,
        admin_list_teachers,
    )

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    app.add_url_rule('/api/admin/users', view_func=admin_list_users, methods=['GET'])
    app.add_url_rule('/api/admin/users', view_func=admin_create_user, methods=['POST'])
    app.add_url_rule('/api/admin/groups', view_func=admin_list_groups, methods=['GET'])
    app.add_url_rule('/api/admin/groups', view_func=admin_create_group, methods=['POST'])
    app.add_url_rule('/api/admin/teachers', view_func=admin_list_teachers, methods=['GET'])

    app.add_url_rule('/api/topics', view_func=list_topics, methods=['GET'])
    app.add_url_rule('/api/topics', view_func=create_topic, methods=['POST'])

    app.add_url_rule('/api/questions', view_func=create_question, methods=['POST'])
    app.add_url_rule('/api/questions', view_func=get_questions, methods=['GET'])
    app.add_url_rule(
        '/api/questions/recommendations',
        view_func=get_recommendations,
        methods=['GET'],
    )
    app.add_url_rule('/api/questions/<int:qid>', view_func=get_question_by_id, methods=['GET'])
    app.add_url_rule('/api/questions/<int:qid>', view_func=update_question, methods=['PUT'])
    app.add_url_rule('/api/questions/<int:qid>', view_func=delete_question, methods=['DELETE'])

    app.add_url_rule('/api/groups', view_func=list_my_groups, methods=['GET'])

    app.add_url_rule('/api/sessions/teacher', view_func=list_teacher_sessions, methods=['GET'])
    app.add_url_rule('/api/sessions/verify-ticket', view_func=verify_join_ticket, methods=['POST'])
    app.add_url_rule('/api/sessions', view_func=create_session, methods=['POST'])
    app.add_url_rule(
        '/api/sessions/<int:sid>/live-qr',
        view_func=get_live_qr,
        methods=['GET'],
    )
    app.add_url_rule(
        '/api/sessions/<int:sid>/close',
        view_func=close_session,
        methods=['POST'],
    )
    app.add_url_rule(
        '/api/sessions/<int:sid>/answers',
        view_func=get_session_answers,
        methods=['GET'],
    )
    app.add_url_rule(
        '/api/sessions/<string:code>',
        view_func=get_session_by_code,
        methods=['GET'],
    )

    app.add_url_rule('/api/answers/my', view_func=my_answers, methods=['GET'])
    app.add_url_rule('/api/answers/submit', view_func=submit_answer, methods=['POST'])
    app.add_url_rule('/api/answers/<int:aid>/grade', view_func=grade_answer, methods=['POST'])

    app.add_url_rule('/api/rating/group', view_func=get_group_rating, methods=['GET'])
    app.add_url_rule('/api/stats/group', view_func=get_group_stats, methods=['GET'])
    app.add_url_rule('/api/analytics/group', view_func=get_group_stat, methods=['GET'])
    app.add_url_rule(
        '/api/analytics/student/<int:student_id>',
        view_func=get_student_stat,
        methods=['GET'],
    )

    app.add_url_rule(
        '/api/groups/<int:group_id>/schedule',
        view_func=get_schedule,
        methods=['GET'],
    )
    app.add_url_rule(
        '/api/groups/<int:group_id>/schedule/current',
        view_func=get_current_slot,
        methods=['GET'],
    )
    app.add_url_rule('/api/schedule', view_func=post_schedule, methods=['POST'])
    app.add_url_rule(
        '/api/schedule/slots/<int:sid>',
        view_func=schedule_slot,
        methods=['PUT', 'DELETE'],
    )

    app.add_url_rule(
        '/api/import/schedule',
        view_func=post_import_schedule,
        methods=['POST'],
    )

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
