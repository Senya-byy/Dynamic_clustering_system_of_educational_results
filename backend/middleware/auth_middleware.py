from functools import wraps
from flask import request, jsonify, g
from services.auth_service import AuthService

auth_service = AuthService()

def validate_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization header format'}), 401
        token = auth_header.split(' ')[1]
        payload = auth_service.validate_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        g.user = payload
        return f(*args, **kwargs)
    return decorated
