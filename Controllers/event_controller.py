from datetime import datetime
from typing import Optional, Dict

from sqlalchemy.orm import Session

from Database.event_query import EventQuery
from Controllers.exceptions import ResourceNotFoundError, InvalidDateRangeError, EmptyFieldError
from DTO.event_DTO import EventDTO
from Database.interfaces import IEventRepository, ICategoryRepository, ISyncMediator
from Models.event import EventSource, Event


class EventController:
    def __init__(
        self,
        event_repo: IEventRepository,
        category_repo: ICategoryRepository,
        sync_mediator: ISyncMediator
    ):
        self._event_repo = event_repo
        self._category_repo = category_repo
        self._sync_mediator = sync_mediator

    def create_new_event(self, title: str, description: str, category_id: Optional[int],
                         start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None,
                         priority: bool = False, source: EventSource = EventSource.LOCAL) -> int:
        """Tworzy nowe zadanie, waliduje i zapisuje."""
        if not title or not title.strip():
            raise EmptyFieldError("Tytuł wydarzenia nie może być pusty!")

        if start_dt and end_dt and end_dt < start_dt:
            raise InvalidDateRangeError("Data zakończenia nie może być wcześniejsza niż rozpoczęcia!")

        if category_id is not None:
            active_ids = [cat.id for cat in self._category_repo.get_all()]
            if category_id not in active_ids:
                raise ResourceNotFoundError(f"Wybrana kategoria o ID {category_id} nie istnieje!")

        new_event = Event(
            title=title.strip(),
            description=description.strip() if description else None,
            category_id=category_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            is_high_priority=priority,
            is_completed=False,
            source=source
        )

        return self._event_repo.add(new_event)

    def edit_event(self, event_id: int, updates: Dict) -> None:
        """
        Aktualizuje wybrane pola zadania.
        'updates' to słownik {'nazwa zmiennej' : 'nowa wartosc'} np. {'title': 'Nowy tytuł', 'priority': 3}
        """
        pass

    def delete_event(self, event_id: int) -> None:
        """Oznacza zadanie jako usunięte (Soft Delete: is_deleted = True)"""
        pass

    def mark_completed(self, event_id: int) -> None:
        """Zmienia status wykonania zadania na True"""
        pass

    def build_query(self) -> EventQuery:
        """Punkt wejścia dla frontendu do budowania filtrów"""
        return self._event_repo.query()

    def get_event_by_id(self, event_id: int) -> Optional[EventDTO]:
        """Pobiera pojedyncze zadanie po jego ID (np. do wypełnienia formularza edycji)."""
        return self._event_repo.get_by_id(event_id)

    def trigger_manual_sync(self) -> None:
        """Ręczne wywołanie pełnej synchronizacji dwustronnej z Google Calendar"""
        self._sync_mediator.run_two_way_sync()
