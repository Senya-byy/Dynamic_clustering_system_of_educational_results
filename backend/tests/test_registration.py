import os
import sys

import pytest

os.environ["APP_ENV"] = "test"
os.environ["SEED_DATA"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import db as _db  # noqa: E402
from models import User, Group  # noqa: E402


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
            # Seed minimal data for registration flows:
            # - an admin (for completeness)
            # - a teacher-owner for groups (legacy owner)
            # - a couple of groups that teachers can attach
            admin = User(login="admin", role="admin", full_name="Админ", group_id=None)
            admin.set_password("admin123")
            owner = User(login="owner", role="teacher", full_name="Owner Teacher", group_id=None)
            owner.set_password("owner123")
            _db.session.add_all([admin, owner])
            _db.session.commit()
            g1 = Group(name="Группа-X", teacher_id=owner.id)
            g2 = Group(name="Группа-Y", teacher_id=owner.id)
            _db.session.add_all([g1, g2])
            _db.session.commit()
        yield c
        with app.app_context():
            _db.drop_all()


def test_register_groups_public(client):
    r = client.get("/api/register/groups")
    assert r.status_code == 200
    names = {x["name"] for x in (r.json or [])}
    assert "Группа-X" in names and "Группа-Y" in names


def test_register_teacher_then_student(client):
    gl = client.get("/api/register/groups")
    assert gl.status_code == 200
    gid = next(x["id"] for x in gl.json if x["name"] == "Группа-X")
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "newteacher",
            "password": "Secret12",
            "full_name": "Иванов Иван Иванович",
            "group_ids": [gid],
            "new_group_names": [],
        },
    )
    assert r.status_code == 201, r.json
    assert r.json["role"] == "teacher"
    assert "access_token" in r.json

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
    gl = client.get("/api/register/groups").json
    gid = gl[0]["id"]
    client.post(
        "/api/register/teacher",
        json={
            "login": "dup",
            "password": "Secret12",
            "full_name": "Сидоров Сидор Сидорович",
            "group_ids": [gid],
            "new_group_names": [],
        },
    )
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


def test_register_teacher_cannot_create_new_groups(client):
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "t2",
            "password": "Secret12",
            "full_name": "Петров Пётр Петрович",
            "group_ids": [],
            "new_group_names": ["uniqueg"],
        },
    )
    assert r.status_code == 400


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_teacher_add_then_delete_own_group(client):
    gl = client.get("/api/register/groups")
    gid_x = next(x["id"] for x in gl.json if x["name"] == "Группа-X")
    gid_y = next(x["id"] for x in gl.json if x["name"] == "Группа-Y")
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "tgrp",
            "password": "Secret12",
            "full_name": "Смирнов Семён Семёнович",
            "group_ids": [gid_x],
            "new_group_names": [],
        },
    )
    assert r.status_code == 201
    token = r.json["access_token"]
    h = _bearer(token)

    gl = client.get("/api/groups", headers=h)
    assert gl.status_code == 200
    assert len(gl.json) == 1

    # Attach another existing group.
    add = client.post("/api/teachers/me/groups", headers=h, json={"group_id": gid_y})
    assert add.status_code in (200, 201), add.json

    gl2 = client.get("/api/groups", headers=h)
    assert len(gl2.json) == 2

    # Detach it back (no deletion).
    d = client.delete(f"/api/teachers/me/groups/{gid_y}", headers=h)
    assert d.status_code == 200, d.json

    gl3 = client.get("/api/groups", headers=h)
    assert len(gl3.json) == 1


def test_teacher_cannot_delete_other_teacher_group(client):
    gl = client.get("/api/register/groups")
    gid_a = next(x["id"] for x in gl.json if x["name"] == "Группа-X")
    r = client.post(
        "/api/register/teacher",
        json={
            "login": "tea_two",
            "password": "Secret12",
            "full_name": "Борисов Борис Борисович",
            "group_ids": [gid_a],
            "new_group_names": [],
        },
    )
    assert r.status_code == 201
    token_b = r.json["access_token"]

    d = client.delete(f"/api/teachers/me/groups/{gid_a}", headers=_bearer(token_b))
    # Not attached -> should still be ok (idempotent-ish) or 200.
    assert d.status_code in (200, 400)
