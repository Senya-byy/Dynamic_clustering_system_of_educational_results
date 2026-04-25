# backend/controllers/import_controller.py
from flask import request, jsonify
from services.import_service import ImportService
from middleware.auth_middleware import token_required, role_required

import_service = ImportService()


@token_required
@role_required(['teacher', 'admin'])
def post_import_schedule(current_user):
    if 'file' not in request.files:
        return jsonify({'error': 'Нужен файл file (CSV)'}), 400
    f = request.files['file']
    try:
        out = import_service.import_schedule_csv(
            f.stream, current_user['id'], current_user['role']
        )
        return jsonify(out), 201
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
