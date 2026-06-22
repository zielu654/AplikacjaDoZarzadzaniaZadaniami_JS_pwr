import datetime
import pytest
from unittest.mock import MagicMock

from DTO.event_DTO import EventDTO
from DTO.deleted_google_event_DTO import DeletedGoogleEventDTO
from Models.event import EventSource


from Services.sync_mediator import SyncMediator


@pytest.fixture
def mock_google_service():
    return MagicMock()


@pytest.fixture
def mock_event_controller():
    return MagicMock()


@pytest.fixture
def mock_auth_controller():
    controller = MagicMock()
    controller.get_last_sync_time.return_value = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    controller.current_user_id = 1
    return controller


@pytest.fixture
def sync_mediator(mock_google_service, mock_event_controller, mock_auth_controller):
    from Services.sync_mediator import SyncMediator
    mediator = SyncMediator(mock_google_service)
    mediator.set_controllers(mock_event_controller, mock_auth_controller)
    return mediator

def test_uninitialized_mediator_raises_runtime_error(mock_google_service):
    """Test 1: Niezainicjowany Mediator rzuca RuntimeError"""
    from Services.sync_mediator import SyncMediator
    mediator = SyncMediator(mock_google_service)

    with pytest.raises(RuntimeError) as excinfo:
        mediator.run_two_way_sync()

    assert "nie został poprawnie zainicjalizowany" in str(excinfo.value)


def test_push_new_local_events(sync_mediator, mock_google_service, mock_event_controller):
    """Test 2: Push'owanie nowych zadań (Local -> Google)"""
    local_event = MagicMock(spec=EventDTO)
    local_event.id = 10
    local_event.google_event_id = None
    local_event.category = None
    local_event.is_deleted = False

    mock_event_controller.get_events_modified_since.return_value = [local_event]
    mock_google_service.get_events_since.return_value = []

    mock_google_service.push_event.return_value = "new_google_id_777"

    sync_mediator.run_two_way_sync()

    mock_google_service.push_event.assert_called_once_with(local_event)

    mock_event_controller.sync_update_metadata.assert_called_once()
    args, _ = mock_event_controller.sync_update_metadata.call_args
    assert args[0] == 10
    assert args[1] == "new_google_id_777"


def test_save_new_google_events(sync_mediator, mock_google_service, mock_event_controller):
    """Test 3: Zapisywanie nowych zadań (Google -> Local)"""
    g_event = MagicMock(spec=EventDTO)
    g_event.google_event_id = "g_id_123"

    mock_google_service.get_events_since.return_value = [g_event]
    mock_event_controller.get_events_modified_since.return_value = []

    mock_event_controller.get_event_by_google_id.return_value = None

    sync_mediator.run_two_way_sync()

    mock_event_controller.sync_create_from_google.assert_called_once()
    args, _ = mock_event_controller.sync_create_from_google.call_args
    assert args[0] == g_event


def test_conflict_google_wins(sync_mediator, mock_google_service, mock_event_controller):
    """Test 4: Konflikt - Google wygrywa (Google -> Local)"""
    now = datetime.datetime.now(datetime.UTC)
    older = now - datetime.timedelta(hours=2)

    local_event = MagicMock(spec=EventDTO)
    local_event.id = 5
    local_event.google_event_id = "conflict_id"
    local_event.updated_at = older
    local_event.category = None

    g_event = MagicMock(spec=EventDTO)
    g_event.google_event_id = "conflict_id"
    g_event.updated_at = now

    mock_google_service.get_events_since.return_value = [g_event]
    mock_event_controller.get_events_modified_since.return_value = [local_event]

    sync_mediator.run_two_way_sync()

    mock_event_controller.sync_update_from_google.assert_called_once()
    args, _ = mock_event_controller.sync_update_from_google.call_args
    assert args[0] == 5
    assert args[1] == g_event

    mock_google_service.update_event.assert_not_called()


def test_conflict_local_wins(sync_mediator, mock_google_service, mock_event_controller):
    """Test 5: Konflikt - Lokalne modyfikacje wygrywają (Local -> Google)"""
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
    mock_event_controller.get_events_modified_since.return_value = [local_event]

    sync_mediator.run_two_way_sync()

    mock_google_service.update_event.assert_called_once_with(local_event)

    mock_event_controller.sync_update_metadata.assert_called_once()


def test_handle_google_deletion(sync_mediator, mock_google_service, mock_event_controller):
    """Test 6: Obsługa usunięcia przez Google (DeletedGoogleEventDTO)"""
    g_deleted_event = DeletedGoogleEventDTO(google_event_id="del_id", updated_at=datetime.datetime.now(datetime.UTC))

    local_existing = MagicMock(spec=EventDTO)
    local_existing.id = 99

    mock_google_service.get_events_since.return_value = [g_deleted_event]
    mock_event_controller.get_events_modified_since.return_value = []
    mock_event_controller.get_event_by_google_id.return_value = local_existing

    sync_mediator.run_two_way_sync()

    mock_event_controller.delete_event.assert_called_once_with(99)


def test_handle_local_soft_deletion(sync_mediator, mock_google_service, mock_event_controller):
    """Test 7: Obsługa usunięcia lokalnego (is_deleted=True) - pozostaje jako soft delete"""
    local_deleted = MagicMock(spec=EventDTO)
    local_deleted.id = 15
    local_deleted.google_event_id = "del_id_local"
    local_deleted.is_deleted = True
    local_deleted.category = None
    local_deleted.updated_at = datetime.datetime.now(datetime.UTC)

    mock_event_controller.get_events_modified_since.return_value = [local_deleted]
    mock_google_service.get_events_since.return_value = []

    sync_mediator.run_two_way_sync()

    mock_google_service.delete_event.assert_called_once_with("del_id_local")

    mock_event_controller.sync_update_metadata.assert_called_once()
    args, _ = mock_event_controller.sync_update_metadata.call_args
    assert args[0] == 15
    assert args[1] == "del_id_local"