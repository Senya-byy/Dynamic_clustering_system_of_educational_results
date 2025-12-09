#!/usr/bin/env python3
"""
Демо-данные: преподаватель, 30 студентов, группа «Тестовая группа», предмет «Математика»,
24 закрытые пары с ответами и разными оценками (динамика в аналитике).

Запуск из каталога backend:
  PYTHONPATH=. python seed_math_demo.py
Пересоздать с нуля:
  PYTHONPATH=. python seed_math_demo.py --force
"""
import argparse
import random
import secrets
import string
import sys
from datetime import datetime, timedelta

from app import app
from models import (
    db,
    User,
    Group,
    Topic,
    Question,
    Session,
    Answer,
    Attendance,
)
from repositories.session_repository import SessionRepository

TEACHER_LOGIN = 'elena_kuznetsova'
TEACHER_NAME = 'Елена Кузнецова'
GROUP_NAME = 'Тестовая группа'
TOPIC_NAME = 'Математика'
NUM_STUDENTS = 30
NUM_SESSIONS = 24  # > 20 на ученика
STUDENT_PASSWORD = 'student123'
TEACHER_PASSWORD = 'teacher123'

STUDENT_FULL_NAMES = [
    'Анна Волкова',
    'Борис Орлов',
    'Виктория Смирнова',
    'Глеб Козлов',
    'Дарья Новикова',
    'Егор Морозов',
    'Жанна Павлова',
    'Илья Соколов',
    'Ксения Лебедева',
    'Леонид Волков',
    'Марина Фёдорова',
    'Никита Алексеев',
    'Ольга Егорова',
    'Павел Семёнов',
    'Регина Голубева',
    'Семён Виноградов',
    'Татьяна Богданова',
    'Ульяна Фролова',
    'Фёдор Романов',
    'Юлия Григорьева',
    'Ярослав Дмитриев',
    'Алина Захарова',
    'Вадим Степанов',
    'Галина Николаева',
    'Денис Андреев',
    'Екатерина Макарова',
    'Зоя Рябова',
    'Кирилл Орлов',
    'Лидия Белова',
    'Максим Титов',
]


QUESTION_SPECS = [
    ('Решите уравнение: 2x + 5 = 17.', 'easy', 2),
    ('Найдите производную функции f(x) = x³ − 3x.', 'medium', 5),
    ('Докажите теорему Пифагора для прямоугольного треугольника.', 'hard', 8),
    ('Вычислите интеграл ∫₀¹ x² dx.', 'medium', 4),
    ('Сколько диагоналей у выпуклого n-угольника? Выведите формулу.', 'medium', 5),
    ('Решите систему: x + y = 5, 2x − y = 4.', 'easy', 3),
    ('Определите чётность функции f(x) = x⁴ + cos(x).', 'easy', 3),
    ('Задача на проценты: цена выросла на 20%, затем снизилась на 20%. Изменение цены?', 'medium', 5),
    ('Найдите НОД(84, 126).', 'easy', 2),
    ('Опишите график квадратичной функции y = −2(x−1)² + 3.', 'medium', 6),
]


def _rand_code(existing: set) -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        c = ''.join(secrets.choice(alphabet) for _ in range(6))
        if c in existing:
            continue
        if Session.query.filter_by(code=c).first():
            continue
        existing.add(c)
        return c


def wipe_elena_demo():
    t = User.query.filter_by(login=TEACHER_LOGIN).first()
    if not t:
        return
    groups = Group.query.filter_by(teacher_id=t.id).all()
    for g in groups:
        for sess in list(Session.query.filter_by(group_id=g.id).all()):
            SessionRepository.delete_session_cascade(sess.id)
    for i in range(1, NUM_STUDENTS + 1):
        u = User.query.filter_by(login=f'mstu{i:02d}').first()
        if u:
            db.session.delete(u)
    for g in groups:
        db.session.delete(g)
    for top in Topic.query.filter_by(teacher_id=t.id, name=TOPIC_NAME).all():
        Question.query.filter_by(topic_id=top.id).delete(synchronize_session=False)
        db.session.delete(top)
    db.session.delete(t)
    db.session.commit()


def seed():
    existing_codes: set = set()
    rnd = random.Random(42)

    t = User(
        login=TEACHER_LOGIN,
        role='teacher',
        full_name=TEACHER_NAME,
        group_id=None,
    )
    t.set_password(TEACHER_PASSWORD)
    db.session.add(t)
    db.session.commit()

    grp = Group(name=GROUP_NAME, teacher_id=t.id)
    db.session.add(grp)
    db.session.commit()

    topic = Topic(name=TOPIC_NAME, teacher_id=t.id)
    db.session.add(topic)
    db.session.commit()

    questions = []
    for text, diff, mx in QUESTION_SPECS:
        q = Question(
            text=text,
            topic=TOPIC_NAME,
            topic_id=topic.id,
            difficulty=diff,
            max_score=mx,
            correct_answer='Эталон для демо.',
            created_by=t.id,
        )
        db.session.add(q)
        questions.append(q)
    db.session.commit()

    students = []
    for i in range(NUM_STUDENTS):
        login = f'mstu{i + 1:02d}'
        u = User(
            login=login,
            role='student',
            full_name=STUDENT_FULL_NAMES[i],
            group_id=grp.id,
        )
        u.set_password(STUDENT_PASSWORD)
        db.session.add(u)
        students.append(u)
    db.session.commit()
    student_ids = [u.id for u in students]

    # «Базовый уровень» ученика и тренд (рост/спад) для разной динамики
    base_skill = [rnd.uniform(0.25, 0.92) for _ in students]
    trend = [rnd.uniform(-0.25, 0.35) for _ in students]

    base_day = datetime.utcnow() - timedelta(days=120)

    for sj in range(NUM_SESSIONS):
        start = base_day + timedelta(days=sj * 4 + rnd.randint(0, 2))
        end = start + timedelta(hours=1, minutes=30)
        q = questions[sj % len(questions)]
        code = _rand_code(existing_codes)
        sess = Session(
            code=code,
            group_id=grp.id,
            question_id=q.id,
            created_by=t.id,
            start_time=start,
            end_time=end,
            is_active=False,
            timer_seconds=3600,
        )
        db.session.add(sess)
        db.session.flush()

        progress = sj / max(1, NUM_SESSIONS - 1)
        for si, stu in enumerate(students):
            mx = q.max_score
            skill = max(0.0, min(1.0, base_skill[si] + trend[si] * progress + rnd.uniform(-0.12, 0.12)))
            raw = skill * (0.35 + 0.65 * progress)
            score = int(round(max(0, min(mx, raw * mx))))
            if rnd.random() < 0.06:
                score = None
            submitted = start + timedelta(minutes=5 + rnd.randint(0, 40))
            is_correct = None
            checked_at = None
            comment = None
            if score is not None:
                is_correct = score >= mx * 0.85 if mx else False
                checked_at = submitted + timedelta(hours=rnd.randint(1, 48))
                if score >= mx:
                    comment = 'Отлично, всё верно.'
                elif score == 0:
                    comment = 'Нужно повторить теорию и типовые примеры.'
                else:
                    comment = rnd.choice(
                        [
                            'Есть ошибки в выкладках.',
                            'Верный ход, неточность в конце.',
                            'Хорошо, но оформление слабое.',
                            'Зачтено частично.',
                        ]
                    )
            ans = Answer(
                session_id=sess.id,
                student_id=stu.id,
                question_id=q.id,
                text=f'Ответ ученика {stu.full_name} на пару {code} (демо).',
                score=score,
                is_correct=is_correct,
                comment=comment,
                checked_by=t.id if score is not None else None,
                checked_at=checked_at,
                submitted_at=submitted,
                is_late=rnd.random() < 0.08,
            )
            db.session.add(ans)
            db.session.add(
                Attendance(
                    student_id=stu.id,
                    session_id=sess.id,
                    status='late' if ans.is_late else 'present',
                    timestamp=submitted,
                )
            )
        db.session.commit()

    print('Готово.')
    print(f'  Преподаватель: login={TEACHER_LOGIN} password={TEACHER_PASSWORD}')
    print(f'  Студенты: mstu01 … mstu{NUM_STUDENTS:02d} password={STUDENT_PASSWORD}')
    print(f'  Группа: {GROUP_NAME}, предмет: {TOPIC_NAME}')
    print(f'  Закрытых пар: {NUM_SESSIONS}, ответов: {NUM_SESSIONS * NUM_STUDENTS}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', help='Удалить старый демо-набор Елены Кузнецовой и создать заново')
    args = parser.parse_args()

    with app.app_context():
        exists = User.query.filter_by(login=TEACHER_LOGIN).first()
        if exists and not args.force:
            print('Демо уже загружено. Запустите с --force для пересоздания.', file=sys.stderr)
            sys.exit(1)
        if exists and args.force:
            wipe_elena_demo()
        seed()


if __name__ == '__main__':
    main()
