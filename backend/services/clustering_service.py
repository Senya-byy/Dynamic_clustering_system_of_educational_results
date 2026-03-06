# backend/services/clustering_service.py
"""Признаки студентов и k-means (StandardScaler + выбор k по силуэту)."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np

from models import Answer, Attendance, Question, Session, User


def _standard_scale(X: np.ndarray) -> np.ndarray:
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std = np.where(std < 1e-9, 1.0, std)
    return (X - mean) / std


def _pairwise_euclidean(X: np.ndarray) -> np.ndarray:
    """Квадраты расстояний ||x_i - x_j||^2, форма (n, n)."""
    a2 = np.sum(X * X, axis=1, keepdims=True)
    return np.maximum(a2 + a2.T - 2 * (X @ X.T), 0.0)


def _kmeans_labels(
    X: np.ndarray,
    k: int,
    *,
    random_state: int = 42,
    n_init: int = 10,
    max_iter: int = 200,
) -> np.ndarray:
    """K-means (Ллойд) только на NumPy, без sklearn/pandas."""
    n, d = X.shape
    rng = np.random.RandomState(random_state)
    best_inertia = np.inf
    best_labels: np.ndarray | None = None
    for _ in range(n_init):
        cent_idx = rng.choice(n, size=k, replace=False)
        centroids = X[cent_idx].copy()
        labels = np.zeros(n, dtype=np.int32)
        for _ in range(max_iter):
            dists = np.sum((X[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2, axis=2)
            labels = np.argmin(dists, axis=1).astype(np.int32)
            new_c = np.zeros_like(centroids)
            for j in range(k):
                mask = labels == j
                if np.any(mask):
                    new_c[j] = X[mask].mean(axis=0)
                else:
                    new_c[j] = X[rng.randint(n)]
            if np.allclose(new_c, centroids, rtol=1e-5, atol=1e-8):
                centroids = new_c
                break
            centroids = new_c
        dists = np.sum((X[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2, axis=2)
        inertia = float(dists[np.arange(n), labels].sum())
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()
    return best_labels if best_labels is not None else np.zeros(n, dtype=np.int32)


def _silhouette_mean(X: np.ndarray, labels: np.ndarray) -> float:
    """Средний коэффициент силуэта (евклидова метрика)."""
    n = X.shape[0]
    uniq = np.unique(labels)
    if len(uniq) < 2 or n < 2:
        return -1.0
    dist = np.sqrt(_pairwise_euclidean(X))
    scores: List[float] = []
    for i in range(n):
        li = labels[i]
        same = (labels == li) & (np.arange(n) != i)
        if np.any(same):
            a = float(dist[i, same].mean())
        else:
            a = 0.0
        others = [c for c in uniq if c != li]
        b_min = np.inf
        for c in others:
            mask = labels == c
            if np.any(mask):
                b_min = min(b_min, float(dist[i, mask].mean()))
        if not np.isfinite(b_min):
            continue
        den = max(a, b_min)
        scores.append(0.0 if den < 1e-12 else (b_min - a) / den)
    return float(np.mean(scores)) if scores else -1.0

FEATURE_KEYS: List[str] = [
    'total_score',
    'avg_score',
    'max_answer_score',
    'count_above_half_max',
    'late_count',
    'share_passed_70',
    'easy_pass',
    'easy_fail',
    'medium_pass',
    'medium_fail',
    'hard_pass',
    'hard_fail',
]

FEATURE_LABELS_RU: Dict[str, str] = {
    'total_score': 'Сумма баллов',
    'avg_score': 'Средний балл за ответ',
    'max_answer_score': 'Макс. балл за ответ',
    'count_above_half_max': 'Ответов > 50% от max_score',
    'late_count': 'Опоздания (сессии)',
    'share_passed_70': 'Доля зачтённых (>70% max или верно)',
    'easy_pass': 'Лёгкие — зачтено',
    'easy_fail': 'Лёгкие — не зачтено',
    'medium_pass': 'Средние — зачтено',
    'medium_fail': 'Средние — не зачтено',
    'hard_pass': 'Сложные — зачтено',
    'hard_fail': 'Сложные — не зачтено',
}


def _norm_difficulty(raw: str | None) -> str:
    if not raw:
        return 'unknown'
    x = raw.lower().strip()
    if x in ('easy', 'легкая', 'легкий', 'легко'):
        return 'easy'
    if x in ('medium', 'средняя', 'средний', 'средне'):
        return 'medium'
    if x in ('hard', 'сложная', 'сложный', 'сложно'):
        return 'hard'
    if 'легк' in x:
        return 'easy'
    if 'сред' in x:
        return 'medium'
    if 'слож' in x:
        return 'hard'
    return 'unknown'


def _graded_passed(ans: Answer, q: Question | None) -> bool | None:
    if ans.score is None or not q:
        return None
    if ans.is_correct is True:
        return True
    if ans.is_correct is False:
        return False
    return ans.score > 0.7 * (q.max_score or 0)


def _above_half_max(ans: Answer, q: Question | None) -> bool:
    if ans.score is None or not q or not q.max_score:
        return False
    return ans.score > 0.5 * q.max_score


def build_group_answers_index(
    group_id: int,
) -> Tuple[set[int], dict[int, Session], dict[int, List[Answer]]]:
    """session_ids, кэш сессий группы, ответы по student_id."""
    sessions = Session.query.filter_by(group_id=group_id).all()
    session_ids = {s.id for s in sessions}
    sess_by_id = {s.id: s for s in sessions}
    if not session_ids:
        return session_ids, sess_by_id, {}
    rows = (
        Answer.query.join(Session, Answer.session_id == Session.id)
        .filter(Session.group_id == group_id)
        .all()
    )
    by_student: dict[int, List[Answer]] = defaultdict(list)
    for a in rows:
        by_student[a.student_id].append(a)
    return session_ids, sess_by_id, by_student


def _late_session_count(
    student_id: int,
    session_ids: set[int],
    group_answers: List[Answer],
) -> int:
    if not session_ids:
        return 0
    late_sessions: set[int] = set()
    att_rows = (
        Attendance.query.filter(
            Attendance.student_id == student_id,
            Attendance.session_id.in_(session_ids),
        )
        .all()
    )
    for att in att_rows:
        if (att.status or '').lower() == 'late':
            late_sessions.add(att.session_id)
    for ans in group_answers:
        if ans.session_id in session_ids and ans.is_late:
            late_sessions.add(ans.session_id)
    return len(late_sessions)


def build_feature_matrix(group_id: int, student_ids: List[int]) -> List[List[float]]:
    """Вектор признаков на студента (порядок = FEATURE_KEYS)."""
    session_ids, sess_by_id, answers_by = build_group_answers_index(group_id)
    n_feat = len(FEATURE_KEYS)
    raw_rows: List[List[float]] = []

    questions_cache: dict[int, Question | None] = {}

    def get_q(qid: int | None) -> Question | None:
        if qid is None:
            return None
        if qid not in questions_cache:
            questions_cache[qid] = Question.query.get(qid)
        return questions_cache[qid]

    for sid in student_ids:
        answers = answers_by.get(sid, [])
        total = 0.0
        scores: List[int] = []
        max_sc = 0
        n_half = 0
        graded = 0
        passed = 0
        easy_p = easy_f = med_p = med_f = hard_p = hard_f = 0

        for ans in answers:
            sess = sess_by_id.get(ans.session_id)
            qid = ans.question_id or (sess.question_id if sess else None)
            q = get_q(qid)
            if ans.score is not None:
                total += ans.score
                scores.append(ans.score)
                max_sc = max(max_sc, ans.score)
                graded += 1
                if _above_half_max(ans, q):
                    n_half += 1
                gp = _graded_passed(ans, q)
                if gp is True:
                    passed += 1
                d = _norm_difficulty(q.difficulty if q else None)
                if gp is not None and d != 'unknown':
                    if d == 'easy':
                        if gp:
                            easy_p += 1
                        else:
                            easy_f += 1
                    elif d == 'medium':
                        if gp:
                            med_p += 1
                        else:
                            med_f += 1
                    elif d == 'hard':
                        if gp:
                            hard_p += 1
                        else:
                            hard_f += 1

        avg = sum(scores) / len(scores) if scores else 0.0
        share70 = passed / graded if graded else 0.0
        late_c = _late_session_count(sid, session_ids, answers)

        vec = [
            float(total),
            float(avg),
            float(max_sc),
            float(n_half),
            float(late_c),
            float(share70),
            float(easy_p),
            float(easy_f),
            float(med_p),
            float(med_f),
            float(hard_p),
            float(hard_f),
        ]
        raw_rows.append(vec)

    return raw_rows


def _choose_k(X_scaled: np.ndarray, n_samples: int) -> int:
    if n_samples < 3:
        raise ValueError('Для кластеризации нужно не менее 3 студентов в группе')
    if n_samples == 3:
        return 3
    best_k = 3
    best_score = -1.0
    upper = min(8, n_samples - 1)
    for k in range(3, upper + 1):
        if k >= n_samples:
            break
        labels = _kmeans_labels(X_scaled, k, random_state=42, n_init=10)
        if len(np.unique(labels)) < 2:
            continue
        sc = _silhouette_mean(X_scaled, labels)
        if sc > best_score:
            best_score = sc
            best_k = k
    return best_k


def _final_labels(X_raw: np.ndarray, k: int) -> np.ndarray:
    Xs = _standard_scale(X_raw)
    return _kmeans_labels(Xs, k, random_state=42, n_init=15)


def cluster_payload_for_group(
    group_id: int,
    students: List[User],
) -> Dict[str, Any]:
    """
    Выполняет кластеризацию без сохранения в БД.
    students — список студентов группы (role=student).
    """
    student_ids = [s.id for s in students]
    n = len(student_ids)
    if n < 3:
        raise ValueError('Для кластеризации нужно не менее 3 студентов в группе')

    raw_rows = build_feature_matrix(group_id, student_ids)
    X = np.asarray(raw_rows, dtype=np.float64)
    X_scaled = _standard_scale(X)
    k = _choose_k(X_scaled, n)
    labels = _final_labels(X, k)

    clusters_map: dict[int, List[int]] = defaultdict(list)
    for idx, lab in enumerate(labels.tolist()):
        clusters_map[int(lab)].append(idx)

    n_dim = len(FEATURE_KEYS)
    clusters_out: List[dict] = []
    for lab in sorted(clusters_map.keys()):
        idxs = clusters_map[lab]
        sums = [0.0] * n_dim
        for i in idxs:
            row = raw_rows[i]
            for j in range(n_dim):
                sums[j] += row[j]
        denom = len(idxs)
        mean_dict = {FEATURE_KEYS[j]: round(sums[j] / denom, 4) for j in range(n_dim)}
        member_ids = [student_ids[i] for i in idxs]
        member_names = [students[i].full_name or students[i].login for i in idxs]
        clusters_out.append({
            'label': lab,
            'student_ids': member_ids,
            'student_names': member_names,
            'size': len(idxs),
            'mean_features': mean_dict,
        })

    assignments = []
    for i, sid in enumerate(student_ids):
        assignments.append({
            'student_id': sid,
            'cluster_label': int(labels[i]),
            'feature_vector': raw_rows[i],
        })

    labels_arr = np.asarray(labels, dtype=np.int32)
    uniq = np.unique(labels_arr)
    if len(uniq) >= 2:
        silhouette = float(_silhouette_mean(X_scaled, labels_arr))
    else:
        silhouette = 0.0

    return {
        'n_clusters': k,
        'silhouette_score': round(silhouette, 4),
        'feature_keys': FEATURE_KEYS,
        'feature_labels': {fk: FEATURE_LABELS_RU.get(fk, fk) for fk in FEATURE_KEYS},
        'clusters': clusters_out,
        'assignments': assignments,
        'summary_ru': _human_summary(clusters_out, k),
    }


def _human_summary(clusters: List[dict], k: int) -> str:
    sizes = [c['size'] for c in clusters]
    parts = [
        f'Автоматически выбрано k={k} по методу силуэта (не менее 3 кластеров).',
        f'Размеры кластеров: {", ".join(str(s) for s in sorted(sizes, reverse=True))} студ.',
    ]
    return ' '.join(parts)
