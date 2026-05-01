# backend/repositories/session_repository.py
from models import (
    db,
    Session,
    Group,
    JoinTicket,
    Answer,
    Attendance,
    ClusterResult,
    Reminder,
    SessionStudentAssignment,
    SessionDeviceBinding,
)
from datetime import datetime, timedelta

from utils.session_display import format_session_default_title
import secrets
import string
import json
import random
from typing import List, Optional


class SessionRepository:
    @staticmethod
    def generate_unique_code(length=6) -> str:
        while True:
            code = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(length)
            )
            if not Session.query.filter_by(code=code).first():
                return code

    @staticmethod
    def create(data: dict) -> Session:
        data = dict(data)
        pool = data.pop('question_ids', None)
        qpool_json = None
        if pool and isinstance(pool, list) and len(pool) > 0:
            qpool_json = json.dumps([int(x) for x in pool])
            data['question_id'] = random.choice([int(x) for x in pool])
        data['code'] = SessionRepository.generate_unique_code()
        if qpool_json:
            data['question_pool_json'] = qpool_json
        allowed = {
            'code',
            'group_id',
            'question_id',
            'created_by',
            'timer_seconds',
            'question_pool_json',
            'start_time',
            'title',
        }
        row = {k: v for k, v in data.items() if k in allowed}
        now = datetime.utcnow()
        if 'start_time' not in row:
            row['start_time'] = now
        st = row['start_time']
        if not isinstance(st, datetime):
            st = now
            row['start_time'] = st
        raw_title = data.get('title')
        if raw_title is not None and str(raw_title).strip():
            row['title'] = str(raw_title).strip()[:250]
        else:
            row.pop('title', None)
            row['title'] = format_session_default_title(st)
        sess = Session(**row)
        db.session.add(sess)
        db.session.commit()
        return sess

    @staticmethod
    def find_by_code(code: str) -> Optional[Session]:
        return Session.query.filter_by(code=code, is_active=True).first()

    @staticmethod
    def find_by_id(sid: int) -> Optional[Session]:
        return Session.query.get(sid)

    @staticmethod
    def close_session(sid: int) -> bool:
        sess = Session.query.get(sid)
        if sess:
            sess.is_active = False
            sess.end_time = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def find_by_group(group_id: int) -> List[Session]:
        return (
            Session.query.filter_by(group_id=group_id)
            .order_by(Session.start_time.desc())
            .all()
        )

    @staticmethod
    def find_by_teacher(teacher_id: int) -> List[Session]:
        return (
            Session.query.join(Group, Session.group_id == Group.id)
            .filter(Group.teacher_id == teacher_id)
            .order_by(Session.start_time.desc())
            .all()
        )

    @staticmethod
    def update_title(sid: int, title: Optional[str]) -> bool:
        sess = Session.query.get(sid)
        if not sess:
            return False
        if title is None or not str(title).strip():
            sess.title = None
        else:
            sess.title = str(title).strip()[:250]
        db.session.commit()
        return True

    @staticmethod
    def update_qr(sid: int, qr_base64: str) -> None:
        sess = Session.query.get(sid)
        if sess:
            sess.qr_code = qr_base64
            db.session.commit()

    @staticmethod
    def create_join_ticket(session_id: int, nonce: str, ttl_seconds: float = 5.0) -> JoinTicket:
        expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        t = JoinTicket(session_id=session_id, nonce=nonce, expires_at=expires)
        db.session.add(t)
        db.session.commit()
        return t

    @staticmethod
    def purge_expired_tickets(before: Optional[datetime] = None) -> None:
        cutoff = before or datetime.utcnow()
        JoinTicket.query.filter(JoinTicket.expires_at < cutoff).delete()
        db.session.commit()

    @staticmethod
    def find_valid_ticket(nonce: str) -> Optional[JoinTicket]:
        now = datetime.utcnow()
        return (
            JoinTicket.query.filter(
                JoinTicket.nonce == nonce,
                JoinTicket.expires_at >= now,
                JoinTicket.consumed_at.is_(None),
            ).first()
        )

    @staticmethod
    def consume_ticket(ticket: JoinTicket, user_id: int) -> None:
        ticket.consumed_at = datetime.utcnow()
        ticket.consumed_by = user_id
        db.session.commit()

    @staticmethod
    def delete_session_cascade(sid: int) -> bool:
        sess = Session.query.get(sid)
        if not sess:
            return False
        JoinTicket.query.filter_by(session_id=sid).delete()
        SessionStudentAssignment.query.filter_by(session_id=sid).delete()
        SessionDeviceBinding.query.filter_by(session_id=sid).delete()
        Answer.query.filter_by(session_id=sid).delete()
        Attendance.query.filter_by(session_id=sid).delete()
        ClusterResult.query.filter_by(session_id=sid).delete()
        Reminder.query.filter_by(session_id=sid).delete()
        db.session.delete(sess)
        db.session.commit()
        return True

    @staticmethod
    def purge_question_from_sessions(qid: int) -> None:
        """Удаляет сессии с этим вопросом и вычищает id из пулов (перед удалением Question)."""
        qid = int(qid)
        for sess in list(Session.query.filter_by(question_id=qid).all()):
            SessionRepository.delete_session_cascade(sess.id)

        for sess in Session.query.filter(Session.question_pool_json.isnot(None)).all():
            try:
                pool = json.loads(sess.question_pool_json)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(pool, list) or qid not in [int(x) for x in pool]:
                continue
            new_pool = [int(x) for x in pool if int(x) != qid]
            if not new_pool:
                SessionRepository.delete_session_cascade(sess.id)
            else:
                sess.question_pool_json = json.dumps(new_pool)
                if int(sess.question_id) == qid:
                    sess.question_id = random.choice(new_pool)
                db.session.commit()

    @staticmethod
    def delete_sessions_for_group(group_id: int) -> None:
        for sess in list(Session.query.filter_by(group_id=group_id).all()):
            SessionRepository.delete_session_cascade(sess.id)
