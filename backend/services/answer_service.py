# backend/services/answer_service.py
from repositories.answer_repository import AnswerRepository
from repositories.attendance_repository import AttendanceRepository
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from models import Group, Question
from datetime import datetime
from typing import Dict, List, Optional


class AnswerService:
    def __init__(self):
        self.answer_repo = AnswerRepository()
        self.attendance_repo = AttendanceRepository()
        self.session_repo = SessionRepository()
        self.user_repo = UserRepository()

    def submit_answer(self, student_id: int, session_code: str, text: str) -> Dict:
        sess = self.session_repo.find_by_code(session_code)
        if not sess or not sess.is_active:
            raise ValueError('Сессия не активна или не найдена')

        if self.answer_repo.find_by_session_student(sess.id, student_id):
            raise ValueError('Ответ уже отправлен')

        if sess.timer_seconds:
            elapsed = (datetime.utcnow() - sess.start_time).total_seconds()
            is_late = elapsed > sess.timer_seconds
        else:
            is_late = False

        answer = self.answer_repo.create({
            'session_id': sess.id,
            'student_id': student_id,
            'text': text,
            'is_late': is_late,
        })
        status = 'late' if is_late else 'present'
        self.attendance_repo.mark_present(student_id, sess.id, status)
        return {
            'id': answer.id,
            'submitted_at': answer.submitted_at.isoformat(),
            'is_late': is_late,
        }

    def grade_answer(
        self,
        answer_id: int,
        score: int,
        comment: str,
        checker_id: int,
        is_correct: Optional[bool] = None,
    ) -> Dict:
        ans = self.answer_repo.update_score(
            answer_id, score, comment, checker_id, is_correct=is_correct
        )
        return {
            'id': ans.id,
            'score': ans.score,
            'comment': ans.comment,
            'is_correct': ans.is_correct,
            'checked_by': ans.checked_by,
            'checked_at': ans.checked_at.isoformat() if ans.checked_at else None,
        }

    def get_answers_for_session(self, session_id: int, teacher_id: int) -> List[dict]:
        sess = self.session_repo.find_by_id(session_id)
        if not sess:
            return []
        group = Group.query.get(sess.group_id)
        u = self.user_repo.find_by_id(teacher_id)
        is_admin = u and u.role == 'admin'
        if not group or (group.teacher_id != teacher_id and not is_admin):
            raise PermissionError('Нет доступа к этой сессии')
        question = Question.query.get(sess.question_id)
        max_score = question.max_score if question else 10
        answers = self.answer_repo.find_by_session(session_id)
        result = []
        for a in answers:
            student = self.user_repo.find_by_id(a.student_id)
            result.append({
                'id': a.id,
                'student_name': student.full_name or student.login if student else '',
                'text': a.text,
                'score': a.score,
                'is_correct': a.is_correct,
                'comment': a.comment,
                'submitted_at': a.submitted_at.isoformat(),
                'is_late': a.is_late,
                'max_score': max_score,
            })
        return result

    def get_student_answers_with_feedback(self, student_id: int) -> List[dict]:
        answers = self.answer_repo.find_by_student(student_id)
        result = []
        for a in answers:
            sess = self.session_repo.find_by_id(a.session_id)
            question = Question.query.get(sess.question_id) if sess else None
            result.append({
                'id': a.id,
                'question_text': question.text if question else None,
                'max_score': question.max_score if question else 0,
                'difficulty': question.difficulty if question else None,
                'correct_answer': question.correct_answer if question else None,
                'student_answer': a.text,
                'score': a.score,
                'is_correct': a.is_correct,
                'comment': a.comment,
                'checked_at': a.checked_at.isoformat() if a.checked_at else None,
            })
        return result
