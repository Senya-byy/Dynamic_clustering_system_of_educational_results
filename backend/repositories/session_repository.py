# backend/repositories/session_repository.py
from models import db, Session, Group, JoinTicket
from datetime import datetime, timedelta
import secrets
import string
import json
import random
from typing import Optional, List


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
        }
        row = {k: v for k, v in data.items() if k in allowed}
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
    def update_qr(sid: int, qr_base64: str) -> None:
        sess = Session.query.get(sid)
        if sess:
            sess.qr_code = qr_base64
            db.session.commit()

    @staticmethod
    def create_join_ticket(session_id: int, nonce: str, ttl_seconds: float = 3.0) -> JoinTicket:
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
