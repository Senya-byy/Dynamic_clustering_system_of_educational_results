"""
WSGI entrypoint for production servers (e.g., PythonAnywhere, gunicorn).

PythonAnywhere expects a module-level variable named `application`.
"""

import os

# Default to production if not explicitly set by hosting environment.
os.environ.setdefault("APP_ENV", "production")

from app import create_app  # noqa: E402

application = create_app()

