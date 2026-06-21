import datetime
import json
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from DTO.event_DTO import EventDTO
from DTO.user_credentials_DTO import UserCredentialsDTO
from DatabaseSqlAlchemy.interfaces import IUserCredentialsRepository
from Models.event import EventSource


class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self,
                 credentials_repository: IUserCredentialsRepository,
                 current_user_id: int,
                 credentials_path: str = 'Secrets/credentials.json'):
        self.repo = credentials_repository
        self.user_id = current_user_id
        self.credentials_path = credentials_path
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
            calendarId='primary',
            body=google_event_body
        ).execute()

        return created_event.get('id')

    def get_upcoming_events(self, max_results: int = 10) -> List[EventDTO]:
        now_str = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now_str,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        google_events = events_result.get('items', [])
        return [self._map_google_to_dto(ge) for ge in google_events]

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