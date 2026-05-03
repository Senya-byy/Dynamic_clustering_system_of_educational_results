# backend/repositories/user_repository.py
from typing import List, Optional

from sqlalchemy import func

from models import User, db


class UserRepository:
    @staticmethod
    def find_by_login(login: str) -> Optional[User]:
        if login is None:
            return None
        ln = str(login).strip().lower()
        if not ln:
            return None
        return User.query.filter(func.lower(User.login) == ln).first()

    @staticmethod
    def find_by_id(user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    @staticmethod
    def find_by_group(group_id: int) -> List[User]:
        return User.query.filter_by(group_id=group_id, role='student').all()

    @staticmethod
    def find_by_role(role: str) -> List[User]:
        return User.query.filter_by(role=role).order_by(User.login).all()

    @staticmethod
    def list_all() -> List[User]:
        return User.query.order_by(User.role, User.login).all()

    @staticmethod
    def create(user_data: dict) -> User:
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user_id: int, data: dict) -> User:
        user = User.query.get(user_id)
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        return user

    @staticmethod
    def update_privacy_mode(user_id: int, mode: bool) -> bool:
        user = User.query.get(user_id)
        user.privacy_mode = mode
        db.session.commit()
        return True