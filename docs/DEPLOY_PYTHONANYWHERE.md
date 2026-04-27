## Деплой backend на PythonAnywhere (Flask)

Цель: поднять backend ClassQR на домене `https://SenyaByy.pythonanywhere.com`.

### 1) Загрузить код на Gitverse и склонировать на PythonAnywhere
- Запушь репозиторий в Gitverse (без `.env`, без базы `.db`).
- На PythonAnywhere в консоли:

```bash
git clone <gitverse_repo_url> classqr
cd classqr/backend
```

### 2) Виртуальное окружение и зависимости

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Переменные окружения (важно)
На PythonAnywhere можно задавать переменные окружения в **Web → Environment variables**.

Минимальный набор:
- `APP_ENV=production`
- `SEED_DATA=false`
- `SECRET_KEY=<случайная_строка>`
- `DATABASE_URL=sqlite:////home/<your_username>/classqr/backend/instance/classqr.db`
- `CORS_ALLOW_LAN=false`
- `CORS_ORIGINS=https://SenyaByy.pythonanywhere.com`
- `QR_FRONTEND_ORIGIN=https://SenyaByy.pythonanywhere.com`

Примечания:
- Для SQLite в production лучше хранить файл в домашней директории пользователя PythonAnywhere (см. путь выше).
- `SECRET_KEY` обязательно поменять (не использовать дефолт).

### 4) Настроить WSGI
В PythonAnywhere: **Web → WSGI configuration file**.

Укажи путь до проекта и WSGI-модуля:
- проект: `/home/<your_username>/classqr/backend`
- WSGI entrypoint: `backend/wsgi.py` уже добавлен в репозиторий.

Пример содержимого (если нужно вставить вручную):

```python
import sys
import os

project_dir = "/home/<your_username>/classqr/backend"
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

os.environ.setdefault("APP_ENV", "production")

from wsgi import application
```

### 5) Healthcheck
После перезапуска веб‑приложения проверь:
- `GET /health` должен вернуть `200` и `{"status":"ok", ...}`

### 6) Фронтенд
PythonAnywhere может раздавать статику, но текущий проект предполагает отдельный фронтенд (Vite build → static hosting).
Если фронтенд тоже будет на PythonAnywhere, нужно:\n
- собрать `frontend` (`npm run build`) и настроить Static files;\n
- либо раздавать фронтенд через отдельный hosting (а тут оставить только API).\n

