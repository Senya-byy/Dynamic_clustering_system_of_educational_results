import pytest
import os
import sys

# Ensure test environment before importing backend app module (it has optional module-level app creation).
os.environ["APP_ENV"] = "test"
os.environ["SEED_DATA"] = "false"

# Ensure backend/ is importable regardless of pytest rootdir.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import User, db as _db
import bcrypt

@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret"
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    with app.test_client() as client:
        with app.app_context():
            _db.create_all()
            # Be defensive: if a prior engine/connection reused the same DB file,
            # ensure the fixture user does not already exist.
            _db.session.query(User).filter_by(login="testuser").delete()
            _db.session.commit()
            password = 'pass123'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(
                login='testuser',
                role='student',
                password_hash=password_hash
            )
            _db.session.add(user)
            _db.session.commit()
        yield client
        with app.app_context():
            _db.drop_all()

def test_login_success(client):
    resp = client.post('/api/auth/login', json={
        'login': 'testuser',
        'password': 'pass123'
    })
    assert resp.status_code == 200
    assert 'access_token' in resp.json

def test_login_wrong_password(client):
    resp = client.post('/api/auth/login', json={
        'login': 'testuser',
        'password': 'wrong'
    })
    assert resp.status_code == 401

def test_login_missing_fields(client):
    resp = client.post('/api/auth/login', json={})
    assert resp.status_code == 400
