import jwt
from datetime import datetime, timedelta
from flask import current_app
import logging

def create_token(user_id: int, login: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'login': login,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS'])
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token: str) -> dict | None:
    logger = logging.getLogger("classqr.jwt")
    try:
        return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        logger.info("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.info("Invalid token: %s", e)
        return None