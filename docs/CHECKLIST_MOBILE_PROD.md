# CHECKLIST_MOBILE_PROD — тестирование на телефонах (production)

## Устройства/браузеры
- iOS: Safari
- Android: Chrome

## Предусловия
- Система доступна по публичному URL (Render):
  - frontend (пример): `https://classqr-frontend.onrender.com`
  - backend (Render Web Service)
- На frontend настроен SPA rewrite `/* → /index.html` (Rewrite).

## Чек-лист
1) Открыть на телефоне `https://classqr-frontend.onrender.com` — SPA загружается.
2) Обновить страницу (F5/Reload) на внутренних роутами (например `/login`, `/teacher/check`) — не должно быть `Not Found`.
3) Войти студентом и убедиться, что API работает (нет CORS ошибок в DevTools).
4) С преподавательского устройства включить «Живой QR».
5) Сканировать QR телефоном (камера/сканер).
6) Должна открыться ссылка `https://classqr-frontend.onrender.com/join?...` (НЕ `localhost`).
7) Verify-ticket проходит, отображается вопрос.
8) Повторно открыть тот же QR через 5–10 секунд → должно быть «QR просрочен».
9) Отправить ответ; затем повторная отправка должна быть запрещена.
10) Device binding: выйти из аккаунта студента, зайти под другим студентом и открыть QR той же сессии → ожидаем ошибку «устройство привязано к другому аккаунту».

## Диагностика (если не работает)
- Проверить правило Render Redirects/Rewrites: `/* → /index.html` (Rewrite).
- Проверить, что backend healthcheck отвечает: `GET /health`.
- Проверить `CORS_ORIGINS` на backend: должен включать frontend-домен.

