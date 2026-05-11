# backend/services/import_service.py
import csv
import io
from typing import List
from repositories.schedule_repository import ScheduleRepository
from repositories.group_repository import GroupRepository


class ImportService:
    def __init__(self):
        self.sched = ScheduleRepository()
        self.groups = GroupRepository()

    def import_schedule_csv(self, file_stream, teacher_id: int, role: str) -> dict:
        if role not in ('teacher', 'admin'):
            raise PermissionError('Импорт только для преподавателя')
        text = file_stream.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        required = {'group_id', 'weekday', 'start_time', 'end_time'}
        rows = list(reader)
        if not rows:
            raise ValueError('Пустой файл')
        if not required.issubset(set(rows[0].keys())):
            raise ValueError(
                f'CSV нужны колонки: {", ".join(required)} и опционально title'
            )
        created = 0
        for row in rows:
            gid = int(row['group_id'])
            g = self.groups.find_by_id(gid)
            if not g:
                continue
            if role != 'admin' and not self.groups.teacher_has_group(teacher_id, gid):
                continue
            self.sched.create({
                'group_id': gid,
                'teacher_id': teacher_id,
                'weekday': int(row['weekday']),
                'start_time': row['start_time'].strip(),
                'end_time': row['end_time'].strip(),
                'title': (row.get('title') or '').strip() or None,
            })
            created += 1
        return {'imported_slots': created}
