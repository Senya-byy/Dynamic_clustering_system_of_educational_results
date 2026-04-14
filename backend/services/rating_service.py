# backend/services/rating_service.py
from repositories.answer_repository import AnswerRepository
from repositories.user_repository import UserRepository
from models import User
from sqlalchemy import func

class RatingService:
    def __init__(self):
        self.answer_repo = AnswerRepository()
        self.user_repo = UserRepository()

    def get_group_rating(self, group_id: int, requesting_user_id: int, is_teacher: bool):
        students = self.user_repo.find_by_group(group_id)
        result = []
        for s in students:
            answers = self.answer_repo.find_by_student(s.id)
            total_score = sum(a.score for a in answers if a.score is not None)
            # если студент скрыт и запрашивает не преподаватель и не сам студент
            if s.privacy_mode and not is_teacher and requesting_user_id != s.id:
                display_name = f"Студент {s.id}"
            else:
                display_name = s.full_name or s.login
            result.append({
                'user_id': s.id,
                'name': display_name,
                'total_score': total_score,
                'is_self': requesting_user_id == s.id,
                'is_hidden': s.privacy_mode
            })
        # сортировка по убыванию баллов
        result.sort(key=lambda x: x['total_score'], reverse=True)
        # добавим место
        for idx, item in enumerate(result, 1):
            item['rank'] = idx
        return result