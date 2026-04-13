# backend/services/session_service.py
from repositories.session_repository import SessionRepository
from repositories.question_repository import QuestionRepository
from repositories.attendance_repository import AttendanceRepository
from repositories.answer_repository import AnswerRepository
from repositories.user_repository import UserRepository
from models import Group
from utils.qr_generator import generate_qr_base64
from datetime import datetime
from typing import Dict, Optional
import secrets
from urllib.parse import quote


class SessionService:
    def __init__(self):
        self.session_repo = SessionRepository()
        self.question_repo = QuestionRepository()
        self.attendance_repo = AttendanceRepository()
        self.answer_repo = AnswerRepository()
        self.user_repo = UserRepository()

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
        self, code: str, nonce: str, student_id: int
    ) -> Optional[Dict]:
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
            raise ValueError('Вы уже отправили ответ на эту пару')

        self.session_repo.consume_ticket(ticket, student_id)
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
                'is_active': s.is_active,
                'start_time': s.start_time.isoformat(),
                'group_id': s.group_id,
                'question_id': s.question_id,
            }
            for s in sessions
        ]
