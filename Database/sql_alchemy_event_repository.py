from datetime import datetime
from typing import List

from sqlalchemy import func

from Database.event_query import EventQuery
from Models.sync_metadata import SyncMetadata
from Database.interfaces import IEventRepository
from Models.event import Event
from Database.exceptions import RecordNotFoundError, db_error_handler

class SqlAlchemyEventRepository(IEventRepository):
    def __init__(self, session):
        self.session = session

    @db_error_handler
    def add(self, event: Event) -> int:
        event.updated_at = datetime.now()
        self.session.add(event)
        self.session.commit()
        return event.id

    @db_error_handler
    def update(self, event: Event) -> None:
        existing_event = self.session.get(Event, event.id)

        if not existing_event:
            raise RecordNotFoundError(f"Nie można zaktualizować. Wydarzenie {event.title} nie istnieje.")
        if existing_event.is_deleted:
            raise RecordNotFoundError(f"Wydarzenie o ID {event.id} zostało usunięte i nie można go edytować.")

        event.updated_at = datetime.now()
        self.session.merge(event)
        self.session.commit()

    @db_error_handler
    def delete(self, event_id: int) -> None:
        event = self.session.get(Event, event_id)
        if not event or event.is_deleted:
            raise RecordNotFoundError(f"Wygarzenie o ID {event_id} nie istnieje!")

        event.is_deleted = True
        event.updated_at = datetime.now()
        self.session.commit()

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

    @db_error_handler
    def query(self) -> EventQuery:
        """Zwraca gotowy do filtrowania obiekt EventQuery używając sesji repozytorium"""
        return EventQuery(self.session)
