# MIN_TESTS — минимальные автотесты (план)

Цель: иметь минимальный **smoke** на backend, чтобы быстро ловить регресс ключевого сценария.

## 1) Инструмент
- Использовать `pytest`
- Тестовая БД: SQLite in-memory (`sqlite:///:memory:`)
- Flask test client

## 2) Как запускать
После добавления зависимостей:
```bash
cd backend
pytest -q
```

## 3) Минимальный smoke-сценарий (структура)

Проверяем цепочку:
1) login teacher
2) создать сессию
3) live-qr → получить join_url/nonce
4) login student
5) verify-ticket (получить question)
6) submit answer
7) teacher: get session answers
8) teacher: grade

## 4) Пример (псевдокод)
```python
def test_smoke_qr_flow(client, db):
    token_teacher = login(client, "teacher", "teacher123")
    sid = create_session(client, token_teacher, group_id=..., question_id=...)
    qr = client.get(f"/api/sessions/{sid}/live-qr?port=5173", headers=auth(token_teacher)).json
    token_student = login(client, "mstu01", "student123")
    payload = client.post("/api/sessions/verify-ticket", json={
        "code": qr["code"],
        "nonce": qr["nonce"],
        "device_id": "test-device",
    }, headers=auth(token_student)).json
    ans = client.post("/api/answers/submit", json={
        "session_code": qr["code"],
        "text": "answer",
        "device_id": "test-device",
    }, headers=auth(token_student)).json
    rows = client.get(f"/api/sessions/{sid}/answers", headers=auth(token_teacher)).json
    client.post(f"/api/answers/{rows[0]['id']}/grade", json={"score": 1, "comment": ""}, headers=auth(token_teacher))
```

## 5) Важно
Сейчас проект использует «ручные миграции» SQLite при старте. Для тестов удобнее:
- создавать app с тестовым конфигом,
- отключать seed по умолчанию,
- создавать фикстуры (teacher/group/student/question).

