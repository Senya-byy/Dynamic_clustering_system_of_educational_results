# backend/services/question_service.py
from repositories.question_repository import QuestionRepository
from repositories.topic_repository import TopicRepository
from services.recommendation_client import RecommendationClient
from typing import Dict, List


class QuestionService:
    def __init__(self):
        self.repo = QuestionRepository()
        self.topics = TopicRepository()
        self.rec_client = RecommendationClient()

    def create_question(self, data: Dict) -> Dict:
        row = dict(data)
        if row.get('topic_id'):
            t = self.topics.find_by_id(int(row['topic_id']))
            if t and not row.get('topic'):
                row['topic'] = t.name
        question = self.repo.create(row)
        return self._to_dict(question)

    def update_question(self, qid: int, data: Dict) -> Dict:
        row = dict(data)
        if row.get('topic_id'):
            t = self.topics.find_by_id(int(row['topic_id']))
            if t and 'topic' not in row:
                row['topic'] = t.name
        q = self.repo.update(qid, row)
        return self._to_dict(q)

    def delete_question(self, qid: int) -> bool:
        return self.repo.delete(qid)

    def get_questions_by_teacher(self, teacher_id: int) -> List[dict]:
        return [self._to_dict(q) for q in self.repo.find_by_teacher(teacher_id)]

    def get_question(self, qid: int) -> Dict:
        q = self.repo.find_by_id(qid)
        if not q:
            return None
        return self._to_dict(q)

    def get_recommendations(self, topic_hint: str = '') -> List[dict]:
        return self.rec_client.fetch_recommendations(topic_hint)

    @staticmethod
    def _to_dict(q) -> dict:
        return {
            'id': q.id,
            'text': q.text,
            'topic': q.topic,
            'topic_id': q.topic_id,
            'difficulty': q.difficulty,
            'max_score': q.max_score,
            'correct_answer': q.correct_answer,
        }
