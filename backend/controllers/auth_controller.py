from flask import Blueprint, request, jsonify, g
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()

@auth_bp.route('/login', methods=['POST'])
def post_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    login = data.get('login')
    password = data.get('password')
    if not login or not password:
        return jsonify({'error': 'Login and password are required'}), 400
    result = auth_service.login(login, password)
    if not result:
        return jsonify({'error': 'Invalid credentials'}), 401
    return jsonify(result), 200

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    if not hasattr(g, 'user') or not g.user:
        return jsonify({'error': 'Unauthorized'}), 401
    profile = auth_service.get_profile(g.user['user_id'])
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(profile), 200

from middleware.auth_middleware import validate_token
