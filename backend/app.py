# backend/app.py
import os
import logging
from flask import Flask
from sqlalchemy.exc import OperationalError
from config import Config
from models import db
from utils.lan_hosts import vite_lan_cors_origins
from utils.error_handlers import register_error_handlers


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


def _ensure_sqlite_migrations():
    """Добавляет столбцы в существующую SQLite-базу (create_all их не меняет)."""
    from sqlalchemy import inspect, text

    if db.engine.url.drivername != 'sqlite':
        return
    insp = inspect(db.engine)
    tables = insp.get_table_names()
    if 'answers' in tables:
        cols = {c['name'] for c in insp.get_columns('answers')}
        if 'question_id' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE answers ADD COLUMN question_id INTEGER'))
        if 'is_late' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE answers ADD COLUMN is_late BOOLEAN DEFAULT 0'))
    if 'sessions' in tables:
        scols = {c['name'] for c in insp.get_columns('sessions')}
        if 'title' not in scols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE sessions ADD COLUMN title VARCHAR(250)'))
        if 'question_pool_json' not in scols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE sessions ADD COLUMN question_pool_json TEXT'))
    if 'cluster_runs' in tables:
        crc = {c['name'] for c in insp.get_columns('cluster_runs')}
        if 'silhouette_score' not in crc:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE cluster_runs ADD COLUMN silhouette_score FLOAT'))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    from flask_cors import CORS

    app_env = (os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "development").lower()

    logging.basicConfig(
        level=logging.INFO if app_env == "production" else logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("werkzeug").setLevel(logging.INFO)

    register_error_handlers(app)

    cors_origins_raw = os.environ.get("CORS_ORIGINS")
    if cors_origins_raw is None:
        # Safe-by-default:
        # - dev: allow localhost + optional LAN
        # - prod: allow nothing unless explicitly configured
        if app_env == "production":
            origins = []
        else:
            origins = [
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
            ]
    else:
        origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

    cors_allow_lan_default = "false" if app_env == "production" else "true"
    if os.environ.get("CORS_ALLOW_LAN", cors_allow_lan_default).lower() in ("1", "true", "yes"):
        seen = set(origins)
        for o in vite_lan_cors_origins():
            if o not in seen:
                seen.add(o)
                origins.append(o)
    CORS(
        app,
        origins=origins,
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'X-Frontend-Origin'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    )
    db.init_app(app)

    with app.app_context():
        # In tests, DB lifecycle is owned by the test suite.
        if app_env != "test":
            db.create_all()
            _ensure_sqlite_migrations()
            try:
                seed_enabled_default = "false" if app_env == "production" else "true"
                if os.environ.get("SEED_DATA", seed_enabled_default).lower() in ("1", "true", "yes"):
                    seed_data()
            except OperationalError:
                # In dev, rebuilding DB can be acceptable. In production, never drop data.
                if app_env != "production":
                    db.drop_all()
                    db.create_all()
                    _ensure_sqlite_migrations()
                    if os.environ.get("SEED_DATA", "true").lower() in ("1", "true", "yes"):
                        seed_data()
                else:
                    raise

    from controllers.meta_controller import get_qr_origin
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
        patch_session_title,
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
    from controllers.analytics_controller import (
        get_group_stat,
        get_group_students_metrics,
        get_student_stat,
        post_cluster_run,
        list_cluster_runs,
        get_cluster_transitions,
        get_cluster_run_detail,
    )
    from controllers.schedule_controller import (
        get_schedule,
        get_current_slot,
        post_schedule,
        schedule_slot,
    )
    from controllers.import_controller import post_import_schedule
    from controllers.topic_controller import list_topics, create_topic, delete_topic
    from controllers.admin_controller import (
        admin_list_users,
        admin_create_user,
        admin_list_groups,
        admin_create_group,
        admin_list_teachers,
        admin_delete_user,
        admin_delete_group,
    )

    app.add_url_rule('/api/meta/qr-origin', view_func=get_qr_origin, methods=['GET'])

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    app.add_url_rule('/api/admin/users', view_func=admin_list_users, methods=['GET'])
    app.add_url_rule('/api/admin/users', view_func=admin_create_user, methods=['POST'])
    app.add_url_rule(
        '/api/admin/users/<int:uid>',
        view_func=admin_delete_user,
        methods=['DELETE'],
    )
    app.add_url_rule('/api/admin/groups', view_func=admin_list_groups, methods=['GET'])
    app.add_url_rule('/api/admin/groups', view_func=admin_create_group, methods=['POST'])
    app.add_url_rule(
        '/api/admin/groups/<int:gid>',
        view_func=admin_delete_group,
        methods=['DELETE'],
    )
    app.add_url_rule('/api/admin/teachers', view_func=admin_list_teachers, methods=['GET'])

    app.add_url_rule('/api/topics', view_func=list_topics, methods=['GET'])
    app.add_url_rule('/api/topics', view_func=create_topic, methods=['POST'])
    app.add_url_rule('/api/topics/<int:tid>', view_func=delete_topic, methods=['DELETE'])

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
        '/api/sessions/<int:sid>/title',
        view_func=patch_session_title,
        methods=['PATCH'],
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
        '/api/analytics/group/<int:group_id>/students',
        view_func=get_group_students_metrics,
        methods=['GET'],
    )
    app.add_url_rule(
        '/api/analytics/student/<int:student_id>',
        view_func=get_student_stat,
        methods=['GET'],
    )

    app.add_url_rule(
        '/api/analytics/cluster/<int:group_id>',
        view_func=post_cluster_run,
        methods=['POST'],
    )
    app.add_url_rule(
        '/api/analytics/cluster/<int:group_id>/runs',
        view_func=list_cluster_runs,
        methods=['GET'],
    )
    app.add_url_rule(
        '/api/analytics/cluster/<int:group_id>/runs/<int:run_id>',
        view_func=get_cluster_run_detail,
        methods=['GET'],
    )
    app.add_url_rule(
        '/api/analytics/cluster/<int:group_id>/transitions',
        view_func=get_cluster_transitions,
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

    @app.get("/health")
    def health():
        # Deep-ish healthcheck: app + DB connectivity.
        from sqlalchemy import text

        try:
            db.session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        status = 200 if db_ok else 503
        return {
            "status": "ok" if db_ok else "degraded",
            "db": "ok" if db_ok else "error",
            "env": app_env,
        }, status

    return app


_env_for_import = (os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "development").lower()
app = None if _env_for_import == "test" else create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
