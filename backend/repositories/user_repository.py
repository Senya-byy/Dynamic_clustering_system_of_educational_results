from models import db, User

class UserRepository:
    def find_by_login(self, login: str) -> User | None:
        return User.query.filter_by(login=login).first()
    
    def find_by_id(self, id: int) -> User | None:
        return User.query.get(id)
    
    def find_by_role(self, role: str) -> list[User]:
        return User.query.filter_by(role=role).all()
    
    def create(self, user_data: dict) -> User:
        user = User(
            login=user_data['login'],
            role=user_data['role'],
            privacy_mode=user_data.get('privacy_mode', False)
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        db.session.commit()
        return user
    
    def update(self, user_id: int, data: dict) -> User | None:
        user = self.find_by_id(user_id)
        if user:
            for key, value in data.items():
                if hasattr(user, key) and key != 'password_hash':
                    setattr(user, key, value)
            db.session.commit()
        return user
    
    def update_privacy_mode(self, user_id: int, mode: bool) -> bool:
        user = self.update(user_id, {'privacy_mode': mode})
        return user is not None
