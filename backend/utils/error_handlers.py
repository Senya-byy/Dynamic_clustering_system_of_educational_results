from __future__ import annotations

import logging
from typing import Any, Tuple

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def _json_error(message: str, status_code: int, *, code: str | None = None) -> Tuple[Any, int]:
    payload: dict[str, Any] = {"error": message}
    if code:
        payload["code"] = code
    return jsonify(payload), status_code


def register_error_handlers(app: Flask) -> None:
    logger = logging.getLogger("classqr")

    @app.errorhandler(HTTPException)
    def _handle_http_exception(e: HTTPException):
        # Keep response shape stable: {"error": "..."}
        return _json_error(e.description, int(e.code or 500))

    @app.errorhandler(ValueError)
    def _handle_value_error(e: ValueError):
        return _json_error(str(e) or "Некорректные данные", 400)

    @app.errorhandler(PermissionError)
    def _handle_permission_error(e: PermissionError):
        return _json_error(str(e) or "Недостаточно прав", 403)

    @app.errorhandler(Exception)
    def _handle_unexpected(e: Exception):
        logger.exception("Unhandled exception: %s", e)
        # Do not leak internals to clients.
        return _json_error("Внутренняя ошибка сервера", 500)

