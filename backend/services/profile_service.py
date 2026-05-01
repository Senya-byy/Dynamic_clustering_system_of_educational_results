# backend/services/profile_service.py
from repositories.user_repository import UserRepository
from typing import Dict

class ProfileService:
    def __init__(self):
        self.user_repo = UserRepository()

    def get_profile(self, user_id: int) -> Dict:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return None
        return {
            'id': user.id,
            'login': user.login,
            'role': user.role,
            'full_name': user.full_name,
            'group_id': user.group_id,
            'privacy_mode': user.privacy_mode
        }

    def update_profile(self, user_id: int, data: Dict) -> Dict:
        allowed = ['full_name', 'privacy_mode']
        update_data = {k: v for k, v in data.items() if k in allowed}
        if 'full_name' in update_data and update_data['full_name'] is not None:
            fn = str(update_data['full_name']).strip()
            if len(fn) > 200:
                raise ValueError('ФИО не длиннее 200 символов')
            update_data['full_name'] = fn or None
        if update_data:
            user = self.user_repo.update(user_id, update_data)
            return self.get_profile(user.id)
        return self.get_profile(user_id)