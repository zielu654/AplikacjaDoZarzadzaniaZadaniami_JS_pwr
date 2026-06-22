from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func

from DTO.eventDTO import EventDTO
from DatabaseSqlAlchemy.sql_alchemy_event_query import SqlAlchemyEventQuery
from Models.recurrence_rule import RecurrenceRule
from Models.sync_metadata import SyncMetadata
from Core.interfaces import IEventRepository
from Models.event import Event
from Core.exceptions import RecordNotFoundError, db_error_handler

class SqlAlchemyEventRepository(IEventRepository):
    def __init__(self, session):
        self.session = session

    @db_error_handler
    def add(self, event_dto: EventDTO) -> int:
        new_event = Event(
            title=event_dto.title,
            description=event_dto.description,
            category_id=event_dto.category.id if event_dto.category else getattr(event_dto, 'category_id', None),
            start_datetime=event_dto.start_datetime,
            end_datetime=event_dto.end_datetime,
            is_high_priority=event_dto.is_high_priority,
            is_completed=event_dto.is_completed,
            is_deleted=False,
            updated_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            source=event_dto.source
        )

        if event_dto.rrule_str:
            new_rule = RecurrenceRule(rrule_string=event_dto.rrule_str)
            new_event.recurrence_rule = new_rule

        self.session.add(new_event)
        self.session.flush()

        if event_dto.google_event_id:
            new_event.sync_metadata = SyncMetadata(
                event_id=new_event.id,
                google_event_id=event_dto.google_event_id,
                last_synced=datetime.now(timezone.utc)
            )
        self.session.commit()
        return new_event.id

    @db_error_handler
    def update(self, event_dto: EventDTO) -> None:
        existing_event = self.session.get(Event, event_dto.id)

        if not existing_event:
            raise RecordNotFoundError(f"Nie można zaktualizować. Wydarzenie {event_dto.title} nie istnieje.")
        if existing_event.is_deleted:
            raise RecordNotFoundError(f"Wydarzenie o ID {event_dto.id} zostało usunięte i nie można go edytować.")

        existing_event.title = event_dto.title
        existing_event.description = event_dto.description
        existing_event.start_datetime = event_dto.start_datetime
        existing_event.end_datetime = event_dto.end_datetime
        existing_event.is_high_priority = event_dto.is_high_priority
        existing_event.is_completed = event_dto.is_completed
        existing_event.category_id = event_dto.category.id if event_dto.category else getattr(event_dto, 'category_id', None)

        new_rrule_str = event_dto.rrule_str

        if existing_event.recurrence_rule:
            if new_rrule_str:
                existing_event.recurrence_rule.rrule_string = new_rrule_str
            else:
                existing_event.recurrence_rule = None
        else:
            if new_rrule_str:
                existing_event.recurrence_rule = RecurrenceRule(rrule_string=new_rrule_str)

        new_google_id = event_dto.google_event_id

        if existing_event.sync_metadata:
            if new_google_id is not None:
                existing_event.sync_metadata.google_event_id = new_google_id
                existing_event.sync_metadata.last_synced = datetime.now(timezone.utc)
            else:
                existing_event.sync_metadata = None
        else:
            if new_google_id:
                existing_event.sync_metadata = SyncMetadata(
                    event_id=existing_event.id,
                    google_event_id=new_google_id,
                    last_synced=datetime.now(timezone.utc)
                )

        existing_event.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    @db_error_handler
    def delete(self, event_id: int) -> None:
        event = self.session.get(Event, event_id)
        if not event or event.is_deleted:
            raise RecordNotFoundError(f"Wygarzenie o ID {event_id} nie istnieje!")
        event.is_deleted = True
        event.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    @db_error_handler
    def get_all(self) -> List[EventDTO]:
        events = self.session.query(Event).filter(Event.is_deleted == False).all()
        return [SqlAlchemyEventQuery.map_to_dto(event) for event in events]

    @db_error_handler
    def get_dirty_records(self) -> List[EventDTO]:
        syncDate = self.session.query(func.max(SyncMetadata.last_synced)).scalar()
        if syncDate is None:
            return self.session.query(Event).all()

        events = self.session.query(Event).filter(
            Event.updated_at > syncDate
        ).all()
        return [SqlAlchemyEventQuery.map_to_dto(event) for event in events]

    @db_error_handler
    def get_by_id(self, event_id: int) -> Optional[EventDTO]:
        event = self.session.get(Event, event_id)
        if not event or event.is_deleted:
            return None
        return SqlAlchemyEventQuery.map_to_dto(event)

    @db_error_handler
    def update_sync_metadata(self, event_id: int, google_event_id: str, last_synced: datetime) -> None:
        existing_event = self.session.get(Event, event_id)
        if not existing_event:
            raise RecordNotFoundError(f"Nie można zaktualizować metadanych. Event {event_id} nie istnieje.")

        if existing_event.sync_metadata:
            existing_event.sync_metadata.google_event_id = google_event_id
            existing_event.sync_metadata.last_synced = last_synced
        else:
            existing_event.sync_metadata = SyncMetadata(
                event_id=existing_event.id,
                google_event_id=google_event_id,
                last_synced=last_synced
            )
        self.session.commit()

    @db_error_handler
    def query(self) -> SqlAlchemyEventQuery:
        return SqlAlchemyEventQuery(self.session)
