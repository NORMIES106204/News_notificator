
import pytest
from unittest.mock import MagicMock

from notificator.database.connection import DatabaseConnection


@pytest.fixture
def db():
    """Create a fresh database manager for each test."""
    return DatabaseConnection()


def mock_connection():
    """Create a mock PostgreSQL connection."""
    connection = MagicMock()
    connection.closed = False
    return connection


# --------------------------------------------------
# 1. Connection tests
# --------------------------------------------------

def test_connect_success(db, monkeypatch):
    connection = mock_connection()

    monkeypatch.setattr(
        "notificator.database.connection.psycopg.connect",
        lambda **kwargs: connection
    )

    result = db.connect()

    assert result is True
    assert db.connection is connection
    assert db.is_connected()


def test_connect_failure(db, monkeypatch, capsys):
    def raise_error(**kwargs):
        raise ConnectionError("Database unavailable")

    monkeypatch.setattr(
        "notificator.database.connection.psycopg.connect",
        raise_error
    )

    result = db.connect()

    captured = capsys.readouterr()

    assert result is False
    assert db.connection is None
    assert "Connection failed" in captured.out
    assert "Traceback" in captured.err
    assert "Database unavailable" in captured.err


def test_connect_when_already_connected(db, monkeypatch):
    connection = mock_connection()
    db.connection = connection

    def unexpected_connect(**kwargs):
        pytest.fail("Should not create another connection")

    monkeypatch.setattr(
        "notificator.database.connection.psycopg.connect",
        unexpected_connect
    )

    assert db.connect() is True
    assert db.connection is connection


# --------------------------------------------------
# 2. Connection status tests
# --------------------------------------------------

def test_is_connected_true(db):
    db.connection = mock_connection()

    assert db.is_connected() is True


def test_is_connected_false_when_no_connection(db):
    db.connection = None

    assert db.is_connected() is False


def test_is_connected_false_when_closed(db):
    connection = mock_connection()
    connection.closed = True
    db.connection = connection

    assert db.is_connected() is False


# --------------------------------------------------
# 3. Health check tests
# --------------------------------------------------

def test_check_connection_success(db):
    connection = mock_connection()
    cursor = MagicMock()

    cursor.fetchone.return_value = (1,)

    connection.cursor.return_value.__enter__.return_value = cursor

    db.connection = connection

    result = db.check_connection()

    assert result is True
    cursor.execute.assert_called_once_with("SELECT 1")
    cursor.fetchone.assert_called_once()


def test_check_connection_no_connection(db, capsys):
    result = db.check_connection()

    captured = capsys.readouterr()

    assert result is False
    assert "No active connection" in captured.out


def test_check_connection_failure(db, capsys):
    connection = mock_connection()

    connection.cursor.side_effect = ConnectionError(
        "Server not responding"
    )

    db.connection = connection

    result = db.check_connection()

    captured = capsys.readouterr()

    assert result is False
    assert "Health check failed" in captured.out
    assert "Traceback" in captured.err
    assert "Server not responding" in captured.err


# --------------------------------------------------
# 4. Close connection tests
# --------------------------------------------------

def test_close_success(db):
    connection = mock_connection()
    db.connection = connection

    db.close()

    connection.close.assert_called_once()
    assert db.connection is None


def test_close_without_connection(db, capsys):
    db.close()

    captured = capsys.readouterr()

    assert db.connection is None
    assert "No connection to close" in captured.out


# --------------------------------------------------
# 5. Reconnect tests
# --------------------------------------------------

def test_reconnect_success(db, monkeypatch):
    old_connection = mock_connection()
    new_connection = mock_connection()

    db.connection = old_connection

    monkeypatch.setattr(
        "notificator.database.connection.psycopg.connect",
        lambda **kwargs: new_connection
    )

    result = db.reconnect()

    assert result is True
    old_connection.close.assert_called_once()
    assert db.connection is new_connection
    assert db.is_connected()


def test_reconnect_failure(db, monkeypatch, capsys):
    old_connection = mock_connection()
    db.connection = old_connection

    def raise_error(**kwargs):
        raise ConnectionError("Reconnect failed")

    monkeypatch.setattr(
        "notificator.database.connection.psycopg.connect",
        raise_error
    )

    result = db.reconnect()

    captured = capsys.readouterr()

    assert result is False
    assert db.connection is None
    old_connection.close.assert_called_once()
    assert "Reconnect failed" in captured.err
