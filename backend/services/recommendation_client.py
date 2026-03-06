# backend/services/recommendation_client.py
"""Could have (MoSCoW): заготовки вопросов — внешний клиент по C4."""


class RecommendationClient:
    @staticmethod
    def fetch_recommendations(topic_hint: str = '') -> list:
        hint = (topic_hint or '').lower()
        samples = [
            {
                'text': 'Объясните разницу между процессом и потоком в ОС.',
                'criteria': 'Оценивается точность определений и пример.',
                'difficulty': 'medium',
            },
            {
                'text': 'Опишите жизненный цикл HTTP-запроса от браузера до сервера.',
                'criteria': 'DNS, TCP, TLS, запрос/ответ.',
                'difficulty': 'hard',
            },
            {
                'text': 'Что такое нормализация БД и зачем она нужна?',
                'criteria': 'Примеры нормальных форм.',
                'difficulty': 'easy',
            },
        ]
        if 'баз' in hint or 'sql' in hint:
            return [samples[2]]
        if 'сет' in hint or 'http' in hint:
            return [samples[1]]
        return samples
