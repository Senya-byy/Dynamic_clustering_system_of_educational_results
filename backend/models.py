# backend/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('groups.id', use_alter=True, name='fk_users_group_id'),
        nullable=True,
    )
    privacy_mode = db.Column(db.Boolean, default=False)
    full_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8'),
        )


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    # Legacy «владелец»; новые группы без владельца (NULL). Доступ преподавателей — teacher_groups.
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # active|pending|archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TeacherGroup(db.Model):
    __tablename__ = 'teacher_groups'
    __table_args__ = (
        db.UniqueConstraint('teacher_id', 'group_id', name='uq_teacher_groups_teacher_group'),
    )
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('groups.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CourseGroup(db.Model):
    __tablename__ = 'course_groups'
    __table_args__ = (
        db.UniqueConstraint('course_id', 'group_id', name='uq_course_groups_course_group'),
    )
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('groups.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    topic = db.Column(db.String(100), nullable=True)  # денормализация / legacy
    difficulty = db.Column(db.String(20), nullable=True)
    max_score = db.Column(db.Integer, nullable=False, default=1)
    correct_answer = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    qr_code = db.Column(db.Text, nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(250), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    timer_seconds = db.Column(db.Integer, nullable=True)
    question_pool_json = db.Column(db.Text, nullable=True)  # JSON list id вопросов
    # Статический PIN для ручного входа (без QR); выдаётся только преподавателю в live-qr.
    join_pin = db.Column(db.String(12), nullable=True)
    frozen_qr_nonce = db.Column(db.String(128), nullable=True)


class SessionGroup(db.Model):
    __tablename__ = 'session_groups'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'group_id', name='uq_session_groups_session_group'),
    )
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('groups.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JoinTicket(db.Model):
    """Краткоживущий билет по динамическому QR: один nonce до истечения срока — для любого студента группы."""
    __tablename__ = 'join_tickets'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    nonce = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    consumed_at = db.Column(db.DateTime, nullable=True)
    consumed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class SessionDeviceBinding(db.Model):
    """Одно устройство (браузер) на пару — только один аккаунт; смена логина на том же телефоне блокируется."""
    __tablename__ = 'session_device_bindings'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'device_key', name='uq_session_device'),
    )
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    device_key = db.Column(db.String(128), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SessionStudentAssignment(db.Model):
    """Какой вопрос из пула (или единственный) закреплён за студентом в этой паре."""
    __tablename__ = 'session_student_assignments'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='uq_session_student_assignment'),
    )
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    checked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    checked_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, default=False)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='present')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ScheduleSlot(db.Model):
    __tablename__ = 'schedule_slots'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0 = понедельник
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClusterResult(db.Model):
    """Заготовка под C4 / Could have (кластеризация)."""
    __tablename__ = 'cluster_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    cluster_id = db.Column(db.Integer, nullable=False)
    transition_from = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClusterRun(db.Model):
    """История запусков k-means по группе (динамика кластеров)."""
    __tablename__ = 'cluster_runs'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.Integer,
        db.ForeignKey('groups.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    n_clusters = db.Column(db.Integer, nullable=False)
    silhouette_score = db.Column(db.Float, nullable=True)
    assignments = db.relationship(
        'ClusterAssignment',
        backref='run',
        lazy=True,
        cascade='all, delete-orphan',
    )


class ClusterAssignment(db.Model):
    """Назначение студента в кластер в рамках одного запуска."""
    __tablename__ = 'cluster_assignments'
    __table_args__ = (
        db.UniqueConstraint('run_id', 'student_id', name='uq_cluster_run_student'),
    )
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(
        db.Integer,
        db.ForeignKey('cluster_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    cluster_label = db.Column(db.Integer, nullable=False)
    feature_vector_json = db.Column(db.Text, nullable=True)


class Reminder(db.Model):
    """Заготовка под C4 / Could have (уведомления)."""
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    send_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
