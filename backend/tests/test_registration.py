import os
import sys

import pytest

os.environ["APP_ENV"] = "test"
os.environ["SEED_DATA"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import db as _db  # noqa: E402


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "reg.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret"
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    with app.test_client() as c:
        with app.app_context():
            _db.create_all()
        yield c
        with app.app_context():
            _db.drop_all()


def test_register_groups_public(client):
    r = client.get("/api/register/groups")
    assert r.status_code == 200
    assert r.json == []


def test_register_teacher_then_student(client):
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "newteacher",
            "password": "Secret12",
            "full_name": "Иванов Иван Иванович",
            "new_group_names": ["Группа-X", "Группа-Y"],
        },
    )
    assert r.status_code == 201, r.json
    assert r.json["role"] == "teacher"
    assert "access_token" in r.json

    gl = client.get("/api/register/groups")
    assert gl.status_code == 200
    names = {x["name"] for x in gl.json}
    assert "Группа-X" in names and "Группа-Y" in names
    gid = next(x["id"] for x in gl.json if x["name"] == "Группа-X")

    r2 = client.post(
        "/api/register/student",
        json={
            "login": "newstudent",
            "password": "Secret12",
            "full_name": "Петров Пётр Петрович",
            "group_id": gid,
        },
    )
    assert r2.status_code == 201, r2.json
    assert r2.json["role"] == "student"
    assert r2.json["group_id"] == gid


def test_register_duplicate_login(client):
    client.post(
        "/api/register/teacher",
        json={
            "login": "dup",
            "password": "Secret12",
            "full_name": "Сидоров Сидор Сидорович",
            "new_group_names": ["G-dup"],
        },
    )
    gl = client.get("/api/register/groups").json
    gid = gl[0]["id"]
    r = client.post(
        "/api/register/student",
        json={
            "login": "dup",
            "password": "Secret12",
            "full_name": "Алексеев Алексей Алексеевич",
            "group_id": gid,
        },
    )
    assert r.status_code == 400


def test_register_duplicate_group_name(client):
    client.post(
        "/api/register/teacher",
        json={
            "login": "t1",
            "password": "Secret12",
            "full_name": "Иванов Иван Иванович",
            "new_group_names": ["UniqueG"],
        },
    )
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "t2",
            "password": "Secret12",
            "full_name": "Петров Пётр Петрович",
            "new_group_names": ["uniqueg"],
        },
    )
    assert r.status_code == 400
