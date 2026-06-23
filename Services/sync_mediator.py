import datetime

from Core.interfaces import ISyncMediator
from DTO.deleted_google_eventDTO import DeletedGoogleEventDTO
from DTO.eventDTO import EventDTO

from Services.google_calendar_service import GoogleCalendarService


class SyncMediator(ISyncMediator):
    def __init__(self, google_service: GoogleCalendarService):
        self.google_service = google_service
        self.event_controller = None
        self.auth_controller = None

    def set_controllers(self, event_controller, auth_controller):
        self.event_controller = event_controller
        self.auth_controller = auth_controller

    def run_two_way_sync(self):
        if not self.event_controller or not self.auth_controller:
            raise RuntimeError("Mediator synchronizacji nie został poprawnie zainicjalizowany kontrolerami.")

        current_sync_start = datetime.datetime.now(datetime.UTC)

        last_sync_time = self.auth_controller.get_last_sync_time()
        if not last_sync_time:
            last_sync_time = current_sync_start - datetime.timedelta(days=21)

        google_changes = self.google_service.get_events_since(last_sync_time)
        raw_local_changes = self.event_controller.get_events_modified_since(last_sync_time)

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
            local_event.google_event_id: local_event for local_event in local_changes if local_event.google_event_id
        }
        new_local_events = [local_event for local_event in local_changes if not local_event.google_event_id]

        self._push_new_local_events(new_local_events, current_sync_start)
        self._process_google_changes(google_events_by_id, local_events_by_google_id, current_sync_start)
        self._push_local_updates_to_google(local_events_by_google_id, google_events_by_id, current_sync_start)

        self.auth_controller.update_last_sync_time(current_sync_start)

    def _push_new_local_events(self, new_local_events: list, sync_time: datetime.datetime):
        for new_local in new_local_events:
            if getattr(new_local, "is_deleted", False):
                continue
            try:
                google_id = self.google_service.push_event(new_local)
                self.event_controller.sync_update_metadata(new_local.id, google_id, sync_time)
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
                        self.event_controller.sync_update_metadata(local_event.id, google_id, sync_time)
                    else:
                        self.google_service.update_event(local_event)
                        self.event_controller.sync_update_metadata(local_event.id, google_id, sync_time)
                except Exception:
                    continue

    def _process_google_event(
        self, google_id: str, google_event: EventDTO, local_events_by_google_id: dict, sync_time: datetime.datetime
    ):
        if google_id in local_events_by_google_id:
            local_event = local_events_by_google_id[google_id]
            self._resolve_conflict(local_event, google_event, sync_time)
            return

        existing_local = self.event_controller.get_event_by_google_id(google_id)

        if existing_local:
            if isinstance(google_event, DeletedGoogleEventDTO):
                self.event_controller.delete_event(existing_local.id)
            else:
                self.event_controller.sync_update_from_google(existing_local.id, google_event, sync_time)
        else:
            if not isinstance(google_event, DeletedGoogleEventDTO):
                self.event_controller.sync_create_from_google(google_event, sync_time)

    def _resolve_conflict(self, local_event: EventDTO, google_event: EventDTO, sync_time: datetime.datetime):
        google_updated = getattr(google_event, "updated_at", None)
        local_updated = local_event.updated_at or datetime.datetime.min

        if google_updated and google_updated > local_updated:
            if isinstance(google_event, DeletedGoogleEventDTO):
                self.event_controller.delete_event(local_event.id)
            else:
                self.event_controller.sync_update_from_google(local_event.id, google_event, sync_time)
        else:
            if getattr(local_event, "is_deleted", False):
                self.google_service.delete_event(local_event.google_event_id)
                self.event_controller.sync_update_metadata(local_event.id, local_event.google_event_id, sync_time)
            else:
                self.google_service.update_event(local_event)
                self.event_controller.sync_update_metadata(local_event.id, local_event.google_event_id, sync_time)
