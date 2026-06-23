import json
import datetime
import pytest
from unittest.mock import MagicMock, patch
from googleapiclient.errors import HttpError
import httplib2

from Core.exceptions import GoogleCalendarError, GoogleEventNotFoundError
from Services.google_calendar_service import GoogleCalendarService
from DTO.eventDTO import EventDTO
from DTO.user_credentialsDTO import UserCredentialsDTO
from Models.event import EventSource


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def google_service(mock_repo):
    with patch.object(GoogleCalendarService, "_authenticate", return_value=MagicMock()):
        service = GoogleCalendarService(credentials_repository=mock_repo, current_user_id=1)
        return service


@patch("Services.google_calendar_service.build")
@patch("Services.google_calendar_service.Credentials")
def test_authenticate_uses_valid_token_from_repository(mock_credentials_class, mock_build, mock_repo):
    fake_token_json = json.dumps({"access_token": "tajny_access", "refresh_token": "tajny_refresh"})
    mock_repo.get_by_user_id.return_value = UserCredentialsDTO(user_id=1, token_data=fake_token_json)

    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_credentials_class.from_authorized_user_info.return_value = mock_creds_instance

    service = GoogleCalendarService(credentials_repository=mock_repo, current_user_id=1)

    mock_repo.get_by_user_id.assert_called_once_with(1)

    mock_credentials_class.from_authorized_user_info.assert_called_once_with(
        {"access_token": "tajny_access", "refresh_token": "tajny_refresh"}, service.SCOPES
    )

    mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds_instance)


def test_map_dto_to_google_formats_dates_and_fields(google_service):
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
        source=EventSource.LOCAL,
    )

    result_dict = google_service._map_dto_to_google(dto)

    assert result_dict["summary"] == "Test mapowania"
    assert result_dict["description"] == "Opis zadania"
    assert result_dict["start"]["dateTime"] == start_dt.isoformat()
    assert result_dict["end"]["dateTime"] == end_dt.isoformat()
    assert result_dict["recurrence"] == ["RRULE:FREQ=DAILY"]
    assert result_dict["colorId"] == "11"


def test_add_event_sends_insert_request_to_google(google_service):
    dto = EventDTO(
        id=None,
        title="Spotkanie",
        description=None,
        start_datetime=None,
        end_datetime=None,
        is_high_priority=False,
        is_completed=False,
    )

    mock_execute = MagicMock(return_value={"id": "id_nadane_przez_google_999"})
    mock_insert = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(insert=mock_insert)

    returned_id = google_service.push_event(dto)

    assert returned_id == "id_nadane_przez_google_999"
    mock_insert.assert_called_once()

    _, kwargs = mock_insert.call_args
    assert kwargs["calendarId"] == "primary"
    assert kwargs["body"]["summary"] == "Spotkanie"


def test_get_upcoming_events_returns_mapped_dtos(google_service):
    mock_google_response = {
        "items": [
            {
                "id": "g1",
                "summary": "Wydarzenie z chmury",
                "description": "Opis z chmury",
                "start": {"dateTime": "2026-06-21T18:00:00+02:00"},
                "end": {"dateTime": "2026-06-21T19:00:00+02:00"},
                "recurrence": ["RRULE:FREQ=WEEKLY"],
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


def test_update_event_sends_put_request_to_google(google_service):
    start_dt = datetime.datetime(2026, 6, 21, 10, 0)
    end_dt = datetime.datetime(2026, 6, 21, 11, 0)
    updated_dto = EventDTO(
        id=None,
        title="Zaktualizowany Tytuł",
        description="Zmieniony opis",
        start_datetime=start_dt,
        end_datetime=end_dt,
        is_high_priority=False,
        is_completed=False,
        google_event_id="google_id_777",
    )

    mock_execute = MagicMock()
    mock_update = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(update=mock_update)

    google_service.update_event(updated_dto)

    mock_update.assert_called_once()
    _, kwargs = mock_update.call_args
    assert kwargs["eventId"] == "google_id_777"
    assert kwargs["calendarId"] in ["primary", getattr(google_service, "calendar_id", "primary")]
    assert kwargs["body"]["summary"] == "Zaktualizowany Tytuł"


def test_delete_event_sends_delete_request(google_service):
    mock_execute = MagicMock()
    mock_delete = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(delete=mock_delete)

    google_service.delete_event("id_do_usuniecia_123")

    mock_delete.assert_called_once()
    _, kwargs = mock_delete.call_args
    assert kwargs["eventId"] == "id_do_usuniecia_123"


def test_delete_event_raises_custom_error_on_404(google_service):
    """Sprawdza, jak zachowa się serwis, jeśli spróbujemy usunąć wydarzenie, którego już nie ma (błąd 404)."""
    fake_resp = httplib2.Response({"status": "404"})
    fake_error = HttpError(fake_resp, b"Not Found")

    mock_execute = MagicMock(side_effect=fake_error)
    mock_delete = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(delete=mock_delete)

    with pytest.raises(Exception) as excinfo:
        google_service.delete_event("duchowe_id_999")

    assert "nie istnieje" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()


def test_update_event_raises_custom_error_on_404(google_service):
    fake_resp = httplib2.Response({"status": "404"})
    fake_error = HttpError(fake_resp, b"Not Found")

    mock_execute = MagicMock(side_effect=fake_error)
    mock_update = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(update=mock_update)

    dummy_dto = EventDTO(
        id=None,
        title="Test",
        description=None,
        start_datetime=datetime.datetime.now(),
        end_datetime=datetime.datetime.now(),
        is_high_priority=False,
        is_completed=False,
        category=None,
        google_event_id="ghost_id_777",
    )

    with pytest.raises(GoogleEventNotFoundError) as excinfo:
        google_service.update_event(dummy_dto)

    assert "nie istnieje" in str(excinfo.value).lower() or "not found" in str(excinfo.value).lower()


def test_delete_event_raises_generic_calendar_error_on_403_forbidden(google_service):
    fake_resp = httplib2.Response({"status": "403"})
    fake_error = HttpError(fake_resp, b"Forbidden")

    mock_execute = MagicMock(side_effect=fake_error)
    mock_delete = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(delete=mock_delete)

    with pytest.raises(GoogleCalendarError) as excinfo:
        google_service.delete_event("some_id")

    assert "403" in str(excinfo.value) or "błąd http" in str(excinfo.value).lower()


def test_network_failure_raises_google_calendar_error(google_service):
    mock_execute = MagicMock(side_effect=ConnectionError("Brak połączenia z siecią"))
    mock_delete = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(delete=mock_delete)

    with pytest.raises(GoogleCalendarError) as excinfo:
        google_service.delete_event("some_id")

    assert "nieoczekiwany błąd" in str(excinfo.value).lower()


def test_get_events_since_success_with_naive_datetime(google_service):
    last_sync = datetime.datetime(2026, 6, 22, 10, 0, 0)
    mock_items = [{"id": "e1", "status": "confirmed", "summary": "Zwykły event"}, {"id": "e2", "status": "cancelled"}]

    mock_execute = MagicMock(return_value={"items": mock_items})
    mock_list = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(list=mock_list)

    results = google_service.get_events_since(last_sync)

    assert len(results) == 2
    assert results[0].google_event_id == "e1"
    assert results[0].title == "Zwykły event"
    assert results[1].google_event_id == "e2"
    mock_list.assert_called_once()

    _, kwargs = mock_list.call_args
    assert kwargs["updatedMin"] == "2026-06-22T10:00:00Z"
    assert kwargs["showDeleted"] is True
    assert kwargs["singleEvents"] is False


def test_get_events_since_success_with_aware_datetime(google_service):
    last_sync = datetime.datetime(2026, 6, 22, 10, 0, 0, tzinfo=datetime.timezone.utc)

    mock_execute = MagicMock(return_value={"items": []})
    mock_list = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(list=mock_list)

    google_service.get_events_since(last_sync)

    _, kwargs = mock_list.call_args
    assert kwargs["updatedMin"] == "2026-06-22T10:00:00+00:00"


def test_get_events_since_raises_google_calendar_error_on_exception(google_service):
    last_sync = datetime.datetime(2026, 6, 22, 10, 0, 0)

    mock_execute = MagicMock(side_effect=Exception("API limit exceeded"))
    mock_list = MagicMock(return_value=MagicMock(execute=mock_execute))
    google_service.service.events.return_value = MagicMock(list=mock_list)

    with pytest.raises(GoogleCalendarError) as excinfo:
        google_service.get_events_since(last_sync)

    assert "nieoczekiwany błąd" in str(excinfo.value).lower()
    assert "api limit exceeded" in str(excinfo.value).lower()
