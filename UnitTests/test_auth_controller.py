import json
import pytest
from unittest.mock import MagicMock, patch

from Controllers.auth_controller import AuthController
from DTO.user_credentialsDTO import UserCredentialsDTO


@pytest.fixture
def mock_google_service():
    mock_service = MagicMock()
    mock_service.service = None
    mock_service.SCOPES = ["https://www.googleapis.com/auth/calendar"]
    return mock_service


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def auth_controller(mock_google_service, mock_repo):
    return AuthController(google_api_service=mock_google_service, credentials_repo=mock_repo, current_user_id=1)


def test_login_authenticates_if_service_is_none(auth_controller, mock_google_service):
    mock_google_service._authenticate.return_value = "AKTYWNE_POLACZENIE"

    result = auth_controller.login()

    assert result is True
    assert mock_google_service.service == "AKTYWNE_POLACZENIE"
    mock_google_service._authenticate.assert_called_once()


def test_login_skips_authentication_if_already_connected(auth_controller, mock_google_service):
    mock_google_service.service = "JUZ_ISTNIEJACE_POLACZENIE"

    result = auth_controller.login()

    assert result is True
    mock_google_service._authenticate.assert_not_called()


def test_logout_clears_db_and_resets_service(auth_controller, mock_google_service, mock_repo):
    auth_controller.logout()

    user_id = getattr(auth_controller, "_user_id", 1)

    mock_repo.delete_for_user.assert_called_once_with(user_id)
    assert mock_google_service.service is None


@patch("Controllers.auth_controller.Credentials")
def test_is_logged_in_returns_true_for_valid_token(mock_credentials_class, auth_controller, mock_repo):
    fake_token = json.dumps({"access_token": "abc"})
    mock_repo.get_by_user_id.return_value = MagicMock(token_data=fake_token)

    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_credentials_class.from_authorized_user_info.return_value = mock_creds

    assert auth_controller.is_logged_in() is True


def test_is_logged_in_returns_false_if_no_token_in_db(auth_controller, mock_repo):
    mock_repo.get_by_user_id.return_value = None
    assert auth_controller.is_logged_in() is False


def test_get_connected_account_info_returns_email(auth_controller, mock_google_service):
    auth_controller.is_logged_in = MagicMock(return_value=True)
    mock_google_service.service = MagicMock()

    mock_execute = MagicMock(return_value={"id": "testowy_user@gmail.com"})
    mock_get = MagicMock(return_value=MagicMock(execute=mock_execute))
    mock_google_service.service.calendars.return_value = MagicMock(get=mock_get)

    email = auth_controller.get_connected_account_info()

    assert email == "testowy_user@gmail.com"
    mock_get.assert_called_once_with(calendarId="primary")
