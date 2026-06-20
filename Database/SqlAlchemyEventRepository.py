from datetime import datetime
from typing import List

from sqlalchemy import func

from DTO.SyncMetadata import SyncMetadata
from Database.Interfaces import IEventRepository
from DTO.Event import Event
from Database.exceptions import RecordNotFoundError, db_error_handler



class SqlAlchemyEventRepository(IEventRepository):
    def __init__(self, session):
        self.session = session

    @db_error_handler
    def add(self, event: Event) -> int:
        self.session.add(event)

        self.session.commit()
        return event.id

    @db_error_handler
    def update(self, event: Event) -> None:
        event.updated_at = datetime.now()
        self.session.merge(event)
        self.session.commit()

    @db_error_handler
    def delete(self, event_id: int) -> None:
        event = self.session.get(Event, event_id)
        if event:
            event.is_deleted = True
            event.updated_at = datetime.now()
            self.session.commit()
        else:
            raise RecordNotFoundError()

    @db_error_handler
    def get_all(self) -> List[Event]:
        return self.session.query(Event).filter(Event.is_deleted == False).all()

    @db_error_handler
    def get_dirty_records(self) -> List[Event]:
        """Niezsynchronizowane eventy"""
        syncDate = self.session.query(func.max(SyncMetadata.last_synced)).scalar()
        if syncDate is None:
            return self.session.query(Event).all()

        return self.session.query(Event).filter(
            Event.updated_at > syncDate
        ).all()


