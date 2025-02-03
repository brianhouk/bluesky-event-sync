import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.bluesky.auth import authenticate, get_session, save_session, on_session_change
from atproto_client import Client, Session, SessionEvent

@pytest.fixture
def mock_client():
    with patch('src.bluesky.auth.Client') as MockClient:
        yield MockClient

@pytest.fixture
def mock_session():
    with patch('src.bluesky.auth.Session') as MockSession:
        yield MockSession

def test_authenticate_with_existing_session(mock_client):
    mock_client_instance = mock_client.return_value
    mock_client_instance.login = MagicMock()
    session_string = "mock_session_string"

    with patch('builtins.open', mock_open(read_data=session_string)):
        client = authenticate("testuser", "testpassword")
    
    mock_client_instance.login.assert_called_once_with(session_string=session_string)
    assert client == mock_client_instance

def test_authenticate_with_new_session(mock_client):
    mock_client_instance = mock_client.return_value
    mock_client_instance.login = MagicMock()

    with patch('builtins.open', mock_open(read_data="")):
        client = authenticate("testuser", "testpassword")
    
    mock_client_instance.login.assert_called_once_with("testuser", "testpassword")
    assert client == mock_client_instance

def test_authenticate_session_reuse_failure(mock_client):
    mock_client_instance = mock_client.return_value
    mock_client_instance.login = MagicMock(side_effect=[Exception("Login failed"), None])
    session_string = "mock_session_string"

    with patch('builtins.open', mock_open(read_data=session_string)):
        client = authenticate("testuser", "testpassword")
    
    assert mock_client_instance.login.call_count == 2
    mock_client_instance.login.assert_any_call(session_string=session_string)
    mock_client_instance.login.assert_any_call("testuser", "testpassword")
    assert client == mock_client_instance

def test_authenticate_failure(mock_client):
    mock_client_instance = mock_client.return_value
    mock_client_instance.login = MagicMock(side_effect=Exception("Login failed"))

    with patch('builtins.open', mock_open(read_data="")):
        with pytest.raises(Exception, match="Login failed"):
            authenticate("testuser", "testpassword")

def test_get_session_existing_file():
    session_string = "mock_session_string"
    with patch('builtins.open', mock_open(read_data=session_string)):
        result = get_session()
    assert result == session_string

def test_get_session_missing_file():
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError
        result = get_session()
    assert result is None

def test_save_session():
    session_string = "mock_session_string"
    with patch('builtins.open', mock_open()) as mock_file:
        save_session(session_string)
    mock_file().write.assert_called_once_with(session_string)

def test_on_session_change_create_event(mock_session):
    mock_session_instance = mock_session.return_value
    mock_session_instance.export = MagicMock(return_value="mock_session_string")

    with patch('src.bluesky.auth.save_session') as mock_save_session:
        on_session_change(SessionEvent.CREATE, mock_session_instance)
    
    mock_save_session.assert_called_once_with("mock_session_string")

def test_on_session_change_refresh_event(mock_session):
    mock_session_instance = mock_session.return_value
    mock_session_instance.export = MagicMock(return_value="mock_session_string")

    with patch('src.bluesky.auth.save_session') as mock_save_session:
        on_session_change(SessionEvent.REFRESH, mock_session_instance)
    
    mock_save_session.assert_called_once_with("mock_session_string")

def test_on_session_change_other_event(mock_session):
    mock_session_instance = mock_session.return_value

    with patch('src.bluesky.auth.save_session') as mock_save_session:
        # Use a proper event that doesn't trigger session saving
        on_session_change('expired', mock_session_instance)
    
    mock_save_session.assert_not_called()