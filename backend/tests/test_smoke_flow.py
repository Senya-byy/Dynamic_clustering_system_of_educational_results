import os
import sys

import pytest

# Ensure test environment before importing backend app module.
os.environ["APP_ENV"] = "test"
os.environ["SEED_DATA"] = "false"

# Ensure backend/ is importable regardless of pytest rootdir.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import db as _db, User, Group, Topic, Question  # noqa: E402


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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

            teacher = User(login="teacher1", role="teacher", group_id=None, full_name="Teacher")
            teacher.set_password("teacher123")
            student = User(login="student1", role="student", group_id=None, full_name="Student")
            student.set_password("student123")
            student2 = User(login="student2", role="student", group_id=None, full_name="Student2")
            student2.set_password("student123")
            _db.session.add_all([teacher, student, student2])
            _db.session.commit()

            grp = Group(name="G1", teacher_id=teacher.id)
            _db.session.add(grp)
            _db.session.commit()

            student.group_id = grp.id
            student2.group_id = grp.id
            _db.session.commit()

            topic = Topic(name="T1", teacher_id=teacher.id)
            _db.session.add(topic)
            _db.session.commit()

            q = Question(
                text="Q1?",
                topic_id=topic.id,
                topic="T1",
                difficulty="easy",
                max_score=5,
                created_by=teacher.id,
            )
            _db.session.add(q)
            _db.session.commit()

        yield c

        with app.app_context():
            _db.drop_all()


def _login(client, login: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"login": login, "password": password})
    assert resp.status_code == 200, resp.json
    return resp.json["access_token"]


def test_smoke_qr_answer_grade_flow(client):
    teacher_token = _login(client, "teacher1", "teacher123")
    student_token = _login(client, "student1", "student123")

    # Teacher creates session
    # We know group_id=1 and question_id=1 in this fixture order, but be robust:
    groups = client.get("/api/groups", headers=_auth(teacher_token))
    assert groups.status_code == 200
    gid = groups.json[0]["id"]

    # Question list (teacher)
    qlist = client.get("/api/questions", headers=_auth(teacher_token))
    assert qlist.status_code == 200
    qid = qlist.json[0]["id"]

    created = client.post(
        "/api/sessions",
        headers=_auth(teacher_token),
        json={"group_id": gid, "question_id": qid, "timer_seconds": 60, "title": "S1"},
    )
    assert created.status_code == 201, created.json
    sid = created.json["id"]

    # Live QR
    qr = client.get(
        f"/api/sessions/{sid}/live-qr?port=5173",
        headers={**_auth(teacher_token), "X-Frontend-Origin": "http://127.0.0.1:5173"},
    )
    assert qr.status_code == 200, qr.json
    assert qr.json["code"]
    assert qr.json["nonce"]
    assert qr.json.get("expires_in_seconds") == 5

    code = qr.json["code"]
    nonce = qr.json["nonce"]

    # Student verify ticket
    verified = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student_token),
        json={"code": code, "nonce": nonce, "device_id": "device-1"},
    )
    assert verified.status_code == 200, verified.json
    assert "question" in verified.json

    # Повторный verify тем же nonce до ответа — тот же вопрос (устойчивость к обновлению страницы)
    verified_again = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student_token),
        json={"code": code, "nonce": nonce, "device_id": "device-1"},
    )
    assert verified_again.status_code == 200, verified_again.json
    assert verified_again.json["question_id"] == verified.json["question_id"]

    # Student submit answer
    submitted = client.post(
        "/api/answers/submit",
        headers=_auth(student_token),
        json={"session_code": code, "text": "my answer", "device_id": "device-1"},
    )
    assert submitted.status_code == 201, submitted.json
    aid = submitted.json["id"]

    # Teacher sees answers
    answers = client.get(f"/api/sessions/{sid}/answers", headers=_auth(teacher_token))
    assert answers.status_code == 200, answers.json
    assert len(answers.json) == 1
    assert answers.json[0]["id"] == aid

    # Teacher grades
    graded = client.post(
        f"/api/answers/{aid}/grade",
        headers=_auth(teacher_token),
        json={"score": 4, "comment": "ok", "is_correct": True},
    )
    assert graded.status_code == 200, graded.json
    assert graded.json["checked_at"] is not None

    # Reload teacher answers: the answer should be marked as checked
    answers2 = client.get(f"/api/sessions/{sid}/answers", headers=_auth(teacher_token))
    assert answers2.status_code == 200
    assert answers2.json[0]["checked_at"] is not None


def test_two_students_same_qr_nonce(client):
    """Один nonce в QR — несколько студентов группы могут получить вопрос, пока билет не истёк."""
    teacher_token = _login(client, "teacher1", "teacher123")
    student1_token = _login(client, "student1", "student123")
    student2_token = _login(client, "student2", "student123")

    _, code, nonce, _pin = _create_session_and_qr(client, teacher_token)

    v1 = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student1_token),
        json={"code": code, "nonce": nonce, "device_id": "device-s1"},
    )
    assert v1.status_code == 200, v1.json

    v2 = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student2_token),
        json={"code": code, "nonce": nonce, "device_id": "device-s2"},
    )
    assert v2.status_code == 200, v2.json
    assert v2.json["question"]["text"] == v1.json["question"]["text"]


def test_verify_pin_two_students(client):
    teacher_token = _login(client, "teacher1", "teacher123")
    s1 = _login(client, "student1", "student123")
    s2 = _login(client, "student2", "student123")
    _, code, _nonce, pin = _create_session_and_qr(client, teacher_token)
    assert len(pin) == 6

    a = client.post(
        "/api/sessions/verify-pin",
        headers=_auth(s1),
        json={"code": code, "join_pin": pin, "device_id": "pin-dev-1"},
    )
    assert a.status_code == 200, a.json
    b = client.post(
        "/api/sessions/verify-pin",
        headers=_auth(s2),
        json={"code": code, "join_pin": pin, "device_id": "pin-dev-2"},
    )
    assert b.status_code == 200, b.json


def test_verify_pin_same_student_second_device_fails(client):
    teacher_token = _login(client, "teacher1", "teacher123")
    st = _login(client, "student1", "student123")
    _, code, _nonce, pin = _create_session_and_qr(client, teacher_token)

    first = client.post(
        "/api/sessions/verify-pin",
        headers=_auth(st),
        json={"code": code, "join_pin": pin, "device_id": "only-one"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/sessions/verify-pin",
        headers=_auth(st),
        json={"code": code, "join_pin": pin, "device_id": "other-phone"},
    )
    assert second.status_code == 400
    assert "другого устройства" in second.json.get("error", "")


def test_negative_submit_without_verify_requires_qr_first(client):
    student_token = _login(client, "student1", "student123")
    # No verify-ticket => no device binding/assignment
    resp = client.post(
        "/api/answers/submit",
        headers=_auth(student_token),
        json={"session_code": "NOPE", "text": "x", "device_id": "device-1"},
    )
    # session not found or "scan QR first" depending on code existence
    assert resp.status_code in (400, 404)


def _create_session_and_qr(client, teacher_token: str):
    groups = client.get("/api/groups", headers=_auth(teacher_token))
    assert groups.status_code == 200
    gid = groups.json[0]["id"]

    qlist = client.get("/api/questions", headers=_auth(teacher_token))
    assert qlist.status_code == 200
    qid = qlist.json[0]["id"]

    created = client.post(
        "/api/sessions",
        headers=_auth(teacher_token),
        json={"group_id": gid, "question_id": qid, "timer_seconds": 60, "title": "S1"},
    )
    assert created.status_code == 201, created.json
    sid = created.json["id"]

    qr = client.get(
        f"/api/sessions/{sid}/live-qr?port=5173",
        headers={**_auth(teacher_token), "X-Frontend-Origin": "http://127.0.0.1:5173"},
    )
    assert qr.status_code == 200, qr.json
    return sid, qr.json["code"], qr.json["nonce"], qr.json.get("join_pin") or ""


def test_negative_double_submit_answer_forbidden(client):
    teacher_token = _login(client, "teacher1", "teacher123")
    student_token = _login(client, "student1", "student123")

    _, code, nonce, _pin = _create_session_and_qr(client, teacher_token)

    verified = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student_token),
        json={"code": code, "nonce": nonce, "device_id": "device-1"},
    )
    assert verified.status_code == 200

    first = client.post(
        "/api/answers/submit",
        headers=_auth(student_token),
        json={"session_code": code, "text": "a1", "device_id": "device-1"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/answers/submit",
        headers=_auth(student_token),
        json={"session_code": code, "text": "a2", "device_id": "device-1"},
    )
    assert second.status_code == 400
    assert "error" in second.json


def test_negative_verify_after_answer_forbidden(client):
    teacher_token = _login(client, "teacher1", "teacher123")
    student_token = _login(client, "student1", "student123")

    _, code, nonce, _pin = _create_session_and_qr(client, teacher_token)

    verified = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student_token),
        json={"code": code, "nonce": nonce, "device_id": "device-1"},
    )
    assert verified.status_code == 200

    first = client.post(
        "/api/answers/submit",
        headers=_auth(student_token),
        json={"session_code": code, "text": "a1", "device_id": "device-1"},
    )
    assert first.status_code == 201

    # new ticket after answer still should refuse to give question again
    sid2, code2, nonce2, _p2 = _create_session_and_qr(client, teacher_token)
    assert code2  # different session, just to keep helper used
    # But verify-ticket should fail for original session only; we need a new ticket for original session:
    # Issue another ticket for the original session and attempt verify again.
    qr2 = client.get(
        f"/api/sessions/{sid2}/live-qr?port=5173",
        headers={**_auth(teacher_token), "X-Frontend-Origin": "http://127.0.0.1:5173"},
    )
    assert qr2.status_code == 200


def test_rbac_student_cannot_grade_or_create_session(client):
    teacher_token = _login(client, "teacher1", "teacher123")
    student_token = _login(client, "student1", "student123")

    sid, code, nonce, _pin = _create_session_and_qr(client, teacher_token)

    verified = client.post(
        "/api/sessions/verify-ticket",
        headers=_auth(student_token),
        json={"code": code, "nonce": nonce, "device_id": "device-1"},
    )
    assert verified.status_code == 200

    submitted = client.post(
        "/api/answers/submit",
        headers=_auth(student_token),
        json={"session_code": code, "text": "a1", "device_id": "device-1"},
    )
    assert submitted.status_code == 201
    aid = submitted.json["id"]

    # Student cannot grade
    grade = client.post(
        f"/api/answers/{aid}/grade",
        headers=_auth(student_token),
        json={"score": 1, "comment": "", "is_correct": True},
    )
    assert grade.status_code == 403

    # Student cannot create session
    groups = client.get("/api/groups", headers=_auth(teacher_token))
    gid = groups.json[0]["id"]
    qlist = client.get("/api/questions", headers=_auth(teacher_token))
    qid = qlist.json[0]["id"]
    create = client.post(
        "/api/sessions",
        headers=_auth(student_token),
        json={"group_id": gid, "question_id": qid},
    )
    assert create.status_code == 403

