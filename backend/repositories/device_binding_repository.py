# backend/repositories/device_binding_repository.py
from typing import Optional

from sqlalchemy.exc import IntegrityError

from models import db, SessionDeviceBinding


class DeviceBindingRepository:
    @staticmethod
    def find(session_id: int, device_key: str) -> Optional[SessionDeviceBinding]:
        return SessionDeviceBinding.query.filter_by(
            session_id=session_id, device_key=device_key
        ).first()

    @staticmethod
    def create(session_id: int, device_key: str, student_id: int) -> SessionDeviceBinding:
        row = SessionDeviceBinding(
            session_id=session_id,
            device_key=device_key,
            student_id=student_id,
        )
        db.session.add(row)
        db.session.commit()
        return row
