# backend/services/admin_service.py
from typing import Dict, List

from models import User, Group
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository


class AdminService:
    def __init__(self):
        self.users = UserRepository()
        self.groups = GroupRepository()

    def list_users(self) -> List[dict]:
        return [
            {
                'id': u.id,
                'login': u.login,
                'role': u.role,
                'full_name': u.full_name,
                'group_id': u.group_id,
            }
            for u in self.users.list_all()
        ]

    def list_groups(self) -> List[dict]:
        rows = []
        for g in self.groups.find_all():
            t = self.users.find_by_id(g.teacher_id)
            rows.append({
                'id': g.id,
                'name': g.name,
                'teacher_id': g.teacher_id,
                'teacher_login': t.login if t else None,
            })
        return rows

    def create_group(self, name: str, teacher_id: int) -> dict:
        name = (name or '').strip()
        if not name:
            raise ValueError('Укажите название группы')
        t = self.users.find_by_id(teacher_id)
        if not t or t.role != 'teacher':
            raise ValueError('Преподаватель не найден или не является teacher')
        g = self.groups.create(name, teacher_id)
        return {'id': g.id, 'name': g.name, 'teacher_id': g.teacher_id}

    def create_user(
        self,
        login: str,
        password: str,
        role: str,
        full_name: str = None,
        group_id: int = None,
    ) -> dict:
        login = (login or '').strip()
        if not login or not password:
            raise ValueError('Логин и пароль обязательны')
        if role not in ('student', 'teacher'):
            raise ValueError('Можно создать только роли student или teacher')
        if self.users.find_by_login(login):
            raise ValueError('Пользователь с таким логином уже есть')
        if role == 'student':
            gid = group_id
            if gid is not None and not self.groups.find_by_id(gid):
                raise ValueError('Группа не найдена')
        else:
            gid = None
        u = User(login=login, role=role, full_name=(full_name or '').strip() or None, group_id=gid)
        u.set_password(password)
        from models import db
        db.session.add(u)
        db.session.commit()
        return {
            'id': u.id,
            'login': u.login,
            'role': u.role,
            'full_name': u.full_name,
            'group_id': u.group_id,
        }
