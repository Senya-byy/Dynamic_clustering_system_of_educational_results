# REPORT_DYNAMIC_TESTING — отчёт (динамическое тестирование)

Дата: 2026-04-27  
Проект: ClassQR  
Формат: запуск и проверка API/логики (smoke) локально через Flask test client и/или pytest

## 1) Цель
Проверить, что ключевые API сценарии работают:
- логин
- создание сессии преподавателем
- live-QR (nonce)
- verify-ticket студентом
- submit answer
- grade answer преподавателем

## 2) Окружение
- Backend: Flask `create_app()`
- DB: SQLite (test), создаётся в тестах
- Seed: отключён (`SEED_DATA=false`)

## 3) Результаты (ожидаемая матрица)
Статусы должны быть такими:
- `POST /api/auth/login`:
  - 200 при валидных кредах
  - 401 при неверном пароле
  - 400 при пустом теле
- `POST /api/sessions` (teacher):
  - 201 при корректном `group_id` и `question_id`
- `GET /api/sessions/<sid>/live-qr` (teacher):
  - 200 возвращает `{code, nonce, join_url, expires_in_seconds}`
- `POST /api/sessions/verify-ticket` (student):
  - 200 возвращает `{question, timer_seconds}`
- `POST /api/answers/submit` (student):
  - 201 возвращает `{id, submitted_at, is_late}`
- `POST /api/answers/<aid>/grade` (teacher):
  - 200 возвращает `{id, score, checked_at}`

## 4) Замечания
- Фактический прогон автосценариев выполнен через `pytest` (Flask test client, SQLite test DB).
- Результат прогона: **8 passed** (см. `backend/tests/test_auth.py`, `backend/tests/test_smoke_flow.py`).

