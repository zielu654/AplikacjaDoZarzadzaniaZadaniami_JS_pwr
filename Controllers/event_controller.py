from datetime import datetime
from typing import Optional, Dict

from Controllers.exceptions import ResourceNotFoundError, InvalidDateRangeError, EmptyFieldError
from DTO.event_DTO import EventDTO
from DatabaseSqlAlchemy.interfaces import IEventRepository, ICategoryRepository, ISyncMediator, IEventQuery
from Models.event import EventSource
from Models.recurrence_rule import RecurrenceRule


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
                         priority: bool = False, rrule: Optional[str] = None, source: EventSource = EventSource.LOCAL) -> int:
        """Tworzy nowe zadanie, waliduje i zapisuje."""
        if not title or not title.strip():
            raise EmptyFieldError("Tytuł wydarzenia nie może być pusty!")

        if start_dt and end_dt and end_dt < start_dt:
            raise InvalidDateRangeError("Data zakończenia nie może być wcześniejsza niż rozpoczęcia!")

        if category_id is not None:
            cat = self._category_repo.get_by_id(category_id)
            if not cat:
                raise ResourceNotFoundError(f"Wybrana kategoria o ID {category_id} nie istnieje!")

        new_event = EventDTO(
            id=0,
            title=title.strip(),
            description=description.strip() if description else None,
            start_datetime=start_dt,
            end_datetime=end_dt,
            is_high_priority=priority,
            is_completed=False,
            category=self._category_repo.get_by_id(category_id),
            rrule_str=rrule,
            source=source
        )

        return self._event_repo.add(new_event)

    def edit_event(self, event_id: int, updates: Dict) -> None:
        """
        Aktualizuje wybrane pola zadania.
        'updates' to słownik {'nazwa zmiennej' : 'nowa wartosc'} np. {'title': 'Nowy tytuł', 'priority': 3}
        zmienne : title; description; priority; is_completed; category_id; start_dt; end_dt; rrule_string
        """
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise ResourceNotFoundError(f"Nie można edytować. Zadanie o ID {event_id} nie istnieje.")

        if 'title' in updates:
            new_title = updates['title']
            if not new_title or not str(new_title).strip():
                raise EmptyFieldError("Tytuł wydarzenia nie może być pusty!")
            event.title = str(new_title).strip()

        if 'description' in updates:
            desc = updates['description']
            event.description = str(desc).strip() if desc else None

        if 'priority' in updates:
            event.is_high_priority = bool(updates['priority'])

        if 'is_completed' in updates:
            event.is_completed = bool(updates['is_completed'])

        if 'category_id' in updates:
            cat_id = updates['category_id']
            if cat_id is not None:
                cat = self._category_repo.get_by_id(cat_id)
                if not cat:
                    raise ResourceNotFoundError(f"Wybrana kategoria o ID {cat_id} nie istnieje!")

            event.category_id = cat_id
            event.category = None

        new_start = updates.get('start_dt', event.start_datetime)
        new_end = updates.get('end_dt', event.end_datetime)

        if new_start and new_end and new_end < new_start:
            raise InvalidDateRangeError("Data zakończenia nie może być wcześniejsza niż rozpoczęcia!")

        if 'start_dt' in updates:
            event.start_datetime = updates['start_dt']
        if 'end_dt' in updates:
            event.end_datetime = updates['end_dt']

        if 'rrule_string' in updates:
            event.rrule_str = updates['rrule_string']

        self._event_repo.update(event)

    def delete_event(self, event_id: int) -> None:
        """Oznacza zadanie jako usunięte (Soft Delete: is_deleted = True)"""
        self._event_repo.delete(event_id)

    def mark_completed(self, event_id: int) -> None:
        """Zmienia status wykonania zadania na True"""
        event = self._event_repo.get_by_id(event_id)
        if not event:
            raise ResourceNotFoundError(f"Nie można oznaczyć. Zadanie o ID {event_id} nie istnieje.")

        event.is_completed = True
        self._event_repo.update(event)

    def build_query(self) -> IEventQuery:
        """Punkt wejścia dla frontendu do budowania filtrów"""
        return self._event_repo.query()

    def get_event_by_id(self, event_id: int) -> Optional[EventDTO]:
        """Pobiera pojedyncze zadanie po jego ID (np. do wypełnienia formularza edycji)."""
        return self._event_repo.get_by_id(event_id)

    def trigger_manual_sync(self) -> None:
        """Ręczne wywołanie pełnej synchronizacji dwustronnej z Google Calendar"""
        self._sync_mediator.run_two_way_sync()

    def get_events_modified_since(self, since_date: datetime) -> list[EventDTO]:
        """Pobiera wydarzenia zmodyfikowane lokalnie od ostatniej synchronizacji"""
        return self._event_repo.query().modified_since(since_date).get_list()

    def get_event_by_google_id(self, google_id: str) -> Optional[EventDTO]:
        """Pobiera pojedyncze wydarzenie z bazy na podstawie identyfikatora z Google Calendar"""
        results = self._event_repo.query().by_google_id(google_id).get_list()

        return results[0] if results else None

    def sync_update_from_google(self, event_id: int, g_event: EventDTO, sync_time: datetime) -> None:
        """Nadpisuje lokalne wydarzenie danymi z Google (Google wygrał konflikt LWW)"""
        event = self._event_repo.get_by_id(event_id)
        if event:
            event.title = g_event.title
            event.description = g_event.description
            event.start_datetime = g_event.start_datetime
            event.end_datetime = g_event.end_datetime
            event.rrule_str = g_event.rrule_str
            event.updated_at = g_event.updated_at
            event.last_synced = sync_time
            self._event_repo.update(event)

    def sync_create_from_google(self, g_event: EventDTO, sync_time: datetime) -> None:
        """Zapisuje w bazie całkowicie nowe wydarzenie pobrane z Google"""
        g_event.last_synced = sync_time
        self._event_repo.add(g_event)

    def sync_update_metadata(self, event_id: int, google_id: str, sync_time: datetime) -> None:
        """Aktualizuje tylko metadane synchronizacji (np. po wypchnięciu nowego eventu do Google)"""
        event = self._event_repo.get_by_id(event_id)
        if event:
            event.google_event_id = google_id
            event.last_synced = sync_time
            self._event_repo.update(event)

    def sync_hard_delete(self, event_id: int) -> None:
        """Trwale usuwa rekord z bazy danych (czyszczenie po usunięciu z obu stron)"""
        # Zakładamy, że interfejs repozytorium posiada metodę do pełnego usuwania
        if hasattr(self._event_repo, 'hard_delete'):
            self._event_repo.hard_delete(event_id)
        else:
            # Fallback jeśli masz tylko standardowe delete
            self._event_repo.delete(event_id)
