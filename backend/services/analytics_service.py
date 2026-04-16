# backend/services/analytics_service.py
from collections import defaultdict
from datetime import datetime
from repositories.group_repository import GroupRepository
from repositories.session_repository import SessionRepository
from repositories.answer_repository import AnswerRepository
from repositories.user_repository import UserRepository
from models import Question, Session


def _submitted(a):
    return a.submitted_at or datetime(1970, 1, 1)


class AnalyticsService:
    def __init__(self):
        self.group_repo = GroupRepository()
        self.session_repo = SessionRepository()
        self.answer_repo = AnswerRepository()
        self.user_repo = UserRepository()

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
            qid = sess.question_id
            for ans in self.answer_repo.find_by_session(sess.id):
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

        hist = defaultdict(int)
        for s in sessions:
            for ans in self.answer_repo.find_by_session(s.id):
                if ans.score is not None:
                    hist[int(ans.score)] += 1

        return {
            'group_id': group_id,
            'sessions_count': len(sessions),
            'questions_breakdown': breakdown,
            'easiest_questions': easiest,
            'hardest_questions': hardest,
            'student_cards': student_cards,
            'score_histogram': dict(sorted(hist.items())),
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
            q = Question.query.get(sess.question_id) if sess else None
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
