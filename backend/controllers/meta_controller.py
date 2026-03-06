# backend/controllers/meta_controller.py
from flask import request, jsonify
from utils.lan_hosts import collect_lan_ipv4_for_qr, suggested_frontend_origin


def get_qr_origin():
    """Публично: подсказка origin для ссылок в QR, когда фронт открыт с localhost."""
    try:
        port = int(request.args.get('port', 5173))
    except (TypeError, ValueError):
        port = 5173
    port = max(1, min(port, 65535))
    origin = suggested_frontend_origin(port)
    return jsonify({'origin': origin, 'candidates': collect_lan_ipv4_for_qr()})
