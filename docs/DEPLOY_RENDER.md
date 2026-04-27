# DEPLOY_RENDER — деплой на Render (frontend + backend + DB)

Цель: задеплоить ClassQR полностью на Render: **frontend (Static Site)** + **backend (Web Service)** + **PostgreSQL**.

## 1) Backend (Web Service)

- **Service type**: Web Service
- **Root directory**: `backend`
- **Start command**: `python app.py` (или через Docker, если так настроено)

### Переменные окружения (минимум)
- `APP_ENV=production`
- `SEED_DATA=false` (в проде обычно выключают автосид)
- `SECRET_KEY=...`
- `JWT_SECRET_KEY=...`
- `DATABASE_URL=<Render Postgres connection string>`
- `CORS_ORIGINS=https://<ваш-frontend>.onrender.com`
- `QR_FRONTEND_ORIGIN=https://<ваш-frontend>.onrender.com`

Проверка после деплоя:
- `GET /health` → `200` и `{"status":"ok", ...}`

## 2) Database (Render PostgreSQL)

Рекомендуется Postgres вместо SQLite (на хостинге SQLite-файл может быть непредсказуемо “эпhemeral”).

- Создайте Render PostgreSQL
- Скопируйте connection string в `DATABASE_URL` backend-сервиса

## 3) Frontend (Static Site)

- **Service type**: Static Site
- **Root directory**: `frontend`
- **Build command**: `npm ci && npm run build`
- **Publish directory**: `dist`

### Критично: SPA rewrites (иначе 404 при обновлении страниц)

Фронт использует `vue-router` в режиме history (`createWebHistory()`), поэтому на Render нужно включить rewrite всех путей на `index.html`:

В Render UI: **Redirects/Rewrites**:
- **Source**: `/*`
- **Destination**: `/index.html`
- **Action**: `Rewrite`

После этого обновление страниц типа `/teacher/sessions` перестанет давать `Not Found`.

