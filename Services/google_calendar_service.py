import datetime
import json
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from DTO.event_DTO import EventDTO
from DTO.user_credentials_DTO import UserCredentialsDTO
from DatabaseSqlAlchemy.interfaces import IUserCredentialsRepository
from Models.event import EventSource
from Services.exceptions import GoogleAuthError, GoogleEventNotFoundError, GoogleCalendarError


class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self,
                 credentials_repository: IUserCredentialsRepository,
                 current_user_id: int,
                 credentials_path: str = 'Secrets/credentials.json',
                 calendar_id: str = 'primary'):
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

        return build('calendar', 'v3', credentials=creds)

    def add_event(self, event_dto: EventDTO) -> str:
        google_event_body = self._map_dto_to_google(event_dto)

        created_event = self.service.events().insert(
            calendarId=self.calendar_id,
            body=google_event_body
        ).execute()

        return created_event.get('id')

    def get_upcoming_events(self, max_results: int = 10) -> List[EventDTO]:
        now_str = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=now_str,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        google_events = events_result.get('items', [])
        return [self._map_google_to_dto(ge) for ge in google_events]

    def update_event(self, google_id: str, dto: EventDTO) -> None:
        if not self.service:
            raise GoogleAuthError("Brak aktywnego połączenia z Google Calendar.")

        try:
            body = self._map_dto_to_google(dto)
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=google_id,
                body=body
            ).execute()

        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(f"Wydarzenie o ID {google_id} nie istnieje w Google Calendar.")

            raise GoogleCalendarError(f"Błąd HTTP podczas aktualizacji wydarzenia w Google: {e._get_reason()}")

        except Exception as e:
            raise GoogleCalendarError(f"Nieoczekiwany błąd podczas komunikacji z Google: {e}")

    def delete_event(self, google_id: str) -> None:
        if not self.service:
            raise GoogleAuthError("Brak aktywnego połączenia z Google Calendar.")

        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=google_id
            ).execute()

        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(f"Nie można usunąć. Wydarzenie o ID {google_id} już nie istnieje w Google Calendar.")
            raise GoogleCalendarError(f"Błąd HTTP podczas usuwania wydarzenia w Google: {e._get_reason()}")

        except Exception as e:
            raise GoogleCalendarError(f"Nieoczekiwany błąd podczas komunikacji z Google: {e}")

    def _map_dto_to_google(self, dto: EventDTO) -> dict:
        start_str = dto.start_datetime.isoformat() if dto.start_datetime else datetime.datetime.now().isoformat()
        end_str = dto.end_datetime.isoformat() if dto.end_datetime else (
                datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()

        body = {
            'summary': dto.title,
            'description': dto.description,
            'start': {
                'dateTime': start_str,
                'timeZone': 'Europe/Warsaw',
            },
            'end': {
                'dateTime': end_str,
                'timeZone': 'Europe/Warsaw',
            }
        }

        if dto.rrule_str:
            body['recurrence'] = [f"RRULE:{dto.rrule_str}"]

        if dto.category and dto.category.color.id is not None:
            body['colorId'] = dto.category.color.id

        return body

    def _map_google_to_dto(self, google_event: dict) -> EventDTO:
        start_data = google_event['start'].get('dateTime', google_event['start'].get('date'))
        end_data = google_event['end'].get('dateTime', google_event['end'].get('date'))

        start_dt = datetime.datetime.fromisoformat(start_data) if start_data else None
        end_dt = datetime.datetime.fromisoformat(end_data) if end_data else None

        rrule_str = None
        if 'recurrence' in google_event and google_event['recurrence']:
            raw_rrule = google_event['recurrence'][0]
            if raw_rrule.startswith("RRULE:"):
                rrule_str = raw_rrule.replace("RRULE:", "")

        return EventDTO(
            id=None,
            title=google_event.get('summary', 'Brak tytułu'),
            description=google_event.get('description'),
            start_datetime=start_dt,
            end_datetime=end_dt,
            is_high_priority=False,
            is_completed=False,
            rrule_str=rrule_str,
            source=EventSource.GOOGLE,
            category=None
        )