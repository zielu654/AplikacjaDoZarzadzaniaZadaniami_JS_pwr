from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from unicodedata import category

from DTO.category_DTO import CategoryDTO
from DTO.event_DTO import EventDTO
from DatabaseSqlAlchemy.sql_alchemy_event_query import SqlAlchemyEventQuery
from Models.category import CalendarColor
from Models.recurrence_rule import RecurrenceRule
from Models.sync_metadata import SyncMetadata
from DatabaseSqlAlchemy.interfaces import IEventRepository
from Models.event import Event, EventSource
from DatabaseSqlAlchemy.exceptions import RecordNotFoundError, db_error_handler

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
            updated_at=datetime.now(),
            created_at=datetime.now(),
            source=event_dto.source
        )

        if event_dto.rrule_str:
            new_rule = RecurrenceRule(rrule_string=event_dto.rrule_str)
            new_event.recurrence_rule = new_rule
        self.session.add(new_event)
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

        existing_event.updated_at = datetime.now()
        self.session.commit()

    @db_error_handler
    def delete(self, event_id: int) -> None:
        event = self.session.get(Event, event_id)
        if not event or event.is_deleted:
            raise RecordNotFoundError(f"Wygarzenie o ID {event_id} nie istnieje!")
        print(f"{self} is deleted")
        event.is_deleted = True
        event.updated_at = datetime.now()
        self.session.commit()

    @db_error_handler
    def get_all(self) -> List[EventDTO]:
        events = self.session.query(Event).filter(Event.is_deleted == False).all()
        return [self._map_to_dto(e) for e in events]

    @db_error_handler
    def get_dirty_records(self) -> List[EventDTO]:
        """Niezsynchronizowane eventy"""
        syncDate = self.session.query(func.max(SyncMetadata.last_synced)).scalar()
        if syncDate is None:
            return self.session.query(Event).all()

        events = self.session.query(Event).filter(
            Event.updated_at > syncDate
        ).all()
        return [self._map_to_dto(e) for e in events]

    @db_error_handler
    def get_by_id(self, event_id: int) -> Optional[EventDTO]:
        event = self.session.get(Event, event_id)
        if not event or event.is_deleted:
            return None
        return self._map_to_dto(event)

    @db_error_handler
    def query(self) -> SqlAlchemyEventQuery:
        """Zwraca gotowy do filtrowania obiekt EventQuery używając sesji repozytorium"""
        return SqlAlchemyEventQuery(self.session)

    def _map_to_dto(self, event: Event) -> EventDTO:
        """Prywatna metoda pomocnicza, żeby nie powtarzać kodu mapowania"""
        cat_dto = None
        if event.category_id and event.category:
            cat_dto = CategoryDTO(
                id=event.category.id,
                name=event.category.name,
                color=event.category.color,
                sync_enabled=event.category.sync_enabled
            )
        rrule = event.recurrence_rule.rrule_string if event.recurrence_rule else None
        return EventDTO(
            id=event.id,
            title=event.title,
            description=event.description,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            is_high_priority=event.is_high_priority,
            is_completed=event.is_completed,
            category=cat_dto,
            rrule_str=rrule,
            source=event.source
        )