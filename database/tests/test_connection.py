"""
Unit and Integration Tests for MongoDB Connection Manager and Health Diagnostic Helper.
"""

from unittest.mock import MagicMock, patch
import pytest
import pymongo

from database.connection.mongodb import (
    MongoDBManager,
    db_manager,
    init_mongo_connection,
    close_mongo_connection,
    get_mongo_client,
    get_db,
    get_collection,
)
from database.connection.health import check_database_health, sanitize_mongodb_uri


def test_sanitize_mongodb_uri():
    """Tests URI credentials obfuscation for security compliance."""
    raw_uri = "mongodb://admin:secretpassword123@localhost:27017/nudgewaste_db"
    sanitized = sanitize_mongodb_uri(raw_uri)
    assert "secretpassword123" not in sanitized
    assert "admin:****@" in sanitized

    raw_srv = "mongodb+srv://db_user:my_secret_token@cluster0.mongodb.net/test"
    sanitized_srv = sanitize_mongodb_uri(raw_srv)
    assert "my_secret_token" not in sanitized_srv
    assert "db_user:****@" in sanitized_srv

    no_auth_uri = "mongodb://localhost:27017"
    assert sanitize_mongodb_uri(no_auth_uri) == no_auth_uri


def test_mongodb_manager_singleton():
    """Tests that MongoDBManager maintains singleton instance semantics."""
    mgr1 = MongoDBManager()
    mgr2 = MongoDBManager()
    assert mgr1 is mgr2
    assert mgr1 is db_manager


@patch("pymongo.MongoClient")
def test_mongodb_manager_connect_and_close(mock_mongo_client_cls):
    """Tests client initialization and cleanup lifecycle using mocks."""
    mock_client = MagicMock()
    mock_mongo_client_cls.return_value = mock_client

    manager = MongoDBManager()
    manager.close()  # Reset prior state

    db = manager.connect(uri="mongodb://localhost:27017", db_name="test_db")
    assert db is not None
    mock_mongo_client_cls.assert_called_once()

    client = manager.get_client()
    assert client is mock_client

    # Verify collection retrieval
    col = manager.get_collection("users")
    assert col is not None

    manager.close()
    mock_client.close.assert_called_once()
    assert manager._client is None
    assert manager._db is None


@patch("pymongo.MongoClient")
def test_health_check_healthy(mock_mongo_client_cls):
    """Tests check_database_health returns healthy status when ping succeeds."""
    mock_client = MagicMock()
    mock_admin = MagicMock()
    mock_admin.command.return_value = {"ok": 1.0}
    mock_client.admin = mock_admin
    mock_mongo_client_cls.return_value = mock_client

    manager = MongoDBManager()
    manager.close()

    result = check_database_health()
    assert result["status"] == "healthy"
    assert result["is_connected"] is True
    assert result["error"] is None
    assert isinstance(result["latency_ms"], float)

    manager.close()


@patch("pymongo.MongoClient")
def test_health_check_unhealthy(mock_mongo_client_cls):
    """Tests check_database_health returns unhealthy status when ping raises an exception."""
    mock_client = MagicMock()
    mock_admin = MagicMock()
    mock_admin.command.side_effect = pymongo.errors.ServerSelectionTimeoutError("Server unreachable")
    mock_client.admin = mock_admin
    mock_mongo_client_cls.return_value = mock_client

    manager = MongoDBManager()
    manager.close()

    result = check_database_health()
    assert result["status"] == "unhealthy"
    assert result["is_connected"] is False
    assert "ping failed" in result["error"]

    manager.close()


def test_helper_accessors_and_lifecycle():
    """Tests top-level accessor functions."""
    with patch("pymongo.MongoClient") as mock_mongo_client_cls:
        mock_client = MagicMock()
        mock_mongo_client_cls.return_value = mock_client

        close_mongo_connection()
        db = init_mongo_connection()
        assert db is not None

        c = get_mongo_client()
        assert c is mock_client

        d = get_db()
        assert d is not None

        col = get_collection("disposals")
        assert col is not None

        close_mongo_connection()
