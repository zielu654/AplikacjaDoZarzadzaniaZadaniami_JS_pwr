import json
from typing import Optional

from DatabaseSqlAlchemy.sql_alchemy_user_credentials_repository import SqlAlchemyUserCredentialsRepository
from Services.google_calendar_service import GoogleCalendarService
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

class AuthController:
    def __init__(self, google_api_service: GoogleCalendarService, credentials_repo: SqlAlchemyUserCredentialsRepository, current_user_id: int = 1):
        self._google_api = google_api_service
        self._credentials_repo = credentials_repo
        self._user_id = current_user_id

    def login(self) -> bool:
        try:
            if not getattr(self._google_api, 'service', None):
                self._google_api.service = self._google_api._authenticate()
            return True
        except Exception:
            return False

    def logout(self) -> None:
        self._credentials_repo.delete_for_user(self._user_id)
        self._google_api.service = None

    def is_logged_in(self) -> bool:
        db_creds = self._credentials_repo.get_by_user_id(self._user_id)

        if db_creds and db_creds.token_data:
            try:
                token_dict = json.loads(db_creds.token_data)
                creds = Credentials.from_authorized_user_info(token_dict, self._google_api.SCOPES)

                return creds.valid or (creds.expired and creds.refresh_token is not None)
            except Exception:
                return False

        return False

    def get_connected_account_info(self) -> Optional[str]:
        if not self.is_logged_in() or not getattr(self._google_api, 'service', None):
            return None

        try:
            calendar = self._google_api.service.calendars().get(calendarId='primary').execute()
            return calendar.get('id')
        except HttpError as e:
            return None