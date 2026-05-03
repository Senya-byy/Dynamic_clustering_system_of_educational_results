# backend/services/registration_service.py
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from models import db, User, Group
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository
from services.auth_service import create_token
from utils.registration_validation import (
    validate_login,
    validate_password,
    validate_full_name,
    parse_new_group_names,
)


class RegistrationService:
    def __init__(self):
        self.users = UserRepository()
        self.groups = GroupRepository()

    def list_groups_public(self) -> list[dict]:
        rows = self.groups.find_all_ordered()
        out = []
        for g in rows:
            t = self.users.find_by_id(g.teacher_id)
            out.append(
                {
                    "id": g.id,
                    "name": g.name,
                    "teacher_login": t.login if t else None,
                    "teacher_name": (t.full_name or t.login) if t else None,
                }
            )
        return out

    def register_student(self, login: str, password: str, full_name: str, group_id: int) -> dict:
        ln = validate_login(login)
        pw = validate_password(password)
        fn = validate_full_name(full_name)
        try:
            gid = int(group_id)
        except (TypeError, ValueError):
            raise ValueError("Выберите группу")

        if self.users.find_by_login(ln):
            raise ValueError("Пользователь с таким логином уже есть")

        g = self.groups.find_by_id(gid)
        if not g:
            raise ValueError("Группа не найдена")

        u = User(login=ln, role="student", full_name=fn, group_id=gid)
        u.set_password(pw)
        try:
            db.session.add(u)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Логин уже занят или данные не сохранились")

        token = create_token(u.id, u.login, u.role)
        return {
            "access_token": token,
            "role": u.role,
            "user_id": u.id,
            "group_id": u.group_id,
        }

    def register_teacher(self, login: str, password: str, full_name: str, new_group_names: list) -> dict:
        ln = validate_login(login)
        pw = validate_password(password)
        fn = validate_full_name(full_name)
        names = parse_new_group_names(new_group_names)
        if not names:
            raise ValueError("Добавьте хотя бы одну группу (уникальное название)")
        if len(names) > 25:
            raise ValueError("Не больше 25 групп за одну регистрацию")

        if self.users.find_by_login(ln):
            raise ValueError("Пользователь с таким логином уже есть")

        for name in names:
            if self.groups.find_by_name_ci(name):
                raise ValueError(f'Группа «{name}» уже существует — выберите другое название')

        u = User(login=ln, role="teacher", full_name=fn, group_id=None)
        u.set_password(pw)
        try:
            db.session.add(u)
            db.session.flush()
            for name in names:
                db.session.add(Group(name=name.strip(), teacher_id=u.id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Логин или название группы уже занято")

        token = create_token(u.id, u.login, u.role)
        return {
            "access_token": token,
            "role": u.role,
            "user_id": u.id,
            "group_id": None,
        }
