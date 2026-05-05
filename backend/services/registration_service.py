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

    def register_teacher(
        self,
        login: str,
        password: str,
        full_name: str,
        group_ids: list,
        new_group_names: list,
    ) -> dict:
        ln = validate_login(login)
        pw = validate_password(password)
        fn = validate_full_name(full_name)
        if new_group_names:
            raise ValueError(
                "Создание новых групп при регистрации отключено. "
                "Попросите администратора добавить группу."
            )
        raw_ids = group_ids if isinstance(group_ids, list) else []
        seen = set()
        picked_ids: list[int] = []
        for x in raw_ids:
            if x is None or x == "":
                continue
            try:
                gid = int(x)
            except (TypeError, ValueError):
                raise ValueError("group_ids должен содержать только целые числа")
            if gid <= 0:
                continue
            if gid in seen:
                continue
            seen.add(gid)
            picked_ids.append(gid)

        if not picked_ids:
            raise ValueError("Выберите хотя бы одну группу")
        if len(picked_ids) > 50:
            raise ValueError("Не больше 50 выбранных групп за одну регистрацию")

        if self.users.find_by_login(ln):
            raise ValueError("Пользователь с таким логином уже есть")

        existing_groups: list[Group] = []
        for gid in picked_ids:
            g = self.groups.find_by_id(gid)
            if not g:
                raise ValueError("Выбрана несуществующая группа")
            existing_groups.append(g)

        u = User(login=ln, role="teacher", full_name=fn, group_id=None)
        u.set_password(pw)
        try:
            db.session.add(u)
            db.session.flush()
            # Связи на уже существующие группы
            for g in existing_groups:
                self.groups.link_teacher_group_no_commit(u.id, g.id)
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
