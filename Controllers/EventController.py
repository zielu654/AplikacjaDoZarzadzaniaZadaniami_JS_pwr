from datetime import datetime
from typing import Optional, Dict

from Controllers.EventQuery import EventQuery
from Models.Event import EventSource, Event


class EventController:
    def __init__(self, event_repo: any, sync_mediator: any, session_factory):
        self._event_repo = event_repo
        self._sync_mediator = sync_mediator
        self._session_factory = session_factory

    def create_new_event(self, title: str, description: str, category_id: Optional[int],
                         start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None,
                         priority: bool = False, source: EventSource = EventSource.LOCAL) -> int:
        """Tworzy nowe zadanie, waliduje dane i zapisuje do bazy. Zwraca ID nowego zadania."""
        if not title.strip():
            raise ValueError("Tytuł zadania nie może być pusty!")
        pass

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

    def query(self) -> EventQuery:
        """Punkt wejścia dla frontendu do budowania filtrów"""
        session = self._session_factory()
        return EventQuery(session)

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Pobiera pojedyncze zadanie po jego ID (np. do wypełnienia formularza edycji)."""
        return self._event_repo.get_by_id(event_id)

    def trigger_manual_sync(self) -> None:
        """Ręczne wywołanie pełnej synchronizacji dwustronnej z Google Calendar"""
        self._sync_mediator.run_two_way_sync()
