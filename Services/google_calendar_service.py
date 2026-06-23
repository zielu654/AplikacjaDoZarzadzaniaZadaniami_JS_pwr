import datetime
import json
from typing import List, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from Core.exceptions import GoogleAuthError, GoogleEventNotFoundError, GoogleCalendarError
from DTO.deleted_google_eventDTO import DeletedGoogleEventDTO
from DTO.eventDTO import EventDTO
from DTO.user_credentialsDTO import UserCredentialsDTO
from Core.interfaces import IUserCredentialsRepository
from Models.event import EventSource


class GoogleCalendarService:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(
        self,
        credentials_repository: IUserCredentialsRepository,
        current_user_id: int,
        credentials_path: str = "../Secrets/credentials.json",
        calendar_id: str = "primary",
    ):
        self.repo = credentials_repository
        self.user_id = current_user_id
        self.credentials_path = credentials_path
        self.calendar_id = calendar_id
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None

        db_creds = self.repo.get_by_user_id(self.user_id)
        if db_creds and db_creds.token_data:
            creds = Credentials.from_authorized_user_info(json.loads(db_creds.token_data), self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)

            dto_to_save = UserCredentialsDTO(user_id=self.user_id, token_data=creds.to_json())
            self.repo.save(dto_to_save)

        return build("calendar", "v3", credentials=creds)

    def push_event(self, event_dto: EventDTO) -> str:
        google_event_body = self._map_dto_to_google(event_dto)

        created_event = self.service.events().insert(calendarId=self.calendar_id, body=google_event_body).execute()

        return created_event.get("id")

    def get_upcoming_events(self, max_results: int = 10) -> List[EventDTO]:
        now_str = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

        events_result = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=now_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        google_events = events_result.get("items", [])

        return [dto for ge in google_events if isinstance((dto := self._map_google_to_dto(ge)), EventDTO)]

    def update_event(self, dto: EventDTO) -> None:
        if not self.service:
            raise GoogleAuthError("Brak aktywnego połączenia z Google Calendar.")

        try:
            body = self._map_dto_to_google(dto)
            self.service.events().update(calendarId=self.calendar_id, eventId=dto.google_event_id, body=body).execute()

        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(f"Wydarzenie o ID {dto.google_event_id} nie istnieje w Google Calendar.")

            raise GoogleCalendarError(f"Błąd HTTP podczas aktualizacji wydarzenia w Google: {e._get_reason()}")

        except Exception as e:
            raise GoogleCalendarError(f"Nieoczekiwany błąd podczas komunikacji z Google: {e}")

    def delete_event(self, google_id: str) -> None:
        if not self.service:
            raise GoogleAuthError("Brak aktywnego połączenia z Google Calendar.")

        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=google_id).execute()

        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(
                    f"Nie można usunąć. Wydarzenie o ID {google_id} już nie istnieje w Google Calendar."
                )
            raise GoogleCalendarError(f"Błąd HTTP podczas usuwania wydarzenia w Google: {e._get_reason()}")

        except Exception as e:
            raise GoogleCalendarError(f"Nieoczekiwany błąd podczas komunikacji z Google: {e}")

    def get_events_since(self, last_sync_date: datetime) -> list[EventDTO | DeletedGoogleEventDTO]:
        if last_sync_date.tzinfo is None:
            updated_min = last_sync_date.isoformat() + "Z"
        else:
            updated_min = last_sync_date.isoformat()

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=getattr(self, "calendar_id", "primary"),
                    updatedMin=updated_min,
                    showDeleted=True,
                    singleEvents=False,
                )
                .execute()
            )

            raw_items = events_result.get("items", [])
            return [self._map_google_to_dto(item) for item in raw_items]
        except Exception as e:
            raise GoogleCalendarError(f"Nieoczekiwany błąd podczas komunikacji z Google: {e}")

    def _map_dto_to_google(self, dto: EventDTO) -> dict:
        start_str = dto.start_datetime.isoformat() if dto.start_datetime else datetime.datetime.now().isoformat()
        end_str = (
            dto.end_datetime.isoformat()
            if dto.end_datetime
            else (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
        )

        body = {
            "summary": dto.title,
            "description": dto.description,
            "start": {
                "dateTime": start_str,
                "timeZone": "Europe/Warsaw",
            },
            "end": {
                "dateTime": end_str,
                "timeZone": "Europe/Warsaw",
            },
        }
        if dto.google_event_id:
            body["id"] = dto.google_event_id

        if dto.rrule_str:
            body["recurrence"] = [f"RRULE:{dto.rrule_str}"]

        if dto.category and dto.category.color.id is not None:
            body["colorId"] = dto.category.color.id

        return body

    def _map_google_to_dto(self, google_event: dict) -> Union[EventDTO, DeletedGoogleEventDTO]:
        google_event_id = google_event.get("id")

        updated_at_dt = None
        google_updated_str = google_event.get("updated")
        if google_updated_str:
            if google_updated_str.endswith("Z"):
                google_updated_str = google_updated_str.replace("Z", "+00:00")
            updated_at_dt = datetime.datetime.fromisoformat(google_updated_str)

        if google_event.get("status") == "cancelled":
            return DeletedGoogleEventDTO(google_event_id=google_event_id, updated_at=updated_at_dt)

        start_info = google_event.get("start", {})
        end_info = google_event.get("end", {})

        start_data = start_info.get("dateTime", start_info.get("date"))
        end_data = end_info.get("dateTime", end_info.get("date"))

        start_dt = datetime.datetime.fromisoformat(start_data) if start_data else None
        end_dt = datetime.datetime.fromisoformat(end_data) if end_data else None

        rrule_str = None
        if "recurrence" in google_event and google_event["recurrence"]:
            raw_rrule = google_event["recurrence"][0]
            if raw_rrule.startswith("RRULE:"):
                rrule_str = raw_rrule.replace("RRULE:", "")

        return EventDTO(
            id=None,
            title=google_event.get("summary", "Brak tytułu"),
            description=google_event.get("description"),
            start_datetime=start_dt,
            end_datetime=end_dt,
            is_high_priority=False,
            is_completed=False,
            rrule_str=rrule_str,
            source=EventSource.GOOGLE,
            category=None,
            google_event_id=google_event_id,
            updated_at=updated_at_dt,
        )
