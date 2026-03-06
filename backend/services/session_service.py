# backend/services/session_service.py
from collections import Counter
import json
import random

from sqlalchemy.exc import IntegrityError

from repositories.session_repository import SessionRepository
from repositories.question_repository import QuestionRepository
from repositories.attendance_repository import AttendanceRepository
from repositories.answer_repository import AnswerRepository
from repositories.user_repository import UserRepository
from repositories.assignment_repository import AssignmentRepository
from repositories.device_binding_repository import DeviceBindingRepository
from models import db, Group, Topic, Question, SessionStudentAssignment
from utils.device_key import normalize_device_key
from utils.qr_generator import generate_qr_base64
from utils.session_display import session_display_title
from datetime import datetime
from typing import Dict, List, Optional
import secrets
from urllib.parse import quote


class SessionService:
    def __init__(self):
        self.session_repo = SessionRepository()
        self.question_repo = QuestionRepository()
        self.attendance_repo = AttendanceRepository()
        self.answer_repo = AnswerRepository()
        self.user_repo = UserRepository()
        self.assign_repo = AssignmentRepository()

    @staticmethod
    def _session_pool_ids(sess) -> List[int]:
        raw = getattr(sess, 'question_pool_json', None)
        if raw:
            try:
                pool = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pool = []
            if isinstance(pool, list) and len(pool) > 0:
                return [int(x) for x in pool]
        return [int(sess.question_id)]

    @staticmethod
    def pick_question_for_student(sess) -> int:
        pool = SessionService._session_pool_ids(sess)
        if len(pool) == 1:
            return pool[0]
        rows = SessionStudentAssignment.query.filter_by(session_id=sess.id).all()
        counts = Counter(r.question_id for r in rows)
        unused = [q for q in pool if counts[q] == 0]
        return random.choice(unused if unused else pool)

    def ensure_device_binding(self, session_id: int, device_key: str, student_id: int) -> None:
        row = DeviceBindingRepository.find(session_id, device_key)
        if row:
            if row.student_id != student_id:
                raise ValueError(
                    'На этом устройстве уже начата эта пара под другим аккаунтом. '
                    'Выйдите из чужого профиля или откройте ссылку с другого телефона.'
                )
            return
        try:
            DeviceBindingRepository.create(session_id, device_key, student_id)
        except IntegrityError:
            db.session.rollback()
            again = DeviceBindingRepository.find(session_id, device_key)
            if again and again.student_id != student_id:
                raise ValueError(
                    'На этом устройстве уже начата эта пара под другим аккаунтом. '
                    'Выйдите из чужого профиля или откройте ссылку с другого телефона.'
                )
            if not again:
                raise

    def ensure_student_question_id(self, sess, student_id: int) -> int:
        row = self.assign_repo.find(sess.id, student_id)
        if row:
            return row.question_id
        qid = SessionService.pick_question_for_student(sess)
        try:
            self.assign_repo.create(sess.id, student_id, qid)
            return qid
        except IntegrityError:
            db.session.rollback()
            again = self.assign_repo.find(sess.id, student_id)
            if again:
                return again.question_id
            raise

    @staticmethod
    def question_ids_from_topic_ids(topic_ids: List[int], owner_teacher_id: int) -> List[int]:
        """Все вопросы преподавателя, привязанные к темам каталога (поле topic_id у вопроса)."""
        if not topic_ids:
            raise ValueError('Не выбраны темы')
        seen_t = set()
        ordered_topics: List[int] = []
        for tid in topic_ids:
            tid = int(tid)
            if tid not in seen_t:
                seen_t.add(tid)
                ordered_topics.append(tid)
        for tid in ordered_topics:
            t = Topic.query.get(tid)
            if not t:
                raise ValueError(f'Тема {tid} не найдена')
            if t.teacher_id != owner_teacher_id:
                raise ValueError('Тема не из каталога преподавателя этой группы')
        rows = (
            Question.query.filter(
                Question.topic_id.in_(ordered_topics),
                Question.created_by == owner_teacher_id,
            )
            .order_by(Question.id)
            .all()
        )
        if not rows:
            raise ValueError(
                'В выбранных темах нет вопросов. При создании вопроса укажите «Тему из каталога».'
            )
        return [q.id for q in rows]

    def create_session(self, data: Dict) -> Dict:
        sess = self.session_repo.create(data)
        return {
            'id': sess.id,
            'code': sess.code,
            'question_id': sess.question_id,
            'start_time': sess.start_time.isoformat(),
        }

    def issue_live_qr(self, session_id: int, teacher_id: int, base_url: str) -> Dict:
        sess = self.session_repo.find_by_id(session_id)
        if not sess or not sess.is_active:
            raise ValueError('Сессия не найдена или закрыта')
        group = Group.query.get(sess.group_id)
        u = self.user_repo.find_by_id(teacher_id)
        is_admin = u and u.role == 'admin'
        if not group or (group.teacher_id != teacher_id and not is_admin):
            raise PermissionError('Нет доступа к сессии')

        self.session_repo.purge_expired_tickets()
        nonce = secrets.token_urlsafe(24)
        self.session_repo.create_join_ticket(sess.id, nonce, ttl_seconds=3.5)
        base = base_url.rstrip('/')
        join_path = f"{base}/join?code={quote(sess.code)}&nonce={quote(nonce)}"
        qr_base64 = generate_qr_base64(join_path)
        self.session_repo.update_qr(sess.id, qr_base64)
        return {
            'session_id': sess.id,
            'code': sess.code,
            'nonce': nonce,
            'expires_in_seconds': 3,
            'join_url': join_path,
            'qr_code': qr_base64,
        }

    def verify_join_ticket(
        self, code: str, nonce: str, student_id: int, device_key: str
    ) -> Optional[Dict]:
        student_id = int(student_id)
        device_key = normalize_device_key(device_key)
        ticket = self.session_repo.find_valid_ticket(nonce)
        if not ticket:
            raise ValueError('Неверный или просроченный QR. Отсканируйте текущий код.')
        sess = self.session_repo.find_by_id(ticket.session_id)
        if not sess or sess.code != code or not sess.is_active:
            raise ValueError('Сессия не найдена')

        user = self.user_repo.find_by_id(student_id)
        if not user or user.role != 'student':
            raise PermissionError('Только студент может входить по QR')
        if user.group_id != sess.group_id:
            raise PermissionError('Эта пара не для вашей группы')

        existing = self.answer_repo.find_by_session_student(sess.id, student_id)
        if existing:
            raise ValueError(
                'Вы уже отправили ответ на эту пару с этого аккаунта (в том числе с другого телефона). '
                'Повторно получить вопрос нельзя.'
            )

        self.ensure_device_binding(sess.id, device_key, student_id)

        qid = self.ensure_student_question_id(sess, student_id)
        self.session_repo.consume_ticket(ticket, student_id)
        question = self.question_repo.find_by_id(qid)
        return {
            'id': sess.id,
            'code': sess.code,
            'question_id': qid,
            'question': {
                'text': question.text,
                'topic': question.topic,
                'difficulty': question.difficulty,
                'max_score': question.max_score,
            },
            'timer_seconds': sess.timer_seconds,
        }

    def get_session_by_code(self, code: str, role: str) -> Optional[Dict]:
        """Просмотр состава пары преподавателем (без одноразового билета)."""
        if role not in ('teacher', 'admin'):
            return None
        sess = self.session_repo.find_by_code(code)
        if not sess:
            return None
        question = self.question_repo.find_by_id(sess.question_id)
        return {
            'id': sess.id,
            'code': sess.code,
            'question': {
                'text': question.text,
                'topic': question.topic,
                'difficulty': question.difficulty,
                'max_score': question.max_score,
            },
            'timer_seconds': sess.timer_seconds,
        }

    def close_session(self, session_id: int, teacher_id: int) -> bool:
        sess = self.session_repo.find_by_id(session_id)
        if not sess:
            return False
        group = Group.query.get(sess.group_id)
        u = self.user_repo.find_by_id(teacher_id)
        is_admin = u and u.role == 'admin'
        if group and group.teacher_id != teacher_id and not is_admin:
            return False
        return self.session_repo.close_session(session_id)

    def list_for_teacher(self, teacher_id: int):
        sessions = self.session_repo.find_by_teacher(teacher_id)
        return [
            {
                'id': s.id,
                'code': s.code,
                'title': getattr(s, 'title', None),
                'display_title': session_display_title(s),
                'is_active': s.is_active,
                'start_time': s.start_time.isoformat(),
                'group_id': s.group_id,
                'question_id': s.question_id,
            }
            for s in sessions
        ]

    def rename_session_title(
        self, session_id: int, teacher_id: int, title: Optional[str]
    ) -> Optional[Dict]:
        sess = self.session_repo.find_by_id(session_id)
        if not sess:
            return None
        group = Group.query.get(sess.group_id)
        u = self.user_repo.find_by_id(teacher_id)
        is_admin = u and u.role == 'admin'
        if not group or (group.teacher_id != teacher_id and not is_admin):
            raise PermissionError('Нет доступа к сессии')
        self.session_repo.update_title(session_id, title)
        sess = self.session_repo.find_by_id(session_id)
        return {
            'title': sess.title,
            'display_title': session_display_title(sess),
        }
