# backend/services/admin_service.py
from typing import Dict, List

from models import (
    db,
    User,
    Group,
    TeacherGroup,
    SessionGroup,
    Topic,
    Question,
    ScheduleSlot,
    JoinTicket,
    Answer,
    Attendance,
    ClusterResult,
    ClusterRun,
    ClusterAssignment,
    Reminder,
    SessionDeviceBinding,
    SessionStudentAssignment,
)
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository
from repositories.session_repository import SessionRepository


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
                'status': getattr(g, 'status', 'active') or 'active',
                'teacher_id': g.teacher_id,
                'teacher_login': t.login if t else None,
            })
        return rows

    def create_group(self, name: str, teacher_id: int) -> dict:
        name = (name or '').strip()
        if not name:
            raise ValueError('Укажите название группы')
        if self.groups.find_by_name_ci(name):
            raise ValueError('Группа с таким названием уже есть')
        t = self.users.find_by_id(teacher_id)
        if not t or t.role != 'teacher':
            raise ValueError('Преподаватель не найден или не является teacher')
        g = self.groups.create(name, teacher_id)
        # Админ создал группу, но преподаватель-владелец должен иметь к ней доступ.
        try:
            self.groups.link_teacher_group(teacher_id, g.id)
        except Exception:
            # Если уже связана или constraint, не мешаем созданию группы.
            pass
        return {'id': g.id, 'name': g.name, 'teacher_id': g.teacher_id}

    def set_group_status(self, group_id: int, status: str) -> dict:
        status = (status or '').strip().lower()
        if status not in ('active', 'pending', 'archived'):
            raise ValueError('status должен быть one of: active, pending, archived')
        g = self.groups.find_by_id(int(group_id))
        if not g:
            raise ValueError('Группа не найдена')
        g.status = status
        db.session.commit()
        return {'id': g.id, 'status': g.status}

    def create_user(
        self,
        login: str,
        password: str,
        role: str,
        full_name: str = None,
        group_id: int = None,
    ) -> dict:
        login = (login or '').strip().lower()
        if not login or not password:
            raise ValueError('Логин и пароль обязательны')
        if len(str(password)) < 4:
            raise ValueError('Пароль не короче 4 символов')
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
        u = User(
            login=login,
            role=role,
            full_name=(full_name or '').strip() or None,
            group_id=gid,
        )
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

    def bootstrap_admin(self, login: str, password: str, full_name: str | None = None) -> dict:
        login = (login or "").strip().lower()
        if not login or not password:
            raise ValueError("Логин и пароль обязательны")
        if len(str(password)) < 4:
            raise ValueError("Пароль не короче 4 символов")
        if self.users.find_by_login(login):
            raise ValueError("Пользователь с таким логином уже есть")
        # Allow bootstrap only if there is no admin yet.
        if User.query.filter_by(role="admin").first():
            raise ValueError("Администратор уже существует")
        u = User(
            login=login,
            role="admin",
            full_name=(full_name or "").strip() or None,
            group_id=None,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return {
            "id": u.id,
            "login": u.login,
            "role": u.role,
            "full_name": u.full_name,
            "group_id": u.group_id,
        }

    def delete_teacher_own_group(self, teacher_id: int, group_id: int) -> bool:
        u = self.users.find_by_id(teacher_id)
        if not u or u.role != 'teacher':
            raise ValueError('Доступно только преподавателю')
        g = self.groups.find_by_id(group_id)
        if not g:
            return False
        if g.teacher_id != teacher_id:
            raise ValueError('Можно удалить только свою группу')
        return self.delete_group(group_id)

    def delete_group(self, group_id: int) -> bool:
        g = self.groups.find_by_id(group_id)
        if not g:
            return False
        # Clean up m2m links first.
        TeacherGroup.query.filter_by(group_id=group_id).delete()
        SessionGroup.query.filter_by(group_id=group_id).delete()
        ScheduleSlot.query.filter_by(group_id=group_id).delete()
        for cr in ClusterRun.query.filter_by(group_id=group_id).all():
            db.session.delete(cr)
        db.session.flush()
        SessionRepository.delete_sessions_for_group(group_id)
        User.query.filter(User.group_id == group_id).update({User.group_id: None})
        db.session.delete(g)
        db.session.commit()
        return True

    def delete_user(self, actor_id: int, target_id: int) -> None:
        if actor_id == target_id:
            raise ValueError('Нельзя удалить свою учётную запись')
        u = self.users.find_by_id(target_id)
        if not u:
            raise ValueError('Пользователь не найден')
        if u.role == 'admin':
            raise ValueError('Нельзя удалить администратора')
        if u.role == 'student':
            self._purge_student(target_id)
            return
        if u.role == 'teacher':
            self._purge_teacher(target_id)
            return
        raise ValueError('Неизвестная роль')

    def _purge_student(self, user_id: int) -> None:
        JoinTicket.query.filter_by(consumed_by=user_id).update({JoinTicket.consumed_by: None})
        SessionDeviceBinding.query.filter_by(student_id=user_id).delete()
        SessionStudentAssignment.query.filter_by(student_id=user_id).delete()
        Answer.query.filter_by(student_id=user_id).delete()
        Attendance.query.filter_by(student_id=user_id).delete()
        ClusterAssignment.query.filter_by(student_id=user_id).delete()
        ClusterResult.query.filter_by(student_id=user_id).delete()
        Reminder.query.filter_by(user_id=user_id).delete()
        row = User.query.get(user_id)
        if row:
            db.session.delete(row)
            db.session.commit()

    def _purge_teacher(self, user_id: int) -> None:
        Reminder.query.filter_by(teacher_id=user_id).delete()
        Answer.query.filter_by(checked_by=user_id).update({Answer.checked_by: None})
        db.session.commit()
        for g in list(Group.query.filter_by(teacher_id=user_id).all()):
            self.delete_group(g.id)
        for q in list(Question.query.filter_by(created_by=user_id).all()):
            SessionRepository.purge_question_from_sessions(q.id)
            db.session.delete(q)
        for t in list(Topic.query.filter_by(teacher_id=user_id).all()):
            db.session.delete(t)
        row = User.query.get(user_id)
        if row:
            db.session.delete(row)
            db.session.commit()
