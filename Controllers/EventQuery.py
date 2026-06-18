from typing import List
from datetime import datetime, date
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.orm import Session
from DTO.Event import Event 

class EventQuery:
    def __init__(self, session: Session):
        self._session = session
        self._query = select(Event).where(Event.is_deleted == False)

    def overdue(self) -> 'EventQuery':
        """Filtruje zadania, których termin minął i nie są zrobione"""
        now = datetime.now()
        self._query = self._query.where(
            and_(
                Event.end_datetime < now,
                Event.is_completed == False
            )
        )
        return self

    def high_priority(self) -> 'EventQuery':
        """Filtruje tylko wysoki priorytet"""
        self._query = self._query.where(Event.is_high_priority == True)
        return self

    def low_priority(self) -> 'EventQuery':
        """Filtruje tylko wysoki priorytet"""
        self._query = self._query.where(Event.is_high_priority == False)
        return self

    def by_category(self, category_id: int) -> 'EventQuery':
        """Filtruje po ID kategorii"""
        self._query = self._query.where(Event.category_id == category_id)
        return self

    def for_date(self, target_date: date) -> 'EventQuery':
        """Filtruje zadania na konkretny dzień (porównuje tylko datę, bez godzin)"""
        self._query = self._query.where(Event.start_datetime.date() == target_date)
        return self

    def sort_by(self, field_name: str, ascending: bool = True) -> 'EventQuery':
        """Dynamiczne sortowanie po polu"""
        column = getattr(Event, field_name, None)
        if column is not None:
            order_func = asc(column) if ascending else desc(column)
            self._query = self._query.order_by(order_func)
        return self

    def get_list(self) -> List[Event]:
        """Uruchamia zapytanie w bazie i zwraca gotowe obiekty"""
        result = self._session.scalars(self._query)
        return list(result.all())