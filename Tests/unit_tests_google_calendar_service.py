import json
import datetime
import pytest
from unittest.mock import MagicMock, patch

from Services.google_calendar_service import GoogleCalendarService
from DTO.event_DTO import EventDTO
from DTO.user_credentials_DTO import UserCredentialsDTO
from Models.event import EventSource


@pytest.fixture
def mock_repo():
    """Tworzy atrapę repozytorium tokenów (IUserCredentialsRepository)."""
    return MagicMock()


@pytest.fixture
def google_service(mock_repo):
    """
    Tworzy serwis Google, odcinając proces autoryzacji (_authenticate),
    dzięki czemu możemy testować metody add_event czy get_upcoming_events
    bez dotykania internetu i bez otwierania przeglądarki.
    """
    with patch.object(GoogleCalendarService, '_authenticate', return_value=MagicMock()):
        service = GoogleCalendarService(credentials_repository=mock_repo, current_user_id=1)
        return service

@patch('Services.google_calendar_service.build')
@patch('Services.google_calendar_service.Credentials')
def test_authenticate_uses_valid_token_from_repository(mock_credentials_class, mock_build, mock_repo):
    """
    Sprawdza, czy jeśli w bazie jest zapisany poprawny token, _authenticate
    użyje go i poprawnie zbuduje klienta API, zamiast prosić o logowanie.
    """
    fake_token_json = json.dumps({"access_token": "tajny_access", "refresh_token": "tajny_refresh"})
    mock_repo.get_by_user_id.return_value = UserCredentialsDTO(user_id=1, token_data=fake_token_json)

    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_credentials_class.from_authorized_user_info.return_value = mock_creds_instance

    service = GoogleCalendarService(credentials_repository=mock_repo, current_user_id=1)

    mock_repo.get_by_user_id.assert_called_once_with(1)

    mock_credentials_class.from_authorized_user_info.assert_called_once_with(
        {"access_token": "tajny_access", "refresh_token": "tajny_refresh"},
        service.SCOPES
    )

    mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds_instance)


def test_map_dto_to_google_formats_dates_and_fields(google_service):
    """Sprawdza, czy obiekt EventDTO jest prawidłowo tłumaczony na strukturę słownika Google."""
    start_dt = datetime.datetime(2026, 6, 21, 12, 0, 0)
    end_dt = datetime.datetime(2026, 6, 21, 13, 0, 0)

    mock_color = MagicMock()
    mock_color.id = "11"
    mock_category = MagicMock()
    mock_category.color = mock_color

    dto = EventDTO(
        id=None,
        title="Test mapowania",
        description="Opis zadania",
        start_datetime=start_dt,
        end_datetime=end_dt,
        is_high_priority=False,
        is_completed=False,
        rrule_str="FREQ=DAILY",
        category=mock_category,
        source=EventSource.LOCAL
    )

    result_dict = google_service._map_dto_to_google(dto)

    assert result_dict['summary'] == "Test mapowania"
    assert result_dict['description'] == "Opis zadania"
    assert result_dict['start']['dateTime'] == start_dt.isoformat()
    assert result_dict['end']['dateTime'] == end_dt.isoformat()
    assert result_dict['recurrence'] == ["RRULE:FREQ=DAILY"]
    assert result_dict['colorId'] == "11"


def test_add_event_sends_insert_request_to_google(google_service):
    """Sprawdza, czy metoda add_event wywołuje funkcję insert z odpowiednimi parametrami."""
    dto = EventDTO(
        id=None, title="Spotkanie", description=None,
        start_datetime=None, end_datetime=None, is_high_priority=False, is_completed=False
    )

    mock_execute = MagicMock(return_value={'id': 'id_nadane_przez_google_999'})
    mock_insert = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(insert=mock_insert)

    returned_id = google_service.add_event(dto)

    assert returned_id == 'id_nadane_przez_google_999'
    mock_insert.assert_called_once()

    _, kwargs = mock_insert.call_args
    assert kwargs['calendarId'] == 'primary'
    assert kwargs['body']['summary'] == "Spotkanie"


def test_get_upcoming_events_returns_mapped_dtos(google_service):
    """Sprawdza, czy pobrane z Google surowe słowniki JSON są poprawnie mapowane na listę obiektów EventDTO."""
    mock_google_response = {
        'items': [
            {
                'id': 'g1',
                'summary': 'Wydarzenie z chmury',
                'description': 'Opis z chmury',
                'start': {'dateTime': '2026-06-21T18:00:00+02:00'},
                'end': {'dateTime': '2026-06-21T19:00:00+02:00'},
                'recurrence': ['RRULE:FREQ=WEEKLY']
            }
        ]
    }

    mock_execute = MagicMock(return_value=mock_google_response)
    mock_list = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(list=mock_list)

    results = google_service.get_upcoming_events(max_results=5)

    assert len(results) == 1
    event_dto = results[0]

    assert isinstance(event_dto, EventDTO)
    assert event_dto.title == "Wydarzenie z chmury"
    assert event_dto.description == "Opis z chmury"
    assert event_dto.rrule_str == "FREQ=WEEKLY"
    assert event_dto.source == EventSource.GOOGLE