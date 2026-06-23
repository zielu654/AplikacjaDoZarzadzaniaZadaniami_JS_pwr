import datetime

from Core.interfaces import ISyncMediator, IEventRepository, IUserCredentialsRepository
from DTO.deleted_google_eventDTO import DeletedGoogleEventDTO
from DTO.eventDTO import EventDTO
from Services.google_calendar_service import GoogleCalendarService


class SyncMediator(ISyncMediator):
    def __init__(
            self,
            google_service: GoogleCalendarService,
            event_repo: IEventRepository,
            credentials_repo: IUserCredentialsRepository
    ):
        self.google_service = google_service
        self.event_repo = event_repo
        self.credentials_repo = credentials_repo

    def run_two_way_sync(self):
        current_sync_start = datetime.datetime.now(datetime.UTC)
        user_id = self.google_service.user_id

        db_creds = self.credentials_repo.get_by_user_id(user_id)
        last_sync_time = db_creds.last_synced if db_creds else None

        if not last_sync_time:
            last_sync_time = current_sync_start - datetime.timedelta(days=21)

        google_changes = self.google_service.get_events_since(last_sync_time)
        raw_local_changes = self.event_repo.query().modified_since(last_sync_time).get_list()

        local_changes = []
        for event in raw_local_changes:
            if event.category is None or getattr(event.category, "sync_enabled", True) is True:
                local_changes.append(event)

        google_events_by_id = {
            google_event.google_event_id: google_event
            for google_event in google_changes
            if google_event.google_event_id
        }
        local_events_by_google_id = {
            local_event.google_event_id: local_event
            for local_event in local_changes
            if local_event.google_event_id
        }
        new_local_events = [local_event for local_event in local_changes if not local_event.google_event_id]

        self._push_new_local_events(new_local_events, current_sync_start)
        self._process_google_changes(google_events_by_id, local_events_by_google_id, current_sync_start)
        self._push_local_updates_to_google(local_events_by_google_id, google_events_by_id, current_sync_start)

        self.credentials_repo.update_last_synced(user_id, current_sync_start)

    def _push_new_local_events(self, new_local_events: list, sync_time: datetime.datetime):
        for new_local in new_local_events:
            if getattr(new_local, "is_deleted", False):
                continue
            try:
                google_id = self.google_service.push_event(new_local)
                self._sync_update_metadata(new_local.id, google_id, sync_time)
            except Exception:
                continue

    def _process_google_changes(
            self, google_events_by_id: dict, local_events_by_google_id: dict, sync_time: datetime.datetime
    ):
        for google_id, google_event in google_events_by_id.items():
            try:
                self._process_google_event(google_id, google_event, local_events_by_google_id, sync_time)
            except Exception:
                continue

    def _push_local_updates_to_google(
            self, local_events_by_google_id: dict, google_events_by_id: dict, sync_time: datetime.datetime
    ):
        for google_id, local_event in local_events_by_google_id.items():
            if google_id not in google_events_by_id:
                try:
                    if getattr(local_event, "is_deleted", False):
                        try:
                            self.google_service.delete_event(google_id)
                        except Exception:
                            continue
                        self._sync_update_metadata(local_event.id, google_id, sync_time)
                    else:
                        self.google_service.update_event(local_event)
                        self._sync_update_metadata(local_event.id, google_id, sync_time)
                except Exception:
                    continue

    def _process_google_event(
            self, google_id: str, google_event: EventDTO, local_events_by_google_id: dict, sync_time: datetime.datetime
    ):
        if google_id in local_events_by_google_id:
            local_event = local_events_by_google_id[google_id]
            self._resolve_conflict(local_event, google_event, sync_time)
            return

        results = self.event_repo.query().by_google_id(google_id).get_list()
        existing_local = results[0] if results else None

        if existing_local:
            if isinstance(google_event, DeletedGoogleEventDTO):
                self.event_repo.delete(existing_local.id)
            else:
                self._sync_update_from_google(existing_local.id, google_event, sync_time)
        else:
            if not isinstance(google_event, DeletedGoogleEventDTO):
                self._sync_create_from_google(google_event, sync_time)

    def _resolve_conflict(self, local_event: EventDTO, google_event: EventDTO, sync_time: datetime.datetime):
        google_updated = getattr(google_event, "updated_at", None)
        local_updated = local_event.updated_at or datetime.datetime.min

        if google_updated and google_updated > local_updated:
            if isinstance(google_event, DeletedGoogleEventDTO):
                self.event_repo.delete(local_event.id)
            else:
                self._sync_update_from_google(local_event.id, google_event, sync_time)
        else:
            if getattr(local_event, "is_deleted", False):
                self.google_service.delete_event(local_event.google_event_id)
                self._sync_update_metadata(local_event.id, local_event.google_event_id, sync_time)
            else:
                self.google_service.update_event(local_event)
                self._sync_update_metadata(local_event.id, local_event.google_event_id, sync_time)


    def _sync_update_from_google(self, event_id: int, google_event: EventDTO, sync_time: datetime.datetime):
        event = self.event_repo.get_by_id(event_id)
        if event:
            event.title = google_event.title
            event.description = google_event.description
            event.start_datetime = google_event.start_datetime
            event.end_datetime = google_event.end_datetime
            event.rrule_str = google_event.rrule_str
            event.updated_at = google_event.updated_at
            event.last_synced = sync_time
            self.event_repo.update(event)

    def _sync_create_from_google(self, google_event: EventDTO, sync_time: datetime.datetime):
        google_event.last_synced = sync_time
        self.event_repo.add(google_event)

    def _sync_update_metadata(self, event_id: int, google_id: str, sync_time: datetime.datetime):
        if hasattr(self.event_repo, "update_sync_metadata"):
            self.event_repo.update_sync_metadata(event_id, google_id, sync_time)
        else:
            event = self.event_repo.get_by_id(event_id)
            if event:
                event.google_event_id = google_id
                event.last_synced = sync_time
                self.event_repo.update(event)