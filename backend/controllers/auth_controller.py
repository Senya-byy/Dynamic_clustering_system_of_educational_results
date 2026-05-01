# backend/controllers/auth_controller.py
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from services.profile_service import ProfileService
from middleware.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()
profile_service = ProfileService()


@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    if not data or 'login' not in data or 'password' not in data:
        return jsonify({'error': 'Login and password required'}), 400

    result = auth_service.login(data['login'], data['password'])
    if result is None:
        return jsonify({'error': 'Invalid credentials'}), 401

    return jsonify(result), 200


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    profile = profile_service.get_profile(current_user['id'])
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(profile), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    try:
        profile = profile_service.update_profile(current_user['id'], data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify(profile), 200


@auth_bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.get_json() or {}
    old_p = data.get('old_password')
    new_p = data.get('new_password')
    if old_p is None or new_p is None or str(old_p).strip() == '' or str(new_p).strip() == '':
        return jsonify({'error': 'old_password и new_password обязательны'}), 400
    new_p = str(new_p)
    if len(new_p) < 4:
        return jsonify({'error': 'Новый пароль не короче 4 символов'}), 400
    ok = auth_service.change_password(
        current_user['id'], str(old_p), new_p
    )
    if not ok:
        return jsonify({'error': 'Неверный текущий пароль'}), 400
    return jsonify({'message': 'Пароль обновлён'}), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    return jsonify({'message': 'Logged out successfully'}), 200
