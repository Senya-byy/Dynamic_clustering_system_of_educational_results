from repositories.user_repository import UserRepository
from utils.jwt_utils import create_token, decode_token

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
    
    def login(self, login: str, password: str) -> dict | None:
        user = self.user_repo.find_by_login(login)
        if not user or not user.authenticate(password):
            return None
        token = create_token(user.id, user.login, user.role)
        return {
            'access_token': token,
            'user': {
                'id': user.id,
                'login': user.login,
                'role': user.role,
                'privacy_mode': user.privacy_mode
            }
        }
    
    def validate_token(self, token: str) -> dict | None:
        payload = decode_token(token)
        if not payload:
            return None
        user = self.user_repo.find_by_id(payload['user_id'])
        if not user:
            return None
        return payload
    
    def get_profile(self, user_id: int) -> dict | None:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return None
        return {
            'id': user.id,
            'login': user.login,
            'role': user.role,
            'privacy_mode': user.privacy_mode
        }
