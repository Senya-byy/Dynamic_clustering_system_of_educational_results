import os
import sys

import pytest

os.environ["APP_ENV"] = "test"
os.environ["SEED_DATA"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import db as _db, User, Group, Course, CourseGroup, TeacherGroup, Question  # noqa: E402


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _login(client, login: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"login": login, "password": password})
    assert resp.status_code == 200, resp.json
    return resp.json["access_token"]


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret"

    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.test_client() as c:
        with app.app_context():
            _db.create_all()

            t1 = User(login="t1", role="teacher", group_id=None, full_name="T1")
            t1.set_password("p1")
            t2 = User(login="t2", role="teacher", group_id=None, full_name="T2")
            t2.set_password("p2")
            s1 = User(login="s1", role="student", group_id=None, full_name="S1")
            s1.set_password("sp")
            _db.session.add_all([t1, t2, s1])
            _db.session.commit()

            g = Group(name="G1", teacher_id=t1.id)
            _db.session.add(g)
            _db.session.commit()

            # Both teachers attached to same group.
            _db.session.add(TeacherGroup(teacher_id=t1.id, group_id=g.id))
            _db.session.add(TeacherGroup(teacher_id=t2.id, group_id=g.id))
            _db.session.commit()

            s1.group_id = g.id
            _db.session.commit()

            c1 = Course(name="C1", teacher_id=t1.id, archived=False)
            _db.session.add(c1)
            _db.session.commit()
            _db.session.add(CourseGroup(course_id=c1.id, group_id=g.id))
            _db.session.commit()

        yield c

        with app.app_context():
            _db.drop_all()


def test_create_question_without_topic_and_correct_answer(client):
    token = _login(client, "t1", "p1")

    courses = client.get("/api/courses", headers=_auth(token))
    assert courses.status_code == 200
    cid = courses.json[0]["id"]

    created = client.post(
        "/api/questions",
        headers=_auth(token),
        json={
            "course_id": cid,
            "text": "Q no topic and no criteria",
            "max_score": 3,
            "difficulty": "easy",
            # no topic_id/topic/correct_answer
        },
    )
    assert created.status_code == 201, created.json
    assert created.json["text"] == "Q no topic and no criteria"


def test_teacher_cannot_view_answers_of_other_teachers_course(client):
    t1 = _login(client, "t1", "p1")
    t2 = _login(client, "t2", "p2")
    s1 = _login(client, "s1", "sp")

    groups = client.get("/api/groups", headers=_auth(t1))
    gid = groups.json[0]["id"]
    courses = client.get("/api/courses", headers=_auth(t1))
    cid = courses.json[0]["id"]

    # Create a question in teacher1 course directly via DB (simpler for test).
    with client.application.app_context():
        q = Question(
            text="Q1",
            course_id=cid,
            topic_id=None,
            topic=None,
            difficulty="easy",
            max_score=2,
            correct_answer=None,
            created_by=1,
        )
        _db.session.add(q)
        _db.session.commit()
        qid = q.id

    created = client.post(
        "/api/sessions",
        headers=_auth(t1),
        json={"course_id": cid, "group_ids": [gid], "question_id": qid, "timer_seconds": 60, "title": "S1"},
    )
    assert created.status_code == 201, created.json
    sid = created.json["id"]

    qr = client.get(
        f"/api/sessions/{sid}/live-qr?port=5173",
        headers={**_auth(t1), "X-Frontend-Origin": "http://127.0.0.1:5173"},
    )
    assert qr.status_code == 200

    verified = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(s1),
        json={"code": qr.json["code"], "nonce": qr.json["nonce"], "device_id": "device-1"},
    )
    assert verified.status_code == 200, verified.json

    submitted = client.post(
        "/api/answers/submit",
        headers=_auth(s1),
        json={"session_code": qr.json["code"], "text": "ans", "device_id": "device-1"},
    )
    assert submitted.status_code == 201

    # Teacher2 should not see answers of teacher1 course session.
    answers = client.get(f"/api/sessions/{sid}/answers", headers=_auth(t2))
    assert answers.status_code == 403, answers.json


def test_freeze_qr_keeps_nonce_valid_until_session_end(client):
    t1 = _login(client, "t1", "p1")
    s1 = _login(client, "s1", "sp")

    groups = client.get("/api/groups", headers=_auth(t1))
    gid = groups.json[0]["id"]
    courses = client.get("/api/courses", headers=_auth(t1))
    cid = courses.json[0]["id"]

    with client.application.app_context():
        q = Question(
            text="Q freeze",
            course_id=cid,
            difficulty="easy",
            max_score=1,
            created_by=1,
        )
        _db.session.add(q)
        _db.session.commit()
        qid = q.id

    created = client.post(
        "/api/sessions",
        headers=_auth(t1),
        json={"course_id": cid, "group_ids": [gid], "question_id": qid},
    )
    assert created.status_code == 201
    sid = created.json["id"]

    frozen = client.post(
        f"/api/sessions/{sid}/freeze-qr?port=5173",
        headers={**_auth(t1), "X-Frontend-Origin": "http://127.0.0.1:5173"},
    )
    assert frozen.status_code == 200, frozen.json
    assert frozen.json.get("is_frozen") is True
    assert int(frozen.json.get("expires_in_seconds") or 0) >= 3600

    verified = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(s1),
        json={"code": frozen.json["code"], "nonce": frozen.json["nonce"], "device_id": "d-freeze"},
    )
    assert verified.status_code == 200, verified.json

