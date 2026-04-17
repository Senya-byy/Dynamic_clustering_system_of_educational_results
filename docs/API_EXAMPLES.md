# API_EXAMPLES — примеры запросов/ответов

Все примеры ниже предполагают:
- backend: `http://127.0.0.1:5001`
- frontend: проксирует `/api` на backend (в dev)

Если используете curl напрямую в backend — подставляйте base `http://127.0.0.1:5001/api`.

## 1) POST `/api/auth/login`

```bash
curl -s -X POST "http://127.0.0.1:5001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"login":"teacher","password":"teacher123"}'
```

```json
{
  "access_token": "JWT...",
  "role": "teacher",
  "user_id": 12,
  "group_id": null
}
```

## 2) GET `/api/sessions/teacher`

```bash
curl -s "http://127.0.0.1:5001/api/sessions/teacher" \
  -H "Authorization: Bearer $TOKEN"
```

```json
[
  { "id": 55, "code": "AB12CD", "group_id": 3, "is_active": true, "display_title": "Занятие - 17.04.2026..." }
]
```

## 3) GET `/api/sessions/{id}/live-qr`

```bash
curl -s "http://127.0.0.1:5001/api/sessions/55/live-qr?port=5173" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Frontend-Origin: http://192.168.1.37:5173"
```

```json
{
  "session_id": 55,
  "code": "AB12CD",
  "nonce": "nonce",
  "expires_in_seconds": 3,
  "join_url": "http://192.168.1.37:5173/join?code=AB12CD&nonce=...",
  "qr_code": "data:image/png;base64,..."
}
```

## 4) POST `/api/sessions/verify-ticket`

```bash
curl -s -X POST "http://127.0.0.1:5001/api/sessions/verify-ticket" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"AB12CD","nonce":"...","device_id":"device-123"}'
```

```json
{
  "id": 55,
  "code": "AB12CD",
  "question_id": 101,
  "question": { "text": "...", "topic": "...", "difficulty": "easy", "max_score": 5 }
}
```

## 5) POST `/api/answers/submit`

```bash
curl -s -X POST "http://127.0.0.1:5001/api/answers/submit" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_code":"AB12CD","text":"Мой ответ","device_id":"device-123"}'
```

```json
{ "id": 9001, "submitted_at": "2026-04-17T10:10:00.000000", "is_late": false }
```

## 6) POST `/api/answers/{id}/grade`

```bash
curl -s -X POST "http://127.0.0.1:5001/api/answers/9001/grade" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"score":4,"comment":"OK","is_correct":true}'
```

```json
{
  "id": 9001,
  "score": 4,
  "comment": "OK",
  "is_correct": true,
  "checked_by": 12,
  "checked_at": "2026-04-17T10:12:00.000000"
}
```

## 7) GET `/api/rating/group`

```bash
curl -s "http://127.0.0.1:5001/api/rating/group?group_id=3" \
  -H "Authorization: Bearer $TOKEN"
```

```json
[
  { "rank": 1, "user_id": 21, "name": "mstu21", "total_score": 42, "is_self": false, "is_hidden": false }
]
```

## 8) POST `/api/analytics/cluster/{group_id}`

```bash
curl -s -X POST "http://127.0.0.1:5001/api/analytics/cluster/3" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "run": { "id": 7, "group_id": 3, "created_at": "2026-04-17T10:20:00", "n_clusters": 4, "silhouette_score": 0.31 },
  "n_clusters": 4,
  "silhouette_score": 0.31,
  "cluster_summaries": [ { "label": 0, "size": 8, "mean_features": { "total_score": 31.5 } } ]
}
```

## 9) GET `/api/analytics/cluster/{group_id}/transitions`

```bash
curl -s "http://127.0.0.1:5001/api/analytics/cluster/3/transitions" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "group_id": 3,
  "runs": [ { "id": 7, "created_at": "...", "n_clusters": 4, "distribution": { "0": 8, "1": 10 } } ],
  "heatmap": { "student_ids": [1,2], "student_labels": ["mstu01","mstu02"], "run_ids": [7], "matrix": [[0],[1]] },
  "latest_run_detail": { "run": { "id": 7 }, "clusters": [ { "label": 0, "size": 8 } ] }
}
```

