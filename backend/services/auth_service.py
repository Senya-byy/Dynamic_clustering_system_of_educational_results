# backend/services/auth_service.py
from repositories.user_repository import UserRepository
import jwt
from config import Config
from datetime import datetime, timedelta

def create_token(user_id: int, login: str, role: str) -> str:
    payload = {
        'id': user_id,
        'login': login,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def login(self, login: str, password: str):
        user = self.user_repo.find_by_login(login)
        if not user or not user.check_password(password):
            return None
        token = create_token(user.id, user.login, user.role)
        return {
            'access_token': token,
            'role': user.role,
            'user_id': user.id,
            'group_id': user.group_id,
        }

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        user = self.user_repo.find_by_id(user_id)
        if not user or not user.check_password(old_password):
            return False
        user.set_password(new_password)
        from models import db
        db.session.commit()
        return True