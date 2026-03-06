# backend/middleware/auth_middleware.py
from functools import wraps
from flask import request, jsonify
import jwt
from config import Config
from repositories.user_repository import UserRepository

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Извлечение токена из заголовка Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            # Декодирование токена
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            try:
                uid = int(payload.get('id'))
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid token'}), 401
            current_user = {
                'id': uid,
                'role': payload.get('role'),
                'exp': payload.get('exp')
            }
            # Проверка, что пользователь существует в БД (опционально)
            user_repo = UserRepository()
            user = user_repo.find_by_id(current_user['id'])
            if not user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def role_required(allowed_roles):
    """
    Декоратор для проверки роли.
    Использование: @role_required(['teacher', 'admin'])
    Должен идти после @token_required, чтобы current_user был определён.
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.get('role') not in allowed_roles:
                return jsonify({'error': 'Forbidden: insufficient role'}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator