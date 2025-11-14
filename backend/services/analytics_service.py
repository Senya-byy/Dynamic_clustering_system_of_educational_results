# backend/services/analytics_service.py
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from repositories.group_repository import GroupRepository
from repositories.session_repository import SessionRepository
from repositories.answer_repository import AnswerRepository
from repositories.user_repository import UserRepository
from repositories.cluster_repository import ClusterRunRepository
from models import Question, Session, User
from services.clustering_service import (
    FEATURE_KEYS,
    FEATURE_LABELS_RU,
    build_group_answers_index,
    cluster_payload_for_group,
    _late_session_count,
)


def _submitted(a):
    return a.submitted_at or datetime(1970, 1, 1)


class AnalyticsService:
    def __init__(self):
        self.group_repo = GroupRepository()
        self.session_repo = SessionRepository()
        self.answer_repo = AnswerRepository()
        self.user_repo = UserRepository()
        self.cluster_repo = ClusterRunRepository()

    def _ensure_teacher_group(self, group_id: int, teacher_id: int, role: str) -> bool:
        g = self.group_repo.find_by_id(group_id)
        if not g:
            return False
        if role == 'admin':
            return True
        return g.teacher_id == teacher_id

    def get_group_stat(self, group_id: int, teacher_id: int, role: str) -> dict:
        if not self._ensure_teacher_group(group_id, teacher_id, role):
            raise PermissionError('Нет доступа к группе')
        sessions = self.session_repo.find_by_group(group_id)
        question_stats = defaultdict(lambda: {'scores': [], 'graded': 0, 'correct': 0})
        for sess in sessions:
            for ans in self.answer_repo.find_by_session(sess.id):
                qid = getattr(ans, 'question_id', None) or sess.question_id
                if ans.score is not None:
                    question_stats[qid]['graded'] += 1
                    question_stats[qid]['scores'].append(ans.score)
                    if ans.is_correct is True:
                        question_stats[qid]['correct'] += 1
                    elif ans.is_correct is None:
                        q = Question.query.get(qid)
                        mx = q.max_score if q else 0
                        if mx and ans.score >= mx:
                            question_stats[qid]['correct'] += 1

        breakdown = []
        for qid, st in question_stats.items():
            q = Question.query.get(qid)
            graded = st['graded']
            pct = round(100 * st['correct'] / graded, 1) if graded else 0
            avg = round(sum(st['scores']) / len(st['scores']), 2) if st['scores'] else 0
            text = q.text if q else ''
            if len(text) > 80:
                text = text[:80] + '…'
            breakdown.append({
                'question_id': qid,
                'text': text,
                'difficulty': q.difficulty if q else None,
                'graded_count': graded,
                'percent_correct': pct,
                'avg_score': avg,
            })
        breakdown.sort(key=lambda x: x['avg_score'])
        easiest = breakdown[-3:] if breakdown else []
        hardest = breakdown[:3] if breakdown else []

        students = self.user_repo.find_by_group(group_id)
        student_cards = []
        for s in students:
            answers = self.answer_repo.find_by_student(s.id)
            series = []
            for a in sorted(answers, key=_submitted):
                series.append({
                    'answer_id': a.id,
                    'score': a.score,
                    'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None,
                })
            student_cards.append({
                'student_id': s.id,
                'name': s.full_name or s.login,
                'results_timeline': series,
            })

        return {
            'group_id': group_id,
            'sessions_count': len(sessions),
            'questions_breakdown': breakdown,
            'easiest_questions': easiest,
            'hardest_questions': hardest,
            'student_cards': student_cards,
        }

    def get_group_students_metrics(self, group_id: int, teacher_id: int, role: str) -> dict:
        if not self._ensure_teacher_group(group_id, teacher_id, role):
            raise PermissionError('Нет доступа к группе')
        sessions = self.session_repo.find_by_group(group_id)
        session_ids, _, answers_by = build_group_answers_index(group_id)
        students = self.user_repo.find_by_group(group_id)
        students.sort(key=lambda u: (u.full_name or u.login or '').lower())
        rows = []
        for s in students:
            answers = answers_by.get(s.id, [])
            graded = [a for a in answers if a.score is not None]
            total = sum(a.score for a in graded)
            n_graded = len(graded)
            avg = round(total / n_graded, 2) if n_graded else 0.0
            late = _late_session_count(s.id, session_ids, answers)
            rows.append({
                'student_id': s.id,
                'name': s.full_name or s.login,
                'total_score': float(total),
                'avg_score': avg,
                'answers_count': len(answers),
                'late_count': late,
            })
        return {
            'group_id': group_id,
            'sessions_count': len(sessions),
            'students': rows,
        }

    def get_student_stat(self, student_id: int, viewer_id: int, role: str) -> dict:
        student = self.user_repo.find_by_id(student_id)
        if not student:
            raise ValueError('Студент не найден')
        if role == 'student' and student_id != viewer_id:
            raise PermissionError('Доступ запрещён')
        if role == 'teacher':
            g = self.group_repo.find_by_id(student.group_id) if student.group_id else None
            if not g or g.teacher_id != viewer_id:
                raise PermissionError('Студент не из ваших групп')
        answers = self.answer_repo.find_by_student(student_id)
        timeline = []
        for a in sorted(answers, key=_submitted):
            sess = Session.query.get(a.session_id)
            qid = getattr(a, 'question_id', None)
            if qid is None and sess:
                qid = sess.question_id
            q = Question.query.get(qid) if qid else None
            timeline.append({
                'date': a.submitted_at.isoformat() if a.submitted_at else None,
                'topic': q.topic if q else None,
                'score': a.score,
                'max_score': q.max_score if q else None,
                'difficulty': q.difficulty if q else None,
            })
        return {
            'student_id': student_id,
            'name': student.full_name or student.login,
            'timeline': timeline,
        }

    def run_clustering(self, group_id: int, teacher_id: int, role: str) -> dict:
        if not self._ensure_teacher_group(group_id, teacher_id, role):
            raise PermissionError('Нет доступа к группе')
        students = self.user_repo.find_by_group(group_id)
        payload = cluster_payload_for_group(group_id, students)
        run = self.cluster_repo.create_run(
            group_id,
            payload['n_clusters'],
            payload['assignments'],
            silhouette_score=payload.get('silhouette_score'),
        )
        summaries = [
            {
                'label': c['label'],
                'size': c['size'],
                'mean_features': c['mean_features'],
            }
            for c in payload['clusters']
        ]
        return {
            'run': self._serialize_run(run),
            'n_clusters': payload['n_clusters'],
            'silhouette_score': payload.get('silhouette_score'),
            'feature_keys': payload['feature_keys'],
            'feature_labels': payload['feature_labels'],
            'cluster_summaries': summaries,
            'summary_ru': payload['summary_ru'],
        }

    def list_cluster_runs(self, group_id: int, teacher_id: int, role: str) -> List[dict]:
        if not self._ensure_teacher_group(group_id, teacher_id, role):
            raise PermissionError('Нет доступа к группе')
        runs = self.cluster_repo.list_runs_for_group(group_id)
        return [self._serialize_run(r, with_distribution=True) for r in runs]

    def get_cluster_transitions(self, group_id: int, teacher_id: int, role: str) -> dict:
        if not self._ensure_teacher_group(group_id, teacher_id, role):
            raise PermissionError('Нет доступа к группе')
        runs = self.cluster_repo.list_runs_for_group(group_id)
        students = self.user_repo.find_by_group(group_id)
        students.sort(key=lambda u: (u.full_name or u.login or '').lower())
        sid_order = [s.id for s in students]
        name_by_id = {s.id: (s.full_name or s.login) for s in students}

        run_metas = []
        run_ids: List[int] = []
        per_run_labels: Dict[int, Dict[int, int]] = {}

        for r in runs:
            run_ids.append(r.id)
            run_metas.append(self._serialize_run(r, with_distribution=True))
            m: Dict[int, int] = {}
            for a in r.assignments:
                m[a.student_id] = a.cluster_label
            per_run_labels[r.id] = m

        matrix: List[List[Optional[int]]] = []
        for sid in sid_order:
            row = []
            for rid in run_ids:
                row.append(per_run_labels[rid].get(sid))
            matrix.append(row)

        latest_detail: Optional[dict] = None
        if runs:
            latest_detail = self._run_clusters_detail(runs[-1])

        return {
            'group_id': group_id,
            'runs': run_metas,
            'heatmap': {
                'student_ids': sid_order,
                'student_labels': [name_by_id[i] for i in sid_order],
                'run_ids': run_ids,
                'matrix': matrix,
            },
            'latest_run_detail': latest_detail,
        }

    def get_cluster_run_detail(
        self, group_id: int, run_id: int, teacher_id: int, role: str
    ) -> dict:
        if not self._ensure_teacher_group(group_id, teacher_id, role):
            raise PermissionError('Нет доступа к группе')
        run = self.cluster_repo.find_run(run_id)
        if not run or run.group_id != group_id:
            raise ValueError('Запуск не найден')
        return self._run_clusters_detail(run)

    @staticmethod
    def _serialize_run(run, with_distribution: bool = False) -> dict:
        row = {
            'id': run.id,
            'group_id': run.group_id,
            'created_at': run.created_at.isoformat() if run.created_at else None,
            'n_clusters': run.n_clusters,
        }
        if with_distribution:
            dist: dict[str, int] = {}
            for a in run.assignments:
                k = str(a.cluster_label)
                dist[k] = dist.get(k, 0) + 1
            row['distribution'] = dist
        if getattr(run, 'silhouette_score', None) is not None:
            row['silhouette_score'] = round(float(run.silhouette_score), 4)
        return row

    def _run_clusters_detail(self, run) -> dict:
        by_label: Dict[int, List] = defaultdict(list)
        for a in run.assignments:
            by_label[a.cluster_label].append(a)

        clusters_out: List[dict] = []
        _ids = list({x.student_id for x in run.assignments})
        if _ids:
            students_by_id = {u.id: u for u in User.query.filter(User.id.in_(_ids)).all()}
        else:
            students_by_id = {}

        for lab in sorted(by_label.keys()):
            assigns = by_label[lab]
            member_ids = [x.student_id for x in assigns]
            member_names = [
                (students_by_id[sid].full_name or students_by_id[sid].login)
                if sid in students_by_id
                else str(sid)
                for sid in member_ids
            ]
            vecs = []
            for x in assigns:
                v = self.cluster_repo.parse_features(x)
                if v and len(v) == len(FEATURE_KEYS):
                    vecs.append(v)
            if vecs:
                n_dim = len(FEATURE_KEYS)
                sums = [0.0] * n_dim
                for v in vecs:
                    for j in range(n_dim):
                        sums[j] += float(v[j])
                denom = len(vecs)
                mean_dict = {
                    FEATURE_KEYS[j]: round(sums[j] / denom, 4) for j in range(n_dim)
                }
            else:
                mean_dict = {k: 0.0 for k in FEATURE_KEYS}

            clusters_out.append({
                'label': lab,
                'student_ids': member_ids,
                'student_names': member_names,
                'size': len(assigns),
                'mean_features': mean_dict,
            })

        sil = getattr(run, 'silhouette_score', None)
        return {
            'run': self._serialize_run(run),
            'silhouette_score': round(float(sil), 4) if sil is not None else None,
            'feature_keys': FEATURE_KEYS,
            'feature_labels': {k: FEATURE_LABELS_RU.get(k, k) for k in FEATURE_KEYS},
            'clusters': clusters_out,
        }
