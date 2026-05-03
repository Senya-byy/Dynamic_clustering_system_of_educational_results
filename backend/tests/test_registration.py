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


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_teacher_add_then_delete_own_group(client):
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "tgrp",
            "password": "Secret12",
            "full_name": "Смирнов Семён Семёнович",
            "new_group_names": ["Группа-основная"],
        },
    )
    assert r.status_code == 201
    token = r.json["access_token"]
    h = _bearer(token)

    add = client.post("/api/groups", headers=h, json={"name": "Группа-доп"})
    assert add.status_code == 201, add.json
    gid_extra = add.json["id"]

    gl = client.get("/api/groups", headers=h)
    assert gl.status_code == 200
    assert len(gl.json) == 2

    d = client.delete(f"/api/groups/{gid_extra}", headers=h)
    assert d.status_code == 200, d.json

    gl2 = client.get("/api/groups", headers=h)
    assert len(gl2.json) == 1
    assert gl2.json[0]["name"] == "Группа-основная"


def test_teacher_cannot_delete_other_teacher_group(client):
    client.post(
        "/api/register/teacher",
        json={
            "login": "tea_one",
            "password": "Secret12",
            "full_name": "Алексеев Алексей Алексеевич",
            "new_group_names": ["Г-A"],
        },
    )
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "tea_two",
            "password": "Secret12",
            "full_name": "Борисов Борис Борисович",
            "new_group_names": ["Г-B"],
        },
    )
    assert r.status_code == 201
    token_b = r.json["access_token"]
    gl = client.get("/api/register/groups")
    gid_a = next(x["id"] for x in gl.json if x["name"] == "Г-A")

    d = client.delete(f"/api/groups/{gid_a}", headers=_bearer(token_b))
    assert d.status_code == 400
    assert "свою" in (d.json.get("error") or "").lower()
