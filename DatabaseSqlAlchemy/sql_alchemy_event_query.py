from typing import List
from datetime import datetime, date, time
from sqlalchemy.orm import Session

from DTO import CategoryDTO, EventDTO
from Core import IEventQuery
from Models import Event


class SqlAlchemyEventQuery(IEventQuery):
    def __init__(self, session: Session):
        self._session = session
        self._query = self._session.query(Event).filter(Event.is_deleted == False)

    def overdue(self) -> "SqlAlchemyEventQuery":
        now = datetime.now()
        self._query = self._query.filter(Event.end_datetime < now, Event.is_completed == False)
        return self

    def high_priority(self) -> "SqlAlchemyEventQuery":
        self._query = self._query.filter(Event.is_high_priority == True)
        return self

    def low_priority(self) -> "SqlAlchemyEventQuery":
        self._query = self._query.filter(Event.is_high_priority == False)
        return self

    def by_category(self, category_id: int) -> "SqlAlchemyEventQuery":
        self._query = self._query.filter(Event.category_id == category_id)
        return self

    def for_date(self, target_date: date) -> "SqlAlchemyEventQuery":
        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)

        self._query = self._query.filter(Event.start_datetime.between(start_of_day, end_of_day))
        return self

    def sort_by(self, field_name: str, ascending: bool = True) -> "SqlAlchemyEventQuery":
        column = getattr(Event, field_name, None)
        if column is not None:
            order_func = column.asc() if ascending else column.desc()
            self._query = self._query.order_by(order_func)
        return self

    def get_list(self) -> List[EventDTO]:
        db_events = self._query.all()

        dtos = []
        for event in db_events:
            dtos.append(self.map_to_dto(event))

        return dtos

    def by_google_id(self, google_id: str) -> "SqlAlchemyEventQuery":
        from Models.sync_metadata import SyncMetadata  # Import awaryjny, w razie gdyby nie było go na górze pliku

        self._query = self._query.filter(Event.sync_metadata.has(SyncMetadata.google_event_id == google_id))
        return self

    def modified_since(self, since_date: datetime) -> "SqlAlchemyEventQuery":
        self._query = self._query.filter(Event.updated_at > since_date)
        return self

    @staticmethod
    def map_to_dto(event: Event) -> EventDTO:
        cat_dto = None
        if event.category_id and event.category:
            cat_dto = CategoryDTO(
                id=event.category.id,
                name=event.category.name,
                color=event.category.color,
                sync_enabled=event.category.sync_enabled,
            )
        rrule = event.recurrence_rule.rrule_string if event.recurrence_rule else None
        google_id = event.sync_metadata.google_event_id if event.sync_metadata else None
        last_synced = event.sync_metadata.last_synced if event.sync_metadata else None
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
            source=event.source,
            updated_at=event.updated_at,
            google_event_id=google_id,
            last_synced=last_synced,
        )
