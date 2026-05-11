# backend/services/answer_service.py
from repositories.answer_repository import AnswerRepository
from repositories.attendance_repository import AttendanceRepository
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from repositories.assignment_repository import AssignmentRepository
from repositories.device_binding_repository import DeviceBindingRepository
from models import Course, Question, Topic
from utils.device_key import normalize_device_key
from datetime import datetime
from typing import Dict, List, Optional


class AnswerService:
    def __init__(self):
        self.answer_repo = AnswerRepository()
        self.attendance_repo = AttendanceRepository()
        self.session_repo = SessionRepository()
        self.user_repo = UserRepository()
        self.assign_repo = AssignmentRepository()

    def submit_answer(
        self, student_id: int, session_code: str, text: str, device_key: str
    ) -> Dict:
        student_id = int(student_id)
        device_key = normalize_device_key(device_key)
        sess = self.session_repo.find_by_code(session_code)
        if not sess or not sess.is_active:
            raise ValueError('Сессия не активна или не найдена')

        if self.answer_repo.find_by_session_student(sess.id, student_id):
            raise ValueError('Ответ уже отправлен')

        bind = DeviceBindingRepository.find(sess.id, device_key)
        if not bind:
            raise ValueError('Сначала получите вопрос, отсканировав QR у преподавателя.')
        if bind.student_id != student_id:
            raise ValueError(
                'Это устройство привязано к другому аккаунту для этой пары. '
                'Выйдите и войдите под тем логином, с которого сканировали QR.'
            )

        assign = self.assign_repo.find(sess.id, student_id)
        if not assign:
            raise ValueError('Сначала получите вопрос, отсканировав QR у преподавателя.')

        if sess.timer_seconds:
            elapsed = (datetime.utcnow() - sess.start_time).total_seconds()
            is_late = elapsed > sess.timer_seconds
        else:
            is_late = False

        answer = self.answer_repo.create({
            'session_id': sess.id,
            'student_id': student_id,
            'question_id': assign.question_id,
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
        ans_row = self.answer_repo.find_by_id(answer_id)
        if not ans_row:
            raise ValueError("Ответ не найден")
        q = Question.query.get(ans_row.question_id)
        max_s = q.max_score if q else 0
        if score < 0 or score > max_s:
            raise ValueError(f"Баллы должны быть от 0 до {max_s}")
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
        u = self.user_repo.find_by_id(teacher_id)
        is_admin = u and u.role == 'admin'
        if not is_admin:
            cid = getattr(sess, 'course_id', None)
            if cid:
                c = Course.query.get(int(cid))
                if not c or int(c.teacher_id) != int(teacher_id):
                    raise PermissionError('Нет доступа к этой сессии')
            else:
                # Backward compatible: legacy sessions without course_id are visible to their creator.
                if int(getattr(sess, 'created_by', 0) or 0) != int(teacher_id):
                    raise PermissionError('Нет доступа к этой сессии')
        answers = self.answer_repo.find_by_session(session_id)
        result = []
        for a in answers:
            # Safety invariant: answer must belong to this session.
            if int(a.session_id) != int(session_id):
                continue
            student = self.user_repo.find_by_id(a.student_id)
            qid = getattr(a, 'question_id', None) or sess.question_id
            q = Question.query.get(qid) if qid else None
            max_score = q.max_score if q else 10
            topic_name = None
            if q:
                if q.topic_id:
                    top = Topic.query.get(q.topic_id)
                    topic_name = top.name if top else None
                if not topic_name:
                    topic_name = q.topic
            result.append({
                'id': a.id,
                'student_name': student.full_name or student.login if student else '',
                'text': a.text,
                'score': a.score,
                'is_correct': a.is_correct,
                'comment': a.comment,
                'checked_at': a.checked_at.isoformat() if a.checked_at else None,
                'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None,
                'is_late': a.is_late,
                'max_score': max_score,
                'question_text': q.text if q else None,
                'question_topic': topic_name,
                'question_difficulty': q.difficulty if q else None,
                'question_max_score': q.max_score if q else max_score,
            })
        return result

    def get_student_answers_with_feedback(self, student_id: int) -> List[dict]:
        answers = self.answer_repo.find_by_student(student_id)
        result = []
        for a in answers:
            sess = self.session_repo.find_by_id(a.session_id)
            qid = getattr(a, 'question_id', None)
            if qid is None and sess:
                qid = sess.question_id
            question = Question.query.get(qid) if qid else None
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
