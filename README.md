# ClassQR — Dynamic clustering system of educational results

Web‑система для проведения опросов/занятий через динамический QR, проверки ответов и аналитики студентов (включая кластеризацию и динамику переходов).

## Быстрый старт (dev)

### Требования
- Python 3.10+
- Node.js 18+ (рекомендуется 20)

### 1) Установка зависимостей

Backend:
```bash
cd backend
pip3 install -r requirements.txt
```

Frontend:
```bash
cd frontend
npm install
```

### 2) Запуск одной командой (macOS/Linux)
```bash
./scripts/dev.sh
```

### 2.1) Windows
```bat
scripts\dev.bat
```

Скрипт выведет **LAN URL** (например `http://192.168.1.37:5173`) — именно его нужно использовать, чтобы QR открывался на телефоне.

## Запуск через Docker
1) Создайте `.env`:
```bash
cp .env.example .env
```
2) Обновите `QR_FRONTEND_ORIGIN` под ваш IP.
3) Запуск:
```bash
docker compose up --build
```

## Деплой (Render)
Если деплоите на Render (frontend + backend + DB):
- backend: Render Web Service (желательно с Postgres вместо SQLite)
- frontend: Render **Static Site**
- важно для SPA (Vue Router `createWebHistory()`): добавьте правило **Redirects/Rewrites**  
  `/*` → `/index.html` (**Rewrite**), иначе при обновлении страницы будет 404.

См. [`docs/DEPLOY_RENDER.md`](docs/DEPLOY_RENDER.md).

## Документация
Файлы в `docs/`:
- `ARCHITECTURE_PROJECT.md` — архитектура, API, QR/LAN, кластеризация, миграции
- `PLAN_45_DAYS_TEAM.md` — план на 45 дней (тимлид/архитектор/тестировщик)
- `RUNBOOK_QR.md` — пошаговая проверка QR в production (Render)
- `API_EXAMPLES.md` — curl и примеры JSON
- `CHECKLIST_RELEASE.md` — регресс перед релизом
- `CHECKLIST_MOBILE_PROD.md` — мобильный чек-лист (production)
- `MIN_TESTS.md` — минимальные автотесты (план)
- `DEPLOY_RENDER.md` — деплой на Render (frontend static + backend + DB)
- `TESTING_MANUAL_STATIC.md` — статическое и ручное динамическое тестирование

## Бейджи
- Status: `active (edu)`
- Version: `v1.0 (target)`

