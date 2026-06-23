import datetime
import pytest
from unittest.mock import MagicMock

from DTO.eventDTO import EventDTO
from DTO.deleted_google_eventDTO import DeletedGoogleEventDTO


@pytest.fixture
def mock_google_service():
    srv = MagicMock()
    srv.user_id = 1
    return srv


@pytest.fixture
def mock_event_repo():
    repo = MagicMock()
    repo.query.return_value.modified_since.return_value.get_list.return_value = []
    repo.query.return_value.by_google_id.return_value.get_list.return_value = []

    repo.update_sync_metadata = MagicMock()
    return repo


@pytest.fixture
def mock_credentials_repo():
    repo = MagicMock()
    db_creds = MagicMock()
    db_creds.last_synced = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    repo.get_by_user_id.return_value = db_creds
    return repo


@pytest.fixture
def sync_mediator(mock_google_service, mock_event_repo, mock_credentials_repo):
    from Services.sync_mediator import SyncMediator

    mediator = SyncMediator(mock_google_service, mock_event_repo, mock_credentials_repo)
    return mediator


def test_push_new_local_events(sync_mediator, mock_google_service, mock_event_repo):
    local_event = MagicMock(spec=EventDTO)
    local_event.id = 10
    local_event.google_event_id = None
    local_event.category = None
    local_event.is_deleted = False

    mock_event_repo.query.return_value.modified_since.return_value.get_list.return_value = [local_event]
    mock_google_service.get_events_since.return_value = []

    mock_google_service.push_event.return_value = "new_google_id_777"

    sync_mediator.run_two_way_sync()

    mock_google_service.push_event.assert_called_once_with(local_event)

    mock_event_repo.update_sync_metadata.assert_called_once()
    args, _ = mock_event_repo.update_sync_metadata.call_args
    assert args[0] == 10
    assert args[1] == "new_google_id_777"


def test_save_new_google_events(sync_mediator, mock_google_service, mock_event_repo):
    g_event = MagicMock(spec=EventDTO)
    g_event.google_event_id = "g_id_123"

    mock_google_service.get_events_since.return_value = [g_event]
    mock_event_repo.query.return_value.modified_since.return_value.get_list.return_value = []

    mock_event_repo.query.return_value.by_google_id.return_value.get_list.return_value = []

    sync_mediator.run_two_way_sync()

    mock_event_repo.add.assert_called_once()
    args, _ = mock_event_repo.add.call_args
    assert args[0] == g_event


def test_conflict_google_wins(sync_mediator, mock_google_service, mock_event_repo):
    now = datetime.datetime.now(datetime.UTC)
    older = now - datetime.timedelta(hours=2)

    local_event = EventDTO(
        id=5,
        title="Lokalny Tytuł",
        description=None,
        start_datetime=None,
        end_datetime=None,
        is_high_priority=False,
        is_completed=False,
        updated_at=older,
        google_event_id="conflict_id",
        category=None
    )

    g_event = EventDTO(
        id=None,
        title="Google Title",
        description="Google Desc",
        start_datetime=None,
        end_datetime=None,
        is_high_priority=False,
        is_completed=False,
        updated_at=now,
        google_event_id="conflict_id"
    )

    mock_event_repo.get_by_id.return_value = local_event
    mock_google_service.get_events_since.return_value = [g_event]
    mock_event_repo.query.return_value.modified_since.return_value.get_list.return_value = [local_event]

    sync_mediator.run_two_way_sync()

    mock_event_repo.update.assert_called_once()

    args, _ = mock_event_repo.update.call_args
    assert args[0] == local_event
    assert args[0].title == "Google Title"
    assert args[0].description == "Google Desc"

    mock_google_service.update_event.assert_not_called()


def test_conflict_local_wins(sync_mediator, mock_google_service, mock_event_repo):
    now = datetime.datetime.now(datetime.UTC)
    older = now - datetime.timedelta(hours=2)

    local_event = MagicMock(spec=EventDTO)
    local_event.id = 5
    local_event.google_event_id = "conflict_id"
    local_event.updated_at = now
    local_event.category = None
    local_event.is_deleted = False

    g_event = MagicMock(spec=EventDTO)
    g_event.google_event_id = "conflict_id"
    g_event.updated_at = older

    mock_google_service.get_events_since.return_value = [g_event]
    mock_event_repo.query.return_value.modified_since.return_value.get_list.return_value = [local_event]

    sync_mediator.run_two_way_sync()

    mock_google_service.update_event.assert_called_once_with(local_event)
    mock_event_repo.update_sync_metadata.assert_called_once()


def test_handle_google_deletion(sync_mediator, mock_google_service, mock_event_repo):
    g_deleted_event = DeletedGoogleEventDTO(google_event_id="del_id", updated_at=datetime.datetime.now(datetime.UTC))

    local_existing = MagicMock(spec=EventDTO)
    local_existing.id = 99

    mock_google_service.get_events_since.return_value = [g_deleted_event]
    mock_event_repo.query.return_value.modified_since.return_value.get_list.return_value = []

    mock_event_repo.query.return_value.by_google_id.return_value.get_list.return_value = [local_existing]

    sync_mediator.run_two_way_sync()

    mock_event_repo.delete.assert_called_once_with(99)


def test_handle_local_soft_deletion(sync_mediator, mock_google_service, mock_event_repo):
    local_deleted = MagicMock(spec=EventDTO)
    local_deleted.id = 15
    local_deleted.google_event_id = "del_id_local"
    local_deleted.is_deleted = True
    local_deleted.category = None
    local_deleted.updated_at = datetime.datetime.now(datetime.UTC)

    mock_event_repo.query.return_value.modified_since.return_value.get_list.return_value = [local_deleted]
    mock_google_service.get_events_since.return_value = []

    sync_mediator.run_two_way_sync()

    mock_google_service.delete_event.assert_called_once_with("del_id_local")

    mock_event_repo.update_sync_metadata.assert_called_once()
    args, _ = mock_event_repo.update_sync_metadata.call_args
    assert args[0] == 15
    assert args[1] == "del_id_local"