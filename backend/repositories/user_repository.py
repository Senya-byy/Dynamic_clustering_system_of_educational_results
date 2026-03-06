# backend/repositories/user_repository.py
from models import db, User, Group
from typing import Optional, List

class UserRepository:
    @staticmethod
    def find_by_login(login: str) -> Optional[User]:
        return User.query.filter_by(login=login).first()

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